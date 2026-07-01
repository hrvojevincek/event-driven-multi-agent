variable "github_org" {
  description = "GitHub user or org for OIDC trust."
  type        = string
  default     = "hrvojevincek"
}

variable "github_repo" {
  description = "GitHub repository name for OIDC trust."
  type        = string
  default     = "event-driven-multi-agent"
}

variable "enable_github_oidc" {
  description = "Create IAM role for GitHub Actions OIDC deploys."
  type        = bool
  default     = true
}

variable "create_github_oidc_provider" {
  description = "Create GitHub OIDC provider (false if already exists in the AWS account)."
  type        = bool
  default     = true
}

variable "terraform_state_bucket_name" {
  description = "S3 bucket for Terraform remote state (empty = no state permissions in OIDC role)."
  type        = string
  default     = ""
}

variable "terraform_lock_table_name" {
  description = "DynamoDB table for Terraform state locking."
  type        = string
  default     = ""
}

module "github_oidc" {
  count  = var.enable_github_oidc ? 1 : 0
  source = "../../modules/github-oidc"

  project_name = var.project_name
  environment  = var.environment

  github_org  = var.github_org
  github_repo = var.github_repo

  create_oidc_provider  = var.create_github_oidc_provider
  oidc_subject_wildcard = true

  ecr_repository_arns = compact([
    module.ecs.backend_ecr_repository_arn,
    module.ecs.frontend_ecr_repository_arn,
  ])

  ecs_pass_role_arns = module.ecs.ecs_pass_role_arns

  ssm_parameter_path_prefix = local.frontend_build_ssm_path

  terraform_state_bucket_arn = var.terraform_state_bucket_name != "" ? "arn:aws:s3:::${var.terraform_state_bucket_name}" : ""
  terraform_lock_table_arn = var.terraform_lock_table_name != "" ? (
    "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.terraform_lock_table_name}"
  ) : ""

  tags = var.tags
}

data "aws_caller_identity" "current" {}
