#########################################
# HOT STORAGE — AWS ElastiCache Redis (TLS)
#########################################

resource "aws_elasticache_replication_group" "redis_tls" {
  description            = "Hot storage Redis with TLS and Multi-AZ"
  replication_group_id   = "${var.project}-redis"

  engine                 = "redis"
  engine_version         = "7.0"
  node_type              = var.hot_cache_node_type

  # new syntax for node count (Terraform AWS provider v5+)
  num_node_groups         = 1
  replicas_per_node_group = 0
  port                    = 6379

  # TLS / encryption settings
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  auth_token                 = var.redis_auth_token

  automatic_failover_enabled = false
  subnet_group_name          = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids         = [aws_security_group.redis_sg.id]
  parameter_group_name       = "default.redis7"

  tags = {
    Project = var.project
    Layer   = "storage-hot"
  }
}

# Outputs for convenience
output "redis_primary_endpoint" {
  description = "TLS-enabled Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis_tls.primary_endpoint_address
}

output "redis_port" {
  description = "Redis port number"
  value       = aws_elasticache_replication_group.redis_tls.port
}

output "redis_tls_enabled" {
  description = "Whether TLS is enabled on the Redis cluster"
  value       = aws_elasticache_replication_group.redis_tls.transit_encryption_enabled
}
