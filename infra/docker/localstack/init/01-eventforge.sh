#!/bin/bash
# Bootstrap EventForge AWS resources in LocalStack
set -euo pipefail

MAX_RECEIVE_COUNT="${SQS_MAX_RECEIVE_COUNT:-3}"
WORKER_QUEUES=(ingestion embedding knowledge-mining research synthesis)

configure_redrive_policy() {
  local queue_name="$1"
  local queue_url attributes_json

  awslocal sqs create-queue --queue-name "${queue_name}" >/dev/null 2>&1 || true

  queue_url="$(awslocal sqs get-queue-url --queue-name "${queue_name}" --query 'QueueUrl' --output text)"

  attributes_json="$(DLQ_ARN="${DLQ_ARN}" MAX_RECEIVE_COUNT="${MAX_RECEIVE_COUNT}" python3 -c '
import json, os

redrive = {
    "deadLetterTargetArn": os.environ["DLQ_ARN"],
    "maxReceiveCount": int(os.environ["MAX_RECEIVE_COUNT"]),
}
print(json.dumps({"RedrivePolicy": json.dumps(redrive)}))
')"

  awslocal sqs set-queue-attributes \
    --queue-url "${queue_url}" \
    --attributes "${attributes_json}"
}

awslocal events create-event-bus --name eventforge-bus || true

awslocal sqs create-queue --queue-name eventforge-dlq >/dev/null 2>&1 || true

DLQ_QUEUE_URL="$(awslocal sqs get-queue-url --queue-name eventforge-dlq --query 'QueueUrl' --output text)"
DLQ_ARN="$(awslocal sqs get-queue-attributes \
  --queue-url "${DLQ_QUEUE_URL}" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)"

for queue in "${WORKER_QUEUES[@]}"; do
  configure_redrive_policy "eventforge-${queue}"
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

KNOWLEDGE_QUEUE_URL="$(awslocal sqs get-queue-url --queue-name eventforge-knowledge-mining --query 'QueueUrl' --output text)"
KNOWLEDGE_QUEUE_ARN="$(awslocal sqs get-queue-attributes \
  --queue-url "${KNOWLEDGE_QUEUE_URL}" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)"

awslocal events put-rule \
  --name eventforge-embedding-completed-to-knowledge \
  --event-bus-name eventforge-bus \
  --event-pattern '{"detail-type":["eventforge.embedding.completed"]}' \
  || true

awslocal events put-targets \
  --rule eventforge-embedding-completed-to-knowledge \
  --event-bus-name eventforge-bus \
  --targets "Id=knowledge-queue,Arn=${KNOWLEDGE_QUEUE_ARN}" \
  || true

RESEARCH_QUEUE_URL="$(awslocal sqs get-queue-url --queue-name eventforge-research --query 'QueueUrl' --output text)"
RESEARCH_QUEUE_ARN="$(awslocal sqs get-queue-attributes \
  --queue-url "${RESEARCH_QUEUE_URL}" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)"

awslocal events put-rule \
  --name eventforge-knowledge-mined-to-research \
  --event-bus-name eventforge-bus \
  --event-pattern '{"detail-type":["eventforge.knowledge.mined"]}' \
  || true

awslocal events put-targets \
  --rule eventforge-knowledge-mined-to-research \
  --event-bus-name eventforge-bus \
  --targets "Id=research-queue,Arn=${RESEARCH_QUEUE_ARN}" \
  || true

awslocal events put-rule \
  --name eventforge-research-task-dispatched-to-research \
  --event-bus-name eventforge-bus \
  --event-pattern '{"detail-type":["eventforge.research.task.dispatched"]}' \
  || true

awslocal events put-targets \
  --rule eventforge-research-task-dispatched-to-research \
  --event-bus-name eventforge-bus \
  --targets "Id=research-dispatch-queue,Arn=${RESEARCH_QUEUE_ARN}" \
  || true

SYNTHESIS_QUEUE_URL="$(awslocal sqs get-queue-url --queue-name eventforge-synthesis --query 'QueueUrl' --output text)"
SYNTHESIS_QUEUE_ARN="$(awslocal sqs get-queue-attributes \
  --queue-url "${SYNTHESIS_QUEUE_URL}" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)"

awslocal events put-rule \
  --name eventforge-research-task-completed-to-synthesis \
  --event-bus-name eventforge-bus \
  --event-pattern '{"detail-type":["eventforge.research.task.completed"]}' \
  || true

awslocal events put-targets \
  --rule eventforge-research-task-completed-to-synthesis \
  --event-bus-name eventforge-bus \
  --targets "Id=synthesis-queue,Arn=${SYNTHESIS_QUEUE_ARN}" \
  || true

echo "EventForge LocalStack resources initialized (DLQ redrive maxReceiveCount=${MAX_RECEIVE_COUNT})."
