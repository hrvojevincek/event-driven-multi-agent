locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  state_machine_definition = templatefile("${path.module}/research_fanout.asl.json.tpl", {
    ecs_cluster_arn              = var.ecs_cluster_arn
    research_task_definition_arn = var.research_task_definition_arn
    private_subnet_ids           = var.private_subnet_ids
    worker_security_group_id     = var.worker_security_group_id
    research_queue_url           = var.research_queue_url
    event_bus_name               = var.event_bus_name
  })
}

data "aws_iam_policy_document" "step_functions_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "step_functions" {
  name               = "${local.name_prefix}-research-sfn"
  assume_role_policy = data.aws_iam_policy_document.step_functions_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "step_functions" {
  statement {
    sid    = "RunPrepareTask"
    effect = "Allow"
    actions = [
      "ecs:RunTask",
      "ecs:StopTask",
      "ecs:DescribeTasks",
    ]
    resources = ["*"]
  }

  statement {
    sid     = "PassEcsRoles"
    effect  = "Allow"
    actions = ["iam:PassRole"]
    resources = [
      var.ecs_execution_role_arn,
      var.ecs_task_role_arn,
    ]
  }

  statement {
    sid       = "DispatchResearchTasks"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [var.research_queue_arn]
  }

  statement {
    sid       = "PublishAllCompleted"
    effect    = "Allow"
    actions   = ["events:PutEvents"]
    resources = [var.event_bus_arn]
  }
}

resource "aws_iam_role_policy" "step_functions" {
  name   = "${local.name_prefix}-research-sfn"
  role   = aws_iam_role.step_functions.id
  policy = data.aws_iam_policy_document.step_functions.json
}

resource "aws_sfn_state_machine" "research_fanout" {
  name     = "${local.name_prefix}-research-fanout"
  role_arn = aws_iam_role.step_functions.arn

  definition = local.state_machine_definition

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-research-fanout"
  })
}

data "aws_iam_policy_document" "eventbridge_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eventbridge_start_execution" {
  name               = "${local.name_prefix}-research-sfn-start"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "eventbridge_start_execution" {
  statement {
    sid       = "StartResearchFanout"
    effect    = "Allow"
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.research_fanout.arn]
  }
}

resource "aws_iam_role_policy" "eventbridge_start_execution" {
  name   = "${local.name_prefix}-research-sfn-start"
  role   = aws_iam_role.eventbridge_start_execution.id
  policy = data.aws_iam_policy_document.eventbridge_start_execution.json
}

resource "aws_cloudwatch_event_rule" "knowledge_mined_to_sfn" {
  name           = "${local.name_prefix}-knowledge-mined-to-research-sfn"
  description    = "Trigger Step Functions research fan-out on knowledge.mined"
  event_bus_name = var.event_bus_name
  event_pattern = jsonencode({
    "detail-type" = ["eventforge.knowledge.mined"]
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "knowledge_mined_to_sfn" {
  rule           = aws_cloudwatch_event_rule.knowledge_mined_to_sfn.name
  event_bus_name = var.event_bus_name
  target_id      = "research-fanout-sfn"
  arn            = aws_sfn_state_machine.research_fanout.arn
  role_arn       = aws_iam_role.eventbridge_start_execution.arn
}
