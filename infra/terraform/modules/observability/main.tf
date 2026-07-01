locals {
  name_prefix      = "${var.project_name}-${var.environment}"
  cluster_name     = "${local.name_prefix}-cluster"
  api_service_name = "${local.name_prefix}-api"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

resource "aws_cloudwatch_metric_alarm" "dlq_messages_visible" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-dlq-messages-visible"
  alarm_description   = "DLQ has visible messages — pipeline terminal failures or poison pills."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = var.dlq_message_alarm_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = var.dlq_queue_name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_running_tasks_low" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name_prefix}-api-running-tasks-low"
  alarm_description   = "API ECS service has no running tasks."
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RunningTaskCount"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  treat_missing_data  = "breaching"

  dimensions = {
    ClusterName = local.cluster_name
    ServiceName = local.api_service_name
  }

  tags = local.common_tags
}
