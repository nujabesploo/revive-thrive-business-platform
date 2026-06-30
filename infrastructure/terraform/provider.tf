terraform {
  # Keep Terraform version explicit so teammates get predictable behavior.
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  # Default deployment region for this project.
  region = var.aws_region
}
