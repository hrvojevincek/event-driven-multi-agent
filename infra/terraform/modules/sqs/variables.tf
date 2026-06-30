variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "eventforge"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "queue_prefix" {
  description = "Prefix for SQS queue names (matches Settings.sqs_queue_prefix)."
  type        = string
  default     = "eventforge"
}

variable "max_receive_count" {
  description = "Max receives before redrive to DLQ."
  type        = number
  default     = 3
}

variable "tags" {
  description = "Additional tags applied to SQS resources."
  type        = map(string)
  default     = {}
}
