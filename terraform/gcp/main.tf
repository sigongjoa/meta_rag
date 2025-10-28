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
/*
resource "google_artifact_registry_repository" "default" {
  location      = var.gcp_region
  repository_id = var.gar_repository
  format        = "DOCKER"
  description   = "Docker repository for Meta-RAG application"
}
*/

# 2. Cloud Run v2 Service
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.gcp_region

  template {
    service_account = data.google_service_account.cloud_run_sa.email
    containers {
      image = var.image_name # This will be provided by the CI/CD pipeline
      ports {
        container_port = 8000
      }
      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }
#       env {
#         name  = "INDEX_ENDPOINT_ID"
#         value = google_vertex_ai_index_endpoint.vector_index_endpoint[0].name
#       }
    }
    scaling {
      min_instance_count = 0 # Start with 0 for cost-efficiency, can be set to 1 for production
    }
  }

  # Allow unauthenticated access for now.
  # This will be locked down by API Gateway later.
  ingress = "INGRESS_TRAFFIC_ALL"
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
# resource "google_vertex_ai_index_endpoint" "vector_index_endpoint" {
#   provider = google-beta
#   # This resource will only be created if the index is also being created.
#   count = length(google_vertex_ai_index.vector_index) > 0 ? 1 : 0
# 
#   project      = var.gcp_project_id
#   region       = var.gcp_region
#   display_name = var.vector_index_endpoint_display_name
#   public_endpoint_enabled = true
# 
#   # The endpoint creation should wait for the index to be ready.
#   depends_on = [google_vertex_ai_index.vector_index]
# }

# 5. Deploy the Index to the Endpoint
# resource "google_vertex_ai_index_endpoint_deployed_index" "deployment" {
#   provider = google-beta # Add this based on previous findings
#   # This resource will only be created if the index and endpoint are also being created.
#   count = length(google_vertex_ai_index_endpoint.vector_index_endpoint) > 0 ? 1 : 0
# 
#   index_endpoint    = google_vertex_ai_index_endpoint.vector_index_endpoint[0].id
#   index             = google_vertex_ai_index.vector_index[0].id
#   deployed_index_id = "meta-rag-deployed-index"
#   region            = var.gcp_region # Use variable for region
# }


# --- API Gateway ---

# 5. Create the API Gateway API
data "google_api_gateway_api" "api" {
  provider = google-beta
  project = var.gcp_project_id
  api_id  = var.api_id
}

# 6. Create the API Gateway API Config
resource "google_api_gateway_api_config" "api_config" {
  provider = google-beta
  project      = var.gcp_project_id
  api          = data.google_api_gateway_api.api.api_id
  api_config_id = var.api_config_id

  openapi_documents {
    document {
      path = "../../docs/api/openapi.yaml"
      contents = filebase64("${path.module}/../../docs/api/openapi.yaml")
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

# 7. Create the Gateway itself
resource "google_api_gateway_gateway" "gateway" {
  provider  = google-beta
  api_config = google_api_gateway_api_config.api_config.id
  region    = var.gcp_region
  gateway_id = var.gateway_id
  display_name = var.gateway_id # Using gateway_id as display_name for clarity
  
  lifecycle {
    create_before_destroy = true
  }
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
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${data.google_service_account.cloud_run_sa.email}"
}
