locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  # Mirrors infra/docker/localstack/init/01-eventforge.sh
  routes = {
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
    knowledge-mined-to-research = {
      detail_type = "eventforge.knowledge.mined"
      queue_key   = "research"
    }
    research-task-dispatched-to-research = {
      detail_type = "eventforge.research.task.dispatched"
      queue_key   = "research"
    }
    research-task-completed-to-synthesis = {
      detail_type = "eventforge.research.task.completed"
      queue_key   = "synthesis"
    }
  }
}

resource "aws_cloudwatch_event_bus" "this" {
  name = var.event_bus_name

  tags = merge(local.common_tags, {
    Name = var.event_bus_name
  })
}

resource "aws_cloudwatch_event_rule" "route" {
  for_each = local.routes

  name           = "${local.name_prefix}-${each.key}"
  description    = "Route ${each.value.detail_type} to ${each.value.queue_key} queue"
  event_bus_name = aws_cloudwatch_event_bus.this.name
  event_pattern = jsonencode({
    "detail-type" = [each.value.detail_type]
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "route" {
  for_each = local.routes

  rule           = aws_cloudwatch_event_rule.route[each.key].name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  target_id      = each.key
  arn            = var.queue_arns[each.value.queue_key]
}

locals {
  rules_by_queue_key = {
    for queue_key in distinct([for route in local.routes : route.queue_key]) :
    queue_key => [
      for name, route in local.routes : aws_cloudwatch_event_rule.route[name].arn
      if route.queue_key == queue_key
    ]
  }
}

data "aws_iam_policy_document" "sqs_eventbridge" {
  for_each = local.rules_by_queue_key

  statement {
    sid    = "AllowEventBridgeSendMessage"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [var.queue_arns[each.key]]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = each.value
    }
  }
}

resource "aws_sqs_queue_policy" "eventbridge" {
  for_each = local.rules_by_queue_key

  queue_url = var.queue_urls[each.key]
  policy    = data.aws_iam_policy_document.sqs_eventbridge[each.key].json
}
