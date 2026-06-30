variable "app_base_url" {
  description = "Public frontend URL for Cognito OAuth (ALB DNS or custom domain). Empty uses localhost defaults for plan-only."
  type        = string
  default     = ""
}

variable "cognito_domain_prefix" {
  description = "Globally unique Cognito Hosted UI domain prefix. Defaults to eventforge-<environment>."
  type        = string
  default     = ""
}

variable "create_cognito_domain" {
  description = "Create Cognito Hosted UI domain."
  type        = bool
  default     = true
}

locals {
  oauth_base = var.app_base_url != "" ? trim(var.app_base_url, "/") : "http://localhost:3000"

  cognito_callback_urls = ["${local.oauth_base}/auth/callback"]
  cognito_logout_urls   = ["${local.oauth_base}/"]

  cognito_domain_prefix = var.cognito_domain_prefix != "" ? var.cognito_domain_prefix : "${var.project_name}-${var.environment}"
}

module "cognito" {
  source = "../../modules/cognito"

  project_name  = var.project_name
  environment   = var.environment
  callback_urls = local.cognito_callback_urls
  logout_urls   = local.cognito_logout_urls
  domain_prefix = local.cognito_domain_prefix
  create_domain = var.create_cognito_domain
  tags          = var.tags
}
