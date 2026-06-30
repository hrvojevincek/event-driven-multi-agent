#!/usr/bin/env bash
# Roll out a new backend image to the API and all worker ECS services.
set -euo pipefail

CLUSTER="${ECS_CLUSTER_NAME:?ECS_CLUSTER_NAME required}"
IMAGE="${BACKEND_IMAGE:?BACKEND_IMAGE required}"
PREFIX="${ECS_NAME_PREFIX:-eventforge-dev}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SERVICES=(
  "${PREFIX}-api"
  "${PREFIX}-worker-ingestion"
  "${PREFIX}-worker-embedding"
  "${PREFIX}-worker-knowledge"
  "${PREFIX}-worker-research"
  "${PREFIX}-worker-synthesis"
  "${PREFIX}-worker-dlq"
)

for service in "${SERVICES[@]}"; do
  echo "==> $service"
  "$SCRIPT_DIR/ecs-deploy-service.sh" "$CLUSTER" "$service" "$IMAGE"
done

echo "Backend rollout complete."
