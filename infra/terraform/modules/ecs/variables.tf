variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "eventforge"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "eu-west-2"
}

variable "vpc_id" {
  description = "VPC identifier from the networking module."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the ALB."
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks."
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group for the ALB."
  type        = string
}

variable "api_security_group_id" {
  description = "Security group for FastAPI tasks."
  type        = string
}

variable "frontend_security_group_id" {
  description = "Security group for Next.js tasks."
  type        = string
}

variable "worker_security_group_id" {
  description = "Security group for worker tasks."
  type        = string
}

variable "backend_image" {
  description = "ECR image URI for the backend (API + workers)."
  type        = string
}

variable "frontend_image" {
  description = "ECR image URI for the Next.js frontend."
  type        = string
}

variable "api_desired_count" {
  description = "Desired task count for the API service."
  type        = number
  default     = 1
}

variable "frontend_desired_count" {
  description = "Desired task count for the frontend service."
  type        = number
  default     = 1
}

variable "worker_desired_count" {
  description = "Desired task count per worker service."
  type        = number
  default     = 1
}

variable "research_worker_desired_count" {
  description = "Desired task count for the research worker (may scale higher)."
  type        = number
  default     = 1
}

variable "api_cpu" {
  description = "Fargate CPU units for the API task."
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Fargate memory (MiB) for the API task."
  type        = number
  default     = 1024
}

variable "worker_cpu" {
  description = "Fargate CPU units for worker tasks."
  type        = number
  default     = 512
}

variable "worker_memory" {
  description = "Fargate memory (MiB) for worker tasks."
  type        = number
  default     = 1024
}

variable "frontend_cpu" {
  description = "Fargate CPU units for the frontend task."
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Fargate memory (MiB) for the frontend task."
  type        = number
  default     = 512
}

variable "alb_idle_timeout" {
  description = "ALB idle timeout in seconds (SSE needs >= 300)."
  type        = number
  default     = 300
}

variable "acm_certificate_arn" {
  description = "Optional ACM certificate ARN for HTTPS listener."
  type        = string
  default     = ""
}

variable "event_bus_arn" {
  description = "EventBridge bus ARN for IAM policies."
  type        = string
}

variable "worker_queue_arns" {
  description = "SQS queue ARNs workers may consume from."
  type        = list(string)
  default     = []
}

variable "postgres_host" {
  description = "RDS Postgres hostname."
  type        = string
}

variable "postgres_port" {
  description = "RDS Postgres port."
  type        = number
  default     = 5432
}

variable "postgres_db" {
  description = "Postgres database name."
  type        = string
  default     = "eventforge"
}

variable "postgres_user" {
  description = "Postgres username."
  type        = string
  default     = "eventforge"
}

variable "postgres_password_secret_arn" {
  description = "Secrets Manager ARN for POSTGRES_PASSWORD."
  type        = string
}

variable "openai_api_key_secret_arn" {
  description = "Secrets Manager ARN for OPENAI_API_KEY."
  type        = string
  default     = ""
}

variable "anthropic_api_key_secret_arn" {
  description = "Secrets Manager ARN for ANTHROPIC_API_KEY."
  type        = string
  default     = ""
}

variable "tavily_api_key_secret_arn" {
  description = "Secrets Manager ARN for TAVILY_API_KEY."
  type        = string
  default     = ""
}

variable "cors_origins" {
  description = "Allowed CORS origins for the API (JSON-encoded list string)."
  type        = string
  default     = "[]"
}

variable "cognito_user_pool_id" {
  description = "Cognito user pool ID."
  type        = string
  default     = ""
}

variable "cognito_app_client_id" {
  description = "Cognito app client ID."
  type        = string
  default     = ""
}

variable "cognito_region" {
  description = "Cognito region."
  type        = string
  default     = "eu-west-2"
}

variable "auth_disabled" {
  description = "Bypass JWT auth (must be false in AWS dev/prod)."
  type        = bool
  default     = false
}

variable "event_bus_name" {
  description = "EventBridge bus name."
  type        = string
  default     = "eventforge-bus"
}

variable "sqs_queue_prefix" {
  description = "SQS queue name prefix."
  type        = string
  default     = "eventforge"
}

variable "otel_enabled" {
  description = "Enable OpenTelemetry export."
  type        = bool
  default     = false
}

variable "otel_exporter_otlp_endpoint" {
  description = "OTLP gRPC endpoint for traces."
  type        = string
  default     = ""
}

variable "create_ecr_repositories" {
  description = "Create ECR repositories (set false if repos already exist)."
  type        = bool
  default     = true
}

variable "step_functions_research_enabled" {
  description = "Enable Step Functions research fan-out (sets RESEARCH_ORCHESTRATION_MODE on workers)."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags applied to ECS resources."
  type        = map(string)
  default     = {}
}
