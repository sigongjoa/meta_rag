terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. ECR to store Docker images
resource "aws_ecr_repository" "default" {
  name = var.ecr_repository
}
