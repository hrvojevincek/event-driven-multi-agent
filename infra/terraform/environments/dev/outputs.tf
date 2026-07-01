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

output "frontend_build_env" {
  description = "Suggested NEXT_PUBLIC_* values for frontend Docker build after apply."
  value = {
    NEXT_PUBLIC_API_URL = "http://${module.ecs.alb_dns_name}"
    NEXT_PUBLIC_APP_URL = var.app_base_url != "" ? trim(var.app_base_url, "/") : "http://${module.ecs.alb_dns_name}"
  }
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

output "api_service_name" {
  description = "ECS API service name for deploy scripts."
  value       = module.ecs.api_service_name
}

output "frontend_service_name" {
  description = "ECS frontend service name for deploy scripts."
  value       = module.ecs.frontend_service_name
}

output "worker_service_names" {
  description = "ECS worker service names keyed by stage."
  value       = module.ecs.worker_service_names
}

output "github_actions_role_arn" {
  description = "IAM role ARN — set as GitHub repository variable AWS_DEPLOY_ROLE_ARN (Actions → Variables, not Secrets)."
  value       = var.enable_github_oidc ? module.github_oidc[0].role_arn : null
}

output "frontend_build_ssm_path" {
  description = "SSM path prefix for frontend Docker build args in CI."
  value       = local.frontend_build_ssm_path
}

output "research_fanout_state_machine_arn" {
  description = "Step Functions state machine ARN for research fan-out (null when disabled)."
  value       = var.enable_step_functions_research ? module.step_functions[0].state_machine_arn : null
}

output "observability_enabled" {
  description = "Whether ADOT sidecar and CloudWatch alarms are enabled."
  value       = var.enable_observability
}

output "otel_exporter_otlp_endpoint" {
  description = "OTLP endpoint configured on ECS tasks (ADOT sidecar on localhost when observability enabled)."
  value       = module.observability.otlp_endpoint
}
