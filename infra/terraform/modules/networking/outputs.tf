output "vpc_id" {
  description = "VPC identifier."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs (ALB)."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs (ECS tasks, RDS)."
  value       = aws_subnet.private[*].id
}

output "alb_security_group_id" {
  description = "Security group for the application load balancer."
  value       = aws_security_group.alb.id
}

output "api_security_group_id" {
  description = "Security group for FastAPI ECS tasks."
  value       = aws_security_group.api.id
}

output "frontend_security_group_id" {
  description = "Security group for Next.js ECS tasks."
  value       = aws_security_group.frontend.id
}

output "worker_security_group_id" {
  description = "Security group for SQS worker ECS tasks."
  value       = aws_security_group.worker.id
}

output "rds_security_group_id" {
  description = "Security group for RDS Postgres."
  value       = aws_security_group.rds.id
}
