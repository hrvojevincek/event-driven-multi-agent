output "cluster_id" {
  description = "ECS cluster identifier."
  value       = aws_ecs_cluster.this.id
}

output "cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.this.name
}

output "alb_dns_name" {
  description = "ALB DNS name — use for API URL and frontend build args."
  value       = aws_lb.this.dns_name
}

output "alb_arn" {
  description = "ALB ARN."
  value       = aws_lb.this.arn
}

output "api_target_group_arn" {
  description = "API target group ARN."
  value       = aws_lb_target_group.api.arn
}

output "frontend_target_group_arn" {
  description = "Frontend target group ARN."
  value       = aws_lb_target_group.frontend.arn
}

output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL (null if create_ecr_repositories=false)."
  value       = var.create_ecr_repositories ? aws_ecr_repository.backend[0].repository_url : null
}

output "frontend_ecr_repository_url" {
  description = "Frontend ECR repository URL (null if create_ecr_repositories=false)."
  value       = var.create_ecr_repositories ? aws_ecr_repository.frontend[0].repository_url : null
}

output "backend_ecr_repository_arn" {
  description = "Backend ECR repository ARN (null if create_ecr_repositories=false)."
  value       = var.create_ecr_repositories ? aws_ecr_repository.backend[0].arn : null
}

output "frontend_ecr_repository_arn" {
  description = "Frontend ECR repository ARN (null if create_ecr_repositories=false)."
  value       = var.create_ecr_repositories ? aws_ecr_repository.frontend[0].arn : null
}

output "cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "api_service_name" {
  description = "ECS API service name."
  value       = aws_ecs_service.api.name
}

output "frontend_service_name" {
  description = "ECS frontend service name."
  value       = aws_ecs_service.frontend.name
}

output "worker_service_names" {
  description = "ECS worker service names keyed by stage."
  value       = { for k, svc in aws_ecs_service.worker : k => svc.name }
}

output "ecs_pass_role_arns" {
  description = "IAM role ARNs required for ecs:RegisterTaskDefinition (PassRole)."
  value = [
    aws_iam_role.execution.arn,
    aws_iam_role.api_task.arn,
    aws_iam_role.worker_task.arn,
    aws_iam_role.frontend_task.arn,
  ]
}
