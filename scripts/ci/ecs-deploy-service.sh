#!/usr/bin/env bash
# Register a new ECS task definition revision with an updated container image and roll out.
set -euo pipefail

CLUSTER="${1:?cluster name required}"
SERVICE="${2:?service name required}"
IMAGE="${3:?image URI required}"
CONTAINER_NAME="${4:-}"

TASK_DEF_ARN="$(aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "$SERVICE" \
  --query 'services[0].taskDefinition' \
  --output text)"

if [[ -z "$CONTAINER_NAME" ]]; then
  CONTAINER_NAME="$(aws ecs describe-task-definition \
    --task-definition "$TASK_DEF_ARN" \
    --query 'taskDefinition.containerDefinitions[0].name' \
    --output text)"
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

aws ecs describe-task-definition \
  --task-definition "$TASK_DEF_ARN" \
  --query 'taskDefinition' \
  | jq --arg img "$IMAGE" --arg name "$CONTAINER_NAME" '
      .containerDefinitions |= map(if .name == $name then .image = $img else . end)
      | del(
          .taskDefinitionArn,
          .revision,
          .status,
          .requiresAttributes,
          .compatibilities,
          .registeredAt,
          .registeredBy,
          .deregisteredAt
        )
    ' >"$TMP"

NEW_TASK_DEF_ARN="$(aws ecs register-task-definition \
  --cli-input-json "file://$TMP" \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)"

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --task-definition "$NEW_TASK_DEF_ARN" \
  --force-new-deployment \
  --no-cli-pager \
  >/dev/null

echo "Waiting for $SERVICE to stabilize..."
aws ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE"
echo "Deployed $SERVICE with image $IMAGE"
