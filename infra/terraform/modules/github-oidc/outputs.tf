output "role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC."
  value       = aws_iam_role.github_actions.arn
}

output "role_name" {
  description = "IAM role name for GitHub Actions OIDC."
  value       = aws_iam_role.github_actions.name
}

output "oidc_provider_arn" {
  description = "GitHub OIDC provider ARN."
  value = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.existing[0].arn
}
