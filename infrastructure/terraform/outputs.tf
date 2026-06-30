output "instance_public_ip" {
  value       = aws_eip.app.public_ip
  description = "Public IP for the app server"
}

output "instance_id" {
  value       = aws_instance.app.id
  description = "EC2 instance ID"
}

output "media_bucket_name" {
  value       = aws_s3_bucket.media.bucket
  description = "S3 media bucket name"
}

output "ssh_user" {
  value       = "ubuntu"
  description = "Default SSH user for Ubuntu AMI"
}
