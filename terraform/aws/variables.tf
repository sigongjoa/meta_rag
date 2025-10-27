variable "aws_region" {
  description = "The AWS region to deploy resources into."
  type        = string
  default     = "ap-northeast-2"
}

variable "ecr_repository" {
  description = "The name of the ECR repository."
  type        = string
  default     = "meta-rag-repo"
}

variable "image_name" {
  description = "The full name of the container image to deploy."
  type        = string
}
