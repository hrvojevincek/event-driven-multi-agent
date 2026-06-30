variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "eventforge"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "callback_urls" {
  description = "OAuth callback URLs for the web app client (Amplify Hosted UI)."
  type        = list(string)
}

variable "logout_urls" {
  description = "OAuth sign-out redirect URLs."
  type        = list(string)
}

variable "domain_prefix" {
  description = "Cognito Hosted UI domain prefix (must be globally unique)."
  type        = string
}

variable "create_domain" {
  description = "Create Cognito Hosted UI domain."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags applied to Cognito resources."
  type        = map(string)
  default     = {}
}
