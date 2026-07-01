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

output "queue_eventbridge_rule_arns" {
  description = "EventBridge rule ARNs grouped by SQS queue key (for combined queue policies)."
  value       = local.rules_by_queue_key
}
