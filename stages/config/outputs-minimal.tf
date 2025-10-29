output "instance_public_ip" {
  description = "Public IP address"
  value       = aws_instance.mock_server.public_ip
}

output "server_url" {
  description = "Mock server URL"
  value       = "http://${aws_instance.mock_server.public_ip}:8000"
}
