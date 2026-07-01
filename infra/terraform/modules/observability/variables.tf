variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "eventforge"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "eu-west-2"
}

variable "dlq_queue_name" {
  description = "SQS DLQ name for CloudWatch alarm (e.g. eventforge-dlq)."
  type        = string
}

variable "enable_alarms" {
  description = "Create CloudWatch alarms for DLQ depth and API task count."
  type        = bool
  default     = true
}

variable "dlq_message_alarm_threshold" {
  description = "Alarm when ApproximateNumberOfMessagesVisible exceeds this value."
  type        = number
  default     = 0
}

variable "adot_collector_image" {
  description = "ADOT collector image for ECS sidecar tasks."
  type        = string
  default     = "public.ecr.aws/aws-observability/aws-otel-collector:v0.43.1"
}

variable "tags" {
  description = "Additional tags applied to observability resources."
  type        = map(string)
  default     = {}
}
