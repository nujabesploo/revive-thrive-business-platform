# Useful value for DNS and SSH checks after EC2 creation.
output "instance_public_ip" {
  value       = aws_eip.app.public_ip
  description = "Public IP for the app server"
}

# Handy resource ID for AWS console navigation.
output "instance_id" {
  value       = aws_instance.app.id
  description = "EC2 instance ID"
}

# Media bucket name used by app/media pipeline.
output "media_bucket_name" {
  value       = aws_s3_bucket.media.bucket
  description = "S3 media bucket name"
}

# Default SSH username for Ubuntu AMIs.
output "ssh_user" {
  value       = "ubuntu"
  description = "Default SSH user for Ubuntu AMI"
}

# Placeholder output so CloudFront wiring can be tracked in one place.
output "cloudfront_domain_placeholder" {
  value       = var.cloudfront_domain_placeholder
  description = "CloudFront domain placeholder until distribution is provisioned"
}
