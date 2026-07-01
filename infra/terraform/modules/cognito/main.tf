locals {
  name_prefix = "${var.project_name}-${var.environment}"
  oauth_base  = var.app_base_url != "" ? trim(var.app_base_url, "/") : "http://localhost:3000"

  # Cognito OAuth callbacks must use HTTPS unless the host is localhost/127.0.0.1.
  oauth_enabled = (
    startswith(local.oauth_base, "https://") ||
    can(regex("^http://localhost(:[0-9]+)?$", local.oauth_base)) ||
    can(regex("^http://127\\.0\\.0\\.1(:[0-9]+)?$", local.oauth_base))
  )

  callback_urls           = local.oauth_enabled ? ["${local.oauth_base}/auth/callback"] : ["http://localhost:3000/auth/callback"]
  logout_urls             = local.oauth_enabled ? ["${local.oauth_base}/"] : ["http://localhost:3000/"]
  create_hosted_ui_domain = var.create_domain && local.oauth_enabled

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

resource "aws_cognito_user_pool" "this" {
  name = "${local.name_prefix}-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-users"
  })
}

resource "aws_cognito_user_pool_client" "web" {
  name         = "${local.name_prefix}-web"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = false

  allowed_oauth_flows_user_pool_client = local.oauth_enabled
  allowed_oauth_flows                  = local.oauth_enabled ? ["code"] : []
  allowed_oauth_scopes                 = local.oauth_enabled ? ["openid", "email", "profile"] : []

  callback_urls = local.callback_urls
  logout_urls   = local.logout_urls

  supported_identity_providers = ["COGNITO"]

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]

  prevent_user_existence_errors = "ENABLED"

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}

resource "aws_cognito_user_pool_domain" "this" {
  count = local.create_hosted_ui_domain ? 1 : 0

  domain       = var.domain_prefix
  user_pool_id = aws_cognito_user_pool.this.id
}
