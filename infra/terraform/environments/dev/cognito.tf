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
  description = "Create Cognito Hosted UI domain when OAuth is enabled (requires HTTPS app_base_url)."
  type        = bool
  default     = true
}

locals {
  cognito_domain_prefix = var.cognito_domain_prefix != "" ? var.cognito_domain_prefix : "${var.project_name}-${var.environment}"
}

module "cognito" {
  source = "../../modules/cognito"

  project_name  = var.project_name
  environment   = var.environment
  app_base_url  = var.app_base_url
  domain_prefix = local.cognito_domain_prefix
  create_domain = var.create_cognito_domain
  tags          = var.tags
}
