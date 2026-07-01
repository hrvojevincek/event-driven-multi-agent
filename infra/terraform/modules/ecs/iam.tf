data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${local.name_prefix}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "execution_secrets" {
  statement {
    sid    = "ReadSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = compact([
      var.postgres_password_secret_arn,
      var.openai_api_key_secret_arn,
      var.anthropic_api_key_secret_arn,
      var.tavily_api_key_secret_arn,
    ])
  }
}

resource "aws_iam_role_policy" "execution_secrets" {
  name   = "${local.name_prefix}-execution-secrets"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution_secrets.json
}

resource "aws_iam_role" "api_task" {
  name               = "${local.name_prefix}-api-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "api_task" {
  statement {
    sid    = "PublishEvents"
    effect = "Allow"
    actions = [
      "events:PutEvents",
    ]
    resources = [var.event_bus_arn]
  }
}

resource "aws_iam_role_policy" "api_task" {
  name   = "${local.name_prefix}-api-task"
  role   = aws_iam_role.api_task.id
  policy = data.aws_iam_policy_document.api_task.json
}

data "aws_iam_policy_document" "api_task_otel" {
  count = var.otel_enabled ? 1 : 0

  statement {
    sid    = "ExportTraces"
    effect = "Allow"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
      "xray:GetSamplingStatisticSummaries",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "api_task_otel" {
  count = var.otel_enabled ? 1 : 0

  name   = "${local.name_prefix}-api-task-otel"
  role   = aws_iam_role.api_task.id
  policy = data.aws_iam_policy_document.api_task_otel[0].json
}

resource "aws_iam_role" "worker_task" {
  name               = "${local.name_prefix}-worker-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "worker_task" {
  statement {
    sid    = "ConsumeQueues"
    effect = "Allow"
    actions = [
      "sqs:GetQueueUrl",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility",
    ]
    resources = length(var.worker_queue_arns) > 0 ? var.worker_queue_arns : ["*"]
  }

  statement {
    sid    = "PublishEvents"
    effect = "Allow"
    actions = [
      "events:PutEvents",
    ]
    resources = [var.event_bus_arn]
  }
}

resource "aws_iam_role_policy" "worker_task" {
  name   = "${local.name_prefix}-worker-task"
  role   = aws_iam_role.worker_task.id
  policy = data.aws_iam_policy_document.worker_task.json
}

resource "aws_iam_role_policy" "worker_task_otel" {
  count = var.otel_enabled ? 1 : 0

  name   = "${local.name_prefix}-worker-task-otel"
  role   = aws_iam_role.worker_task.id
  policy = data.aws_iam_policy_document.api_task_otel[0].json
}

data "aws_iam_policy_document" "worker_step_functions" {
  count = var.step_functions_research_enabled ? 1 : 0

  statement {
    sid    = "CompleteStepFunctionsTasks"
    effect = "Allow"
    actions = [
      "states:SendTaskSuccess",
      "states:SendTaskFailure",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "worker_step_functions" {
  count = var.step_functions_research_enabled ? 1 : 0

  name   = "${local.name_prefix}-worker-step-functions"
  role   = aws_iam_role.worker_task.id
  policy = data.aws_iam_policy_document.worker_step_functions[0].json
}

resource "aws_iam_role" "frontend_task" {
  name               = "${local.name_prefix}-frontend-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = local.common_tags
}
