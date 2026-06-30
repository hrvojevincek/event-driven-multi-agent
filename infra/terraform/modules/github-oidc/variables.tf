variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "github_org" {
  description = "GitHub organization or user that owns the repository."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (without org)."
  type        = string
}

variable "allowed_branches" {
  description = "Branches allowed to assume the deploy role (push + workflow_dispatch)."
  type        = list(string)
  default     = ["main"]
}

variable "allow_pull_request" {
  description = "Allow pull_request workflows (e.g. terraform plan) from the same repo."
  type        = bool
  default     = true
}

variable "create_oidc_provider" {
  description = "Create the GitHub OIDC provider. Set false if it already exists in the account."
  type        = bool
  default     = true
}

variable "ecr_repository_arns" {
  description = "ECR repository ARNs GitHub Actions may push to."
  type        = list(string)
  default     = []
}

variable "ecs_pass_role_arns" {
  description = "ECS task/execution role ARNs for iam:PassRole when registering task definitions."
  type        = list(string)
  default     = []
}

variable "ssm_parameter_path_prefix" {
  description = "SSM path prefix for frontend build env (e.g. /eventforge/dev/frontend-build)."
  type        = string
  default     = ""
}

variable "terraform_state_bucket_arn" {
  description = "Optional S3 bucket ARN for Terraform remote state."
  type        = string
  default     = ""
}

variable "terraform_lock_table_arn" {
  description = "Optional DynamoDB table ARN for Terraform state locking."
  type        = string
  default     = ""
}

variable "enable_terraform_permissions" {
  description = "Grant broad Terraform apply permissions (dev only; tighten for prod)."
  type        = bool
  default     = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
