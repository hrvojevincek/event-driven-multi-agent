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

output "cognito_user_pool_id" {
  description = "Cognito user pool ID — NEXT_PUBLIC_COGNITO_USER_POOL_ID at frontend build."
  value       = module.cognito.user_pool_id
}

output "cognito_app_client_id" {
  description = "Cognito app client ID — NEXT_PUBLIC_COGNITO_APP_CLIENT_ID at frontend build."
  value       = module.cognito.app_client_id
}

output "cognito_hosted_ui_domain" {
  description = "Hosted UI FQDN — NEXT_PUBLIC_COGNITO_DOMAIN at frontend build."
  value       = module.cognito.hosted_ui_domain_fqdn
}

output "frontend_build_env" {
  description = "Suggested NEXT_PUBLIC_* values for frontend Docker build after apply."
  value = {
    NEXT_PUBLIC_API_URL               = "http://${module.ecs.alb_dns_name}"
    NEXT_PUBLIC_APP_URL               = var.app_base_url != "" ? trim(var.app_base_url, "/") : "http://${module.ecs.alb_dns_name}"
    NEXT_PUBLIC_AUTH_DISABLED         = var.auth_disabled ? "true" : "false"
    NEXT_PUBLIC_COGNITO_USER_POOL_ID  = module.cognito.user_pool_id
    NEXT_PUBLIC_COGNITO_APP_CLIENT_ID = module.cognito.app_client_id
    NEXT_PUBLIC_COGNITO_REGION        = var.aws_region
    NEXT_PUBLIC_COGNITO_DOMAIN        = module.cognito.hosted_ui_domain_fqdn
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
