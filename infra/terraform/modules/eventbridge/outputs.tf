output "bus_name" {
  description = "EventBridge bus name."
  value       = aws_cloudwatch_event_bus.this.name
}

output "bus_arn" {
  description = "EventBridge bus ARN for IAM and ECS."
  value       = aws_cloudwatch_event_bus.this.arn
}

output "rule_arns" {
  description = "EventBridge rule ARNs keyed by route name."
  value       = { for name, rule in aws_cloudwatch_event_rule.route : name => rule.arn }
}
