output "vpc_id" {
  value = module.networking.vpc_id
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "rds_security_group_id" {
  description = "RDS security group (used by modules/rds)."
  value       = module.networking.rds_security_group_id
}

output "rds_address" {
  description = "RDS hostname for POSTGRES_HOST."
  value       = module.rds.address
}

output "rds_password_secret_arn" {
  description = "Secrets Manager ARN for Postgres password."
  value       = module.rds.password_secret_arn
  sensitive   = true
}

output "event_bus_arn" {
  description = "EventBridge bus ARN."
  value       = module.eventbridge.bus_arn
}

output "sqs_worker_queue_arns" {
  description = "SQS queue ARNs for pipeline workers."
  value       = module.sqs.worker_queue_arns
}

output "alb_dns_name" {
  description = "ALB URL — set NEXT_PUBLIC_API_URL to http(s)://<this>/api path via same host."
  value       = module.ecs.alb_dns_name
}

output "backend_ecr_repository_url" {
  value = module.ecs.backend_ecr_repository_url
}

output "frontend_ecr_repository_url" {
  value = module.ecs.frontend_ecr_repository_url
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}
