output "dlq_arn" {
  description = "Dead-letter queue ARN."
  value       = aws_sqs_queue.dlq.arn
}

output "dlq_url" {
  description = "Dead-letter queue URL."
  value       = aws_sqs_queue.dlq.url
}

output "queue_arns" {
  description = "Worker + DLQ ARNs keyed by stage (ingestion, embedding, knowledge_mining, research, synthesis, dlq)."
  value = merge(
    { for key, queue in aws_sqs_queue.worker : key => queue.arn },
    { dlq = aws_sqs_queue.dlq.arn },
  )
}

output "queue_urls" {
  description = "Worker + DLQ URLs keyed by stage."
  value = merge(
    { for key, queue in aws_sqs_queue.worker : key => queue.url },
    { dlq = aws_sqs_queue.dlq.url },
  )
}

output "worker_queue_arns" {
  description = "All queue ARNs consumed by ECS workers (including DLQ worker IAM)."
  value = concat(
    [for queue in aws_sqs_queue.worker : queue.arn],
    [aws_sqs_queue.dlq.arn],
  )
}

output "queue_prefix" {
  description = "Queue name prefix."
  value       = var.queue_prefix
}
