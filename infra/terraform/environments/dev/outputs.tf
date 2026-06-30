output "vpc_id" {
  value = module.networking.vpc_id
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "rds_security_group_id" {
  description = "Attach to RDS when modules/rds is added."
  value       = module.networking.rds_security_group_id
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
