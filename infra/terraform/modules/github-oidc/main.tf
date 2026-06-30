data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  github_subjects = concat(
    [for branch in var.allowed_branches : "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${branch}"],
    var.allow_pull_request ? ["repo:${var.github_org}/${var.github_repo}:pull_request"] : [],
  )

  ssm_parameter_arn = var.ssm_parameter_path_prefix != "" ? (
    "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${trim(var.ssm_parameter_path_prefix, "/")}/*"
  ) : ""
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    data.tls_certificate.github.certificates[0].sha1_fingerprint,
  ]

  tags = local.common_tags
}

data "aws_iam_policy_document" "github_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.existing[0].arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.github_subjects
    }
  }
}

data "aws_iam_openid_connect_provider" "existing" {
  count = var.create_oidc_provider ? 0 : 1
  url   = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_actions" {
  name               = "${local.name_prefix}-github-actions"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "deploy" {
  statement {
    sid    = "ECRAuth"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = length(var.ecr_repository_arns) > 0 ? [1] : []
    content {
      sid    = "ECRPush"
      effect = "Allow"
      actions = [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
      ]
      resources = var.ecr_repository_arns
    }
  }

  statement {
    sid    = "ECSDeploy"
    effect = "Allow"
    actions = [
      "ecs:DescribeClusters",
      "ecs:DescribeServices",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:UpdateService",
      "ecs:ListServices",
    ]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = length(var.ecs_pass_role_arns) > 0 ? [1] : []
    content {
      sid    = "ECSPassRole"
      effect = "Allow"
      actions = [
        "iam:PassRole",
      ]
      resources = var.ecs_pass_role_arns

      condition {
        test     = "StringEquals"
        variable = "iam:PassedToService"
        values   = ["ecs-tasks.amazonaws.com"]
      }
    }
  }

  dynamic "statement" {
    for_each = local.ssm_parameter_arn != "" ? [1] : []
    content {
      sid    = "ReadFrontendBuildEnv"
      effect = "Allow"
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
      ]
      resources = [local.ssm_parameter_arn]
    }
  }
}

resource "aws_iam_role_policy" "deploy" {
  name   = "${local.name_prefix}-github-deploy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.deploy.json
}

data "aws_iam_policy_document" "terraform" {
  count = var.enable_terraform_permissions ? 1 : 0

  dynamic "statement" {
    for_each = var.terraform_state_bucket_arn != "" ? [1] : []
    content {
      sid    = "TerraformStateS3"
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
      ]
      resources = [
        var.terraform_state_bucket_arn,
        "${var.terraform_state_bucket_arn}/*",
      ]
    }
  }

  dynamic "statement" {
    for_each = var.terraform_lock_table_arn != "" ? [1] : []
    content {
      sid    = "TerraformStateLock"
      effect = "Allow"
      actions = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:DescribeTable",
      ]
      resources = [var.terraform_lock_table_arn]
    }
  }

  statement {
    sid    = "TerraformApplyRegion"
    effect = "Allow"
    actions = [
      "*",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [data.aws_region.current.name]
    }
  }
}

resource "aws_iam_role_policy" "terraform" {
  count = var.enable_terraform_permissions ? 1 : 0

  name   = "${local.name_prefix}-github-terraform"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.terraform[0].json
}
