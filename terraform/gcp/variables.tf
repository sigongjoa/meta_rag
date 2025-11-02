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

variable "vector_index_display_name" {
  description = "The display name for the Vertex AI Index."
  type        = string
  default     = "meta-rag-vector-index"
}

variable "vector_index_contents_uri" {
  description = "The GCS path to the directory containing the embedding data."
  type        = string
  default     = null
}

variable "vector_index_dimensions" {
  description = "The number of dimensions for the vectors."
  type        = number
  default     = 384
}

variable "vector_index_endpoint_display_name" {
  description = "The display name for the Vertex AI Index Endpoint."
  type        = string
  default     = "meta-rag-vector-index-endpoint"
}

variable "api_id" {
  description = "The ID of the API Gateway API."
  type        = string
  default     = "meta-rag-api"
}

variable "api_config_id" {
  description = "The ID of the API Gateway API Config."
  type        = string
  default     = "meta-rag-api-config-v6"
}

variable "gateway_id" {
  description = "The ID of the API Gateway."
  type        = string
  default     = "meta-rag-gateway"
}

variable "cloud_run_service_account_id" {
  description = "The ID for the Cloud Run dedicated service account."
  type        = string
  default     = "meta-rag-cr-sa"
}

variable "api_gateway_service_account_id" {
  description = "The ID for the API Gateway dedicated service account."
  type        = string
  default     = "meta-rag-gw-sa"
}
