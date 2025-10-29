# Output configurations for the banking mock server infrastructure

output "instance_public_ip" {
  description = "Public IP address of the mock server instance"
  value       = aws_instance.mock_server.public_ip
}

output "instance_id" {
  description = "ID of the mock server instance"
  value       = aws_instance.mock_server.id
}

output "server_url" {
  description = "URL of the mock server API"
  value       = "http://${aws_instance.mock_server.public_ip}:${var.server_port}"
}

output "health_check_url" {
  description = "Health check URL for the mock server"
  value       = "http://${aws_instance.mock_server.public_ip}:${var.server_port}/health"
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = terraform.workspace == "aws" ? "ssh -i ${aws_key_pair.deployer[0].key_name}.pem ec2-user@${aws_instance.mock_server.public_ip}" : "SSH not available for ${terraform.workspace} workspace"
}

output "control_api_url" {
  description = "URL for the control API endpoint"
  value       = "http://${aws_instance.mock_server.public_ip}:${var.server_port}/control"
}

output "workspace" {
  description = "Current Terraform workspace"
  value       = terraform.workspace
}

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "docker_container_status" {
  description = "Command to check Docker container status"
  value       = "ssh -i ${aws_key_pair.deployer[0].key_name}.pem ec2-user@${aws_instance.mock_server.public_ip} 'docker ps | grep banking-mock-server'"
}

output "view_logs_command" {
  description = "Command to view application logs"
  value       = "ssh -i ${aws_key_pair.deployer[0].key_name}.pem ec2-user@${aws_instance.mock_server.public_ip} 'docker logs -f banking-mock-server-container'"
}
