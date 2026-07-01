locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })
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
  for_each = local.queue_policy_keys

  queue_url = var.queue_urls[each.key]
  policy    = data.aws_iam_policy_document.sqs_eventbridge[each.key].json
}
