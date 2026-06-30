locals {
  frontend_build_ssm_path = "/${var.project_name}/${var.environment}/frontend-build"
}

resource "aws_ssm_parameter" "frontend_build_env" {
  for_each = {
    for key, value in {
      NEXT_PUBLIC_API_URL               = "http://${module.ecs.alb_dns_name}"
      NEXT_PUBLIC_APP_URL               = var.app_base_url != "" ? trim(var.app_base_url, "/") : "http://${module.ecs.alb_dns_name}"
      NEXT_PUBLIC_AUTH_DISABLED         = var.auth_disabled ? "true" : "false"
      NEXT_PUBLIC_COGNITO_USER_POOL_ID  = module.cognito.user_pool_id
      NEXT_PUBLIC_COGNITO_APP_CLIENT_ID = module.cognito.app_client_id
      NEXT_PUBLIC_COGNITO_REGION        = var.aws_region
      NEXT_PUBLIC_COGNITO_DOMAIN        = module.cognito.hosted_ui_domain_fqdn != null ? module.cognito.hosted_ui_domain_fqdn : ""
    } : key => value if value != ""
  }

  name  = "${local.frontend_build_ssm_path}/${each.key}"
  type  = "String"
  value = each.value

  tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}
