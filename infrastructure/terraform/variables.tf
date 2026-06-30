# Human-readable prefix used to name AWS resources.
variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "revive-thrive"
}

# Deployment region (requested: us-east-1 default).
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Networking variables below allow easy edits later without changing resource blocks.
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.40.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.40.1.0/24"
}

variable "availability_zone" {
  description = "Availability zone for subnet"
  type        = string
  default     = "us-east-1a"
}

# EC2 sizing and image settings.
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "ami_id" {
  description = "Ubuntu AMI ID"
  type        = string
}

# SSH access scope for admins.
variable "allowed_ssh_cidr" {
  description = "CIDR allowed for SSH"
  type        = string
  default     = "0.0.0.0/0"
}

variable "public_key_material" {
  description = "SSH public key contents"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "revivethrivetech.com"
}

variable "cloudfront_domain_placeholder" {
  description = "CloudFront distribution domain placeholder (set after distribution is created)"
  type        = string
  default     = "pending-cloudfront-domain"
}
