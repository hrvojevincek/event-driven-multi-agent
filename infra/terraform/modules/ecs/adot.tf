variable "adot_collector_image" {
  description = "ADOT collector sidecar image when otel_enabled is true."
  type        = string
  default     = "public.ecr.aws/aws-observability/aws-otel-collector:v0.43.1"
}

variable "adot_config_content" {
  description = "ADOT collector YAML for AOT_CONFIG_CONTENT sidecar env var."
  type        = string
  default     = ""
  sensitive   = true
}

locals {
  otlp_endpoint_effective = var.otel_enabled ? "http://127.0.0.1:4317" : var.otel_exporter_otlp_endpoint

  api_memory_effective    = var.otel_enabled ? max(var.api_memory, 2048) : var.api_memory
  worker_memory_effective = var.otel_enabled ? max(var.worker_memory, 2048) : var.worker_memory

  adot_sidecar_enabled = var.otel_enabled && trimspace(var.adot_config_content) != ""

  adot_sidecar_container = local.adot_sidecar_enabled ? {
    name      = "aws-otel-collector"
    image     = var.adot_collector_image
    essential = false
    command   = ["--config=env:AOT_CONFIG_CONTENT"]
    environment = [
      { name = "AOT_CONFIG_CONTENT", value = var.adot_config_content },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.adot[0].name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "adot"
      }
    }
  } : null

  api_container_depends_on = local.adot_sidecar_container != null ? [{
    containerName = local.adot_sidecar_container.name
    condition     = "START"
  }] : []

  worker_container_depends_on = local.adot_sidecar_container != null ? [{
    containerName = local.adot_sidecar_container.name
    condition     = "START"
  }] : []
}

resource "aws_cloudwatch_log_group" "adot" {
  count = local.adot_sidecar_enabled ? 1 : 0

  name              = "/ecs/${local.name_prefix}/adot"
  retention_in_days = 14
  tags              = local.common_tags
}
