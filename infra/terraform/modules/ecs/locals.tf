locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  workers = {
    ingestion = {
      module    = "eventforge.workers.ingestion"
      otel_name = "eventforge-worker-ingestion"
    }
    embedding = {
      module    = "eventforge.workers.embedding"
      otel_name = "eventforge-worker-embedding"
    }
    knowledge = {
      module    = "eventforge.workers.knowledge"
      otel_name = "eventforge-worker-knowledge"
    }
    research = {
      module    = "eventforge.workers.research"
      otel_name = "eventforge-worker-research"
    }
    synthesis = {
      module    = "eventforge.workers.synthesis"
      otel_name = "eventforge-worker-synthesis"
    }
    dlq = {
      module    = "eventforge.workers.dlq"
      otel_name = "eventforge-worker-dlq"
    }
  }

  api_environment = [
    { name = "ENVIRONMENT", value = var.environment },
    { name = "LOG_LEVEL", value = "INFO" },
    { name = "POSTGRES_HOST", value = var.postgres_host },
    { name = "POSTGRES_PORT", value = tostring(var.postgres_port) },
    { name = "POSTGRES_DB", value = var.postgres_db },
    { name = "POSTGRES_USER", value = var.postgres_user },
    { name = "AWS_REGION", value = var.aws_region },
    { name = "AWS_ENDPOINT_URL", value = "" },
    { name = "EVENT_BUS_NAME", value = var.event_bus_name },
    { name = "SQS_QUEUE_PREFIX", value = var.sqs_queue_prefix },
    { name = "CORS_ORIGINS", value = var.cors_origins },
    { name = "OTEL_ENABLED", value = var.otel_enabled ? "true" : "false" },
    { name = "OTEL_SERVICE_NAME", value = "eventforge-api" },
    { name = "OTEL_EXPORTER_OTLP_ENDPOINT", value = local.otlp_endpoint_effective },
  ]

  api_secrets = concat(
    [{ name = "POSTGRES_PASSWORD", valueFrom = var.postgres_password_secret_arn }],
    var.openai_api_key_secret_arn != "" ? [{ name = "OPENAI_API_KEY", valueFrom = var.openai_api_key_secret_arn }] : [],
    var.anthropic_api_key_secret_arn != "" ? [{ name = "ANTHROPIC_API_KEY", valueFrom = var.anthropic_api_key_secret_arn }] : [],
    var.tavily_api_key_secret_arn != "" ? [{ name = "TAVILY_API_KEY", valueFrom = var.tavily_api_key_secret_arn }] : [],
  )

  worker_environment_base = concat(
    [
      for item in local.api_environment : item
      if !contains(["CORS_ORIGINS", "OTEL_SERVICE_NAME"], item.name)
    ],
    [{
      name  = "RESEARCH_ORCHESTRATION_MODE"
      value = var.step_functions_research_enabled ? "step_functions" : "local"
    }],
  )
}
