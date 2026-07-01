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

  enable_step_functions_research = var.enable_step_functions_research
}

module "step_functions" {
  count  = var.enable_step_functions_research ? 1 : 0
  source = "../../modules/step-functions"

  project_name   = var.project_name
  environment    = var.environment
  event_bus_name = var.event_bus_name
  event_bus_arn  = module.eventbridge.bus_arn

  research_queue_url = module.sqs.queue_urls["research"]
  research_queue_arn = module.sqs.queue_arns["research"]

  ecs_cluster_arn              = module.ecs.cluster_arn
  research_task_definition_arn = module.ecs.research_task_definition_arn
  ecs_execution_role_arn       = module.ecs.execution_role_arn
  ecs_task_role_arn            = module.ecs.worker_task_role_arn
  private_subnet_ids           = module.networking.private_subnet_ids
  worker_security_group_id     = module.networking.worker_security_group_id

  tags = var.tags
}
