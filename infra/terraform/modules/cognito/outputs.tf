output "user_pool_id" {
  description = "Cognito user pool ID."
  value       = aws_cognito_user_pool.this.id
}

output "user_pool_arn" {
  description = "Cognito user pool ARN."
  value       = aws_cognito_user_pool.this.arn
}

output "app_client_id" {
  description = "Public app client ID for Amplify / frontend."
  value       = aws_cognito_user_pool_client.web.id
}

output "hosted_ui_domain" {
  description = "Hosted UI domain prefix (append .auth.<region>.amazoncognito.com)."
  value       = length(aws_cognito_user_pool_domain.this) > 0 ? aws_cognito_user_pool_domain.this[0].domain : null
}

output "hosted_ui_domain_fqdn" {
  description = "Full Hosted UI domain for NEXT_PUBLIC_COGNITO_DOMAIN."
  value       = length(aws_cognito_user_pool_domain.this) > 0 ? "${aws_cognito_user_pool_domain.this[0].domain}.auth.${data.aws_region.current.region}.amazoncognito.com" : null
}

data "aws_region" "current" {}
