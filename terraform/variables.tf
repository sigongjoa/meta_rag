variable "gcp_project_id" {
  description = "The GCP project ID to deploy resources into."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region to deploy resources into."
  type        = string
  default     = "asia-northeast3"
}

variable "service_name" {
  description = "The name of the Cloud Run service."
  type        = string
  default     = "meta-rag-backend-v2"
}

variable "gar_repository" {
  description = "The name of the Google Artifact Registry repository."
  type        = string
  default     = "meta-rag-repo"
}

variable "image_name" {
  description = "The full name of the container image to deploy."
  type        = string
}
