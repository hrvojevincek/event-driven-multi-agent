variable "sqs_queue_prefix" {
  description = "SQS queue name prefix (matches Settings.sqs_queue_prefix)."
  type        = string
  default     = "eventforge"
}

variable "sqs_max_receive_count" {
  description = "SQS max receive count before DLQ redrive."
  type        = number
  default     = 3
}

variable "event_bus_name" {
  description = "EventBridge bus name (matches Settings.event_bus_name)."
  type        = string
  default     = "eventforge-bus"
}

module "sqs" {
  source = "../../modules/sqs"

  project_name      = var.project_name
  environment       = var.environment
  queue_prefix      = var.sqs_queue_prefix
  max_receive_count = var.sqs_max_receive_count
  tags              = var.tags
}

module "eventbridge" {
  source = "../../modules/eventbridge"

  project_name   = var.project_name
  environment    = var.environment
  event_bus_name = var.event_bus_name
  queue_arns     = module.sqs.queue_arns
  queue_urls     = module.sqs.queue_urls
  tags           = var.tags
}
