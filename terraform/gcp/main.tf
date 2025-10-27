terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
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

# 1. Artifact Registry to store Docker images
resource "google_artifact_registry_repository" "default" {
  location      = var.gcp_region
  repository_id = var.gar_repository
  format        = "DOCKER"
  description   = "Docker repository for Meta-RAG application"
}

# 2. Cloud Run v2 Service
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.gcp_region

  template {
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
    }
    scaling {
      min_instance_count = 0 # Start with 0 for cost-efficiency, can be set to 1 for production
    }
  }

  # Allow unauthenticated access for now.
  # This will be locked down by API Gateway later.
  ingress = "INGRESS_TRAFFIC_ALL"
}
