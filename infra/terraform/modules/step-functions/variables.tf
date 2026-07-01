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
  description = "EventBridge bus name."
  type        = string
}

variable "event_bus_arn" {
  description = "EventBridge bus ARN."
  type        = string
}

variable "research_queue_url" {
  description = "Research worker SQS queue URL."
  type        = string
}

variable "research_queue_arn" {
  description = "Research worker SQS queue ARN."
  type        = string
}

variable "ecs_cluster_arn" {
  description = "ECS cluster ARN for the prepare fan-out task."
  type        = string
}

variable "research_task_definition_arn" {
  description = "Research worker ECS task definition ARN (reused for one-shot prepare step)."
  type        = string
}

variable "ecs_execution_role_arn" {
  description = "ECS task execution role ARN (PassRole for runTask)."
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ECS task role ARN (PassRole for runTask)."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS runTask networking."
  type        = list(string)
}

variable "worker_security_group_id" {
  description = "Worker security group for ECS runTask networking."
  type        = string
}

variable "tags" {
  description = "Additional tags applied to Step Functions resources."
  type        = map(string)
  default     = {}
}
