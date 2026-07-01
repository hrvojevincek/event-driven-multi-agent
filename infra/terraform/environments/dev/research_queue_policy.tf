# Single SQS policy for eventforge-research when Step Functions is enabled.
# EventBridge (task.dispatched) and Step Functions (Map fan-out) must share one policy document.

data "aws_iam_policy_document" "research_queue_combined" {
  count = var.enable_step_functions_research ? 1 : 0

  statement {
    sid    = "AllowEventBridgeSendMessage"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [module.sqs.queue_arns["research"]]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = module.eventbridge.queue_eventbridge_rule_arns["research"]
    }
  }

  statement {
    sid    = "AllowStepFunctionsSendMessage"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [module.sqs.queue_arns["research"]]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [module.step_functions[0].state_machine_arn]
    }
  }
}

resource "aws_sqs_queue_policy" "research_combined" {
  count = var.enable_step_functions_research ? 1 : 0

  queue_url = module.sqs.queue_urls["research"]
  policy    = data.aws_iam_policy_document.research_queue_combined[0].json
}
