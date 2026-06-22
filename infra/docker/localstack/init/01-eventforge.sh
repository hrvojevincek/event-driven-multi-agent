#!/bin/bash
# Bootstrap EventForge AWS resources in LocalStack
set -euo pipefail

awslocal events create-event-bus --name eventforge-bus || true

for queue in ingestion embedding knowledge-mining research synthesis dlq; do
  awslocal sqs create-queue --queue-name "eventforge-${queue}" || true
done

INGESTION_QUEUE_URL="$(awslocal sqs get-queue-url --queue-name eventforge-ingestion --query 'QueueUrl' --output text)"
INGESTION_QUEUE_ARN="$(awslocal sqs get-queue-attributes \
  --queue-url "${INGESTION_QUEUE_URL}" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)"

awslocal events put-rule \
  --name eventforge-query-submitted-to-ingestion \
  --event-bus-name eventforge-bus \
  --event-pattern '{"detail-type":["eventforge.query.submitted"]}' \
  || true

awslocal events put-targets \
  --rule eventforge-query-submitted-to-ingestion \
  --event-bus-name eventforge-bus \
  --targets "Id=ingestion-queue,Arn=${INGESTION_QUEUE_ARN}" \
  || true

EMBEDDING_QUEUE_URL="$(awslocal sqs get-queue-url --queue-name eventforge-embedding --query 'QueueUrl' --output text)"
EMBEDDING_QUEUE_ARN="$(awslocal sqs get-queue-attributes \
  --queue-url "${EMBEDDING_QUEUE_URL}" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)"

awslocal events put-rule \
  --name eventforge-ingestion-completed-to-embedding \
  --event-bus-name eventforge-bus \
  --event-pattern '{"detail-type":["eventforge.ingestion.completed"]}' \
  || true

awslocal events put-targets \
  --rule eventforge-ingestion-completed-to-embedding \
  --event-bus-name eventforge-bus \
  --targets "Id=embedding-queue,Arn=${EMBEDDING_QUEUE_ARN}" \
  || true

# Wire DLQ redrive policy (configure in Phase 2)
echo "EventForge LocalStack resources initialized."
