# Terraform Infrastructure

This stack provisions core AWS infrastructure for Revive & Thrive Tech:
- VPC + public subnet + internet gateway
- Security group (SSH/HTTP/HTTPS)
- EC2 app host with Elastic IP
- IAM role + instance profile
- S3 media bucket with versioning

## Usage

1. Copy and edit variables:
   cp terraform.tfvars.example terraform.tfvars

2. Initialize:
   terraform init

3. Validate:
   terraform validate

4. Plan:
   terraform plan

5. Apply:
   terraform apply

## Notes
- Use a current Ubuntu AMI ID for your selected region.
- Restrict SSH CIDR to your workstation IP.
- Store state remotely (S3 + DynamoDB) before production team usage.
