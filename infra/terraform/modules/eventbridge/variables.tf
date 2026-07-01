variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "eventforge"
}

variable "environment" {
  description = "Deployment environment (dev, prod)."
  type        = string
}

variable "event_bus_name" {
  description = "Custom EventBridge bus name (matches Settings.event_bus_name)."
  type        = string
  default     = "eventforge-bus"
}

variable "queue_arns" {
  description = "SQS queue ARNs from modules/sqs (keys: ingestion, embedding, knowledge_mining, research, synthesis)."
  type        = map(string)
}

variable "queue_urls" {
  description = "SQS queue URLs from modules/sqs (same keys as queue_arns + dlq)."
  type        = map(string)
}

variable "tags" {
  description = "Additional tags applied to EventBridge resources."
  type        = map(string)
  default     = {}
}

variable "enable_step_functions_research" {
  description = "When true, route research.all_completed to synthesis and defer research queue policy to the environment root."
  type        = bool
  default     = false
}
