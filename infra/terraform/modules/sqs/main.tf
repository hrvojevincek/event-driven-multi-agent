locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  # Keys match eventbridge module routing; suffixes match LocalStack init.
  worker_queues = {
    ingestion        = "ingestion"
    embedding        = "embedding"
    knowledge_mining = "knowledge-mining"
    research         = "research"
    synthesis        = "synthesis"
  }
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.queue_prefix}-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = "${var.queue_prefix}-dlq"
  })
}

resource "aws_sqs_queue" "worker" {
  for_each = local.worker_queues

  name                       = "${var.queue_prefix}-${each.value}"
  visibility_timeout_seconds = 300
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = merge(local.common_tags, {
    Name = "${var.queue_prefix}-${each.value}"
  })
}
