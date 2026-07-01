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

variable "postgres_db" {
  type    = string
  default = "eventforge"
}

variable "postgres_user" {
  type    = string
  default = "eventforge"
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

variable "enable_step_functions_research" {
  description = "Use Step Functions for research fan-out in AWS dev."
  type        = bool
  default     = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
