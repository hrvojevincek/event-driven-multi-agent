variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "eventforge"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "app_base_url" {
  description = "Public frontend URL for OAuth callbacks. Empty uses localhost defaults."
  type        = string
  default     = ""
}

variable "domain_prefix" {
  description = "Cognito Hosted UI domain prefix (must be globally unique)."
  type        = string
}

variable "create_domain" {
  description = "Create Cognito Hosted UI domain when OAuth is enabled."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags applied to Cognito resources."
  type        = map(string)
  default     = {}
}
