# Outputs for Terraform configuration

output "api_url" {
  description = "URL of the API Gateway (if deployed)"
  value       = try(aws_api_gateway_deployment.api.invoke_url, "N/A")
}

output "lambda_function_name" {
  description = "Name of the Lambda function (if deployed)"
  value       = try(aws_lambda_function.api.function_name, "N/A")
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket (if deployed)"
  value       = try(aws_s3_bucket.app_bucket.id, "N/A")
}

output "ec2_instance_ip" {
  description = "IP address of the EC2 instance (if deployed)"
  value       = try(aws_instance.app_server.public_ip, "N/A")
}
