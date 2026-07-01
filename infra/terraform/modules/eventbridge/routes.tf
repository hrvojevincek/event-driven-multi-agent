locals {
  # Mirrors infra/docker/localstack/init/01-eventforge.sh
  base_routes = {
    query-submitted-to-ingestion = {
      detail_type = "eventforge.query.submitted"
      queue_key   = "ingestion"
    }
    ingestion-completed-to-embedding = {
      detail_type = "eventforge.ingestion.completed"
      queue_key   = "embedding"
    }
    embedding-completed-to-knowledge = {
      detail_type = "eventforge.embedding.completed"
      queue_key   = "knowledge_mining"
    }
    research-task-dispatched-to-research = {
      detail_type = "eventforge.research.task.dispatched"
      queue_key   = "research"
    }
  }

  local_research_routes = var.enable_step_functions_research ? {} : {
    knowledge-mined-to-research = {
      detail_type = "eventforge.knowledge.mined"
      queue_key   = "research"
    }
    research-task-completed-to-synthesis = {
      detail_type = "eventforge.research.task.completed"
      queue_key   = "synthesis"
    }
  }

  step_functions_routes = var.enable_step_functions_research ? {
    research-all-completed-to-synthesis = {
      detail_type = "eventforge.research.all_completed"
      queue_key   = "synthesis"
    }
  } : {}

  routes = merge(local.base_routes, local.local_research_routes, local.step_functions_routes)

  rules_by_queue_key = {
    for queue_key in distinct([for route in local.routes : route.queue_key]) :
    queue_key => [
      for name, route in local.routes : aws_cloudwatch_event_rule.route[name].arn
      if route.queue_key == queue_key
    ]
  }

  # Research queue policy is merged with Step Functions at the environment root when SF is enabled.
  queue_policy_keys = var.enable_step_functions_research ? {
    for queue_key, rule_arns in local.rules_by_queue_key : queue_key => rule_arns
    if queue_key != "research"
  } : local.rules_by_queue_key
}
