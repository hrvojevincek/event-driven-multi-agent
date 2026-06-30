variable "project_name" {
  type    = string
  default = "eventforge"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "single_nat_gateway" {
  type    = bool
  default = true
}

variable "backend_image" {
  description = "Backend ECR image URI (build and push before first deploy)."
  type        = string
}

variable "frontend_image" {
  description = "Frontend ECR image URI (build and push before first deploy)."
  type        = string
}

variable "event_bus_arn" {
  description = "EventBridge bus ARN (from modules/eventbridge — wire when available)."
  type        = string
}

variable "worker_queue_arns" {
  description = "SQS queue ARNs for worker IAM (from modules/sqs — wire when available)."
  type        = list(string)
  default     = []
}

variable "postgres_host" {
  description = "RDS endpoint (from modules/rds — wire when available)."
  type        = string
}

variable "postgres_port" {
  type    = number
  default = 5432
}

variable "postgres_db" {
  type    = string
  default = "eventforge"
}

variable "postgres_user" {
  type    = string
  default = "eventforge"
}

variable "postgres_password_secret_arn" {
  description = "Secrets Manager ARN for the Postgres password."
  type        = string
}

variable "openai_api_key_secret_arn" {
  type    = string
  default = ""
}

variable "anthropic_api_key_secret_arn" {
  type    = string
  default = ""
}

variable "tavily_api_key_secret_arn" {
  type    = string
  default = ""
}

variable "cors_origins" {
  description = "JSON array string for CORS_ORIGINS, e.g. [\"https://app.example.com\"]."
  type        = string
  default     = "[]"
}

variable "cognito_user_pool_id" {
  type    = string
  default = ""
}

variable "cognito_app_client_id" {
  type    = string
  default = ""
}

variable "cognito_region" {
  type    = string
  default = "eu-west-2"
}

variable "auth_disabled" {
  description = "Set false once Cognito is wired."
  type        = bool
  default     = false
}

variable "acm_certificate_arn" {
  description = "Optional ACM cert for HTTPS on the ALB."
  type        = string
  default     = ""
}

variable "otel_exporter_otlp_endpoint" {
  type    = string
  default = ""
}

variable "create_ecr_repositories" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
