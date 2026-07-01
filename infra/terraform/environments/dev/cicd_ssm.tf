locals {
  frontend_build_ssm_path = "/${var.project_name}/${var.environment}/frontend-build"
}

resource "aws_ssm_parameter" "frontend_build_env" {
  for_each = {
    for key, value in {
      NEXT_PUBLIC_API_URL = "http://${module.ecs.alb_dns_name}"
      NEXT_PUBLIC_APP_URL = var.app_base_url != "" ? trim(var.app_base_url, "/") : "http://${module.ecs.alb_dns_name}"
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
