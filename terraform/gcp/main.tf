terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.25.0" # Explicitly set minimum version
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.25.0" # Explicitly set minimum version for beta provider
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.10.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 1. Artifact Registry to store Docker images
resource "google_artifact_registry_repository" "default" {
  location      = var.gcp_region
  repository_id = var.gar_repository
  format        = "DOCKER"
  description   = "Docker repository for Meta-RAG application"
}

# 2. Cloud Run v2 Service
resource "time_sleep" "wait_for_image" {
  create_duration = "30s"

  depends_on = [
    google_artifact_registry_repository.default
  ]
}

resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.gcp_region
  project  = var.gcp_project_id

  depends_on = [
    time_sleep.wait_for_image
  ]

  template {
    containers {
      image = var.image_name
      ports {
        container_port = 8000
      }
      env {
        name  = "INDEX_ENDPOINT_ID"
        value = google_vertex_ai_index_endpoint.vector_index_endpoint[0].name
      }
      env {
        name  = "DEPLOYED_INDEX_ID"
        value = google_vertex_ai_index_endpoint_deployed_index.deployment[0].deployed_index_id
      }
      resources {
        limits = {
          memory = "4Gi"
          cpu    = "1"
        }
      }
    }
    service_account = data.google_service_account.cloud_run_sa.email
  }
}

# 3. Vertex AI Vector Search Index
resource "google_vertex_ai_index" "vector_index" {
  # This resource will only be created if the required variables are provided.
  count = 1

  project      = var.gcp_project_id
  region       = var.gcp_region
  display_name = var.vector_index_display_name

  metadata {
    contents_delta_uri = var.vector_index_contents_uri
    config {
      dimensions = var.vector_index_dimensions
      approximate_neighbors_count = 10
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 500
        }
      }
    }
  }
}

# 4. Vertex AI Index Endpoint and Deployment
resource "google_vertex_ai_index_endpoint" "vector_index_endpoint" {
  provider = google-beta
  # This resource will only be created if the index is also being created.
  count = length(google_vertex_ai_index.vector_index) > 0 ? 1 : 0

  project      = var.gcp_project_id
  region       = var.gcp_region
  display_name = var.vector_index_endpoint_display_name
  public_endpoint_enabled = true

  # The endpoint creation should wait for the index to be ready.
  depends_on = [google_vertex_ai_index.vector_index]
}

# 5. Deploy the Index to the Endpoint
resource "google_vertex_ai_index_endpoint_deployed_index" "deployment" {
  provider = google-beta # Add this based on previous findings
  # This resource will only be created if the index and endpoint are also being created.
  count = length(google_vertex_ai_index_endpoint.vector_index_endpoint) > 0 ? 1 : 0

  index_endpoint    = google_vertex_ai_index_endpoint.vector_index_endpoint[0].id
  index             = google_vertex_ai_index.vector_index[0].id
  deployed_index_id = "meta_rag_deployed_index_2"
  region            = var.gcp_region # Use variable for region
}


# --- API Gateway ---

# 5. Create the API Gateway API
resource "google_api_gateway_api" "api" {
  provider = google-beta
  project = var.gcp_project_id
  api_id  = var.api_id
}

# 6. Create the API Gateway API Config
# This reads the OpenAPI spec, injects the Cloud Run backend URL, and creates a config.
resource "google_api_gateway_api_config" "api_config" {
  provider = google-beta
  project      = var.gcp_project_id
  api          = google_api_gateway_api.api.api_id
  api_config_id = var.api_config_id # Now "meta-rag-api-config-v3"

  depends_on = [
    google_cloud_run_v2_service.default
  ]

  openapi_documents {
    document {
      path = "openapi.yaml"
      # Dynamically inject the backend address into the OpenAPI spec
      contents = base64encode(templatefile("${path.module}/../../docs/api/openapi.yaml", {
        cloud_run_uri = google_cloud_run_v2_service.default.uri
      }))
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

# 7. Create the Gateway itself
resource "google_api_gateway_gateway" "gateway" {
  provider  = google-beta
  api_config = google_api_gateway_api_config.api_config.name
  region    = "asia-northeast1"
  gateway_id = var.gateway_id
  display_name = var.gateway_id # Using gateway_id as display_name for clarity
}

# 8. Grant API Gateway permission to invoke the Cloud Run service
resource "google_cloud_run_v2_service_iam_member" "api_gateway_invoker" {
  project  = google_cloud_run_v2_service.default.project
  location = google_cloud_run_v2_service.default.location
  name     = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  # The member is the service account created for the API Config
  member   = "serviceAccount:${data.google_service_account.api_gateway_sa.email}"
}

# --- Cloud Run Service Account and Permissions ---

# 9. Create a dedicated Service Account for the Cloud Run service
data "google_service_account" "cloud_run_sa" {
  project      = var.gcp_project_id
  account_id   = var.cloud_run_service_account_id
}

# 10. Create a dedicated Service Account for the API Gateway
data "google_service_account" "api_gateway_sa" {
  project      = var.gcp_project_id
  account_id   = var.api_gateway_service_account_id
}

# 10. Grant the Cloud Run SA permission to use Vertex AI
resource "google_project_iam_member" "cloud_run_sa_ai_user" {
  project = var.gcp_project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${data.google_service_account.cloud_run_sa.email}"
}

# 11. Grant the Cloud Run SA permission to read from Artifact Registry
resource "google_artifact_registry_repository_iam_member" "gar_reader" {
  project    = var.gcp_project_id
  location   = var.gcp_region
  repository = var.gar_repository
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${data.google_service_account.cloud_run_sa.email}"
  depends_on = [google_artifact_registry_repository.default]
}

output "api_gateway_url" {
  value = "https://${google_api_gateway_gateway.gateway.default_hostname}/v1/chat"
  description = "The base URL for the deployed API Gateway, including the /v1/chat path."
}

output "api_gateway_managed_service" {
  value = google_api_gateway_api.api.managed_service
  description = "The managed service name for the API Gateway API."
}
