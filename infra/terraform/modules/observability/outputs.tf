output "otlp_endpoint" {
  description = "OTLP gRPC endpoint for app containers (ADOT sidecar on localhost)."
  value       = "http://127.0.0.1:4317"
}

output "adot_collector_image" {
  description = "ADOT collector container image URI."
  value       = var.adot_collector_image
}

output "adot_config_content" {
  description = "ADOT collector YAML passed to ECS via AOT_CONFIG_CONTENT."
  value = templatefile("${path.module}/adot-config.yaml.tpl", {
    aws_region = var.aws_region
  })
}

output "dlq_alarm_name" {
  description = "CloudWatch alarm name for DLQ visible messages (null when alarms disabled)."
  value       = var.enable_alarms ? aws_cloudwatch_metric_alarm.dlq_messages_visible[0].alarm_name : null
}

output "api_running_tasks_alarm_name" {
  description = "CloudWatch alarm name for API running task count (null when alarms disabled)."
  value       = var.enable_alarms ? aws_cloudwatch_metric_alarm.api_running_tasks_low[0].alarm_name : null
}
