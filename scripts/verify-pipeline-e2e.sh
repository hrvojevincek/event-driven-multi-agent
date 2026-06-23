#!/usr/bin/env bash
# End-to-end pipeline smoke test: POST /api/v1/queries → poll until all stages complete.
#
# Prerequisites (all must be running):
#   docker compose up -d postgres localstack
#   uv run --project backend uvicorn eventforge.main:app --port 8000
#   make workers   # or: make workers-overmind
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
TOPIC="${TOPIC:-Event-driven architecture patterns}"
POLL_INTERVAL="${POLL_INTERVAL:-2}"
TIMEOUT="${TIMEOUT:-180}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

echo "Checking API health at ${API_URL}/health ..."
curl -sf "${API_URL}/health" >/dev/null || die "API not reachable at ${API_URL}"

echo "Submitting query to ${API_URL}/api/v1/queries ..."
RESPONSE="$(curl -sf -X POST "${API_URL}/api/v1/queries" \
  -H "Content-Type: application/json" \
  -d "{\"topic\": \"${TOPIC}\", \"depth\": \"standard\", \"max_sources\": 5}")"

JOB_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])' <<<"${RESPONSE}")"
CORR_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["correlation_id"])' <<<"${RESPONSE}")"

echo "Created job_id=${JOB_ID} correlation_id=${CORR_ID}"
echo "Polling ${API_URL}/api/v1/queries/${JOB_ID} (timeout ${TIMEOUT}s, interval ${POLL_INTERVAL}s) ..."

ELAPSED=0
DETAIL=""
while (( ELAPSED < TIMEOUT )); do
  DETAIL="$(curl -sf "${API_URL}/api/v1/queries/${JOB_ID}")"
  STATUS="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])' <<<"${DETAIL}")"

  if [[ "${STATUS}" == "completed" ]]; then
    break
  fi
  if [[ "${STATUS}" == "failed" ]]; then
    echo "${DETAIL}" | python3 -m json.tool
    die "Job failed before completion"
  fi

  STAGE_SUMMARY="$(python3 -c '
import json, sys
detail = json.load(sys.stdin)
parts = [s["stage"] + ":" + s["status"] for s in detail["stages"]]
print(" | ".join(parts))
' <<<"${DETAIL}")"
  echo "  [${ELAPSED}s] job=${STATUS}  ${STAGE_SUMMARY}"

  sleep "${POLL_INTERVAL}"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

if [[ -z "${DETAIL}" ]]; then
  die "No job detail received"
fi

FINAL_STATUS="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])' <<<"${DETAIL}")"
if [[ "${FINAL_STATUS}" != "completed" ]]; then
  echo "${DETAIL}" | python3 -m json.tool
  die "Timed out after ${TIMEOUT}s (job status: ${FINAL_STATUS})"
fi

python3 -c '
import json, sys

detail = json.load(sys.stdin)
expected = ("ingestion", "embedding", "knowledge_mining", "research", "synthesis")
stages = {s["stage"]: s["status"] for s in detail["stages"]}

if detail["status"] != "completed":
    print("Expected job status completed, got", detail["status"], file=sys.stderr)
    sys.exit(1)

for name in expected:
    status = stages.get(name)
    if status != "completed":
        print(f"Expected stage {name} completed, got {status!r}", file=sys.stderr)
        sys.exit(1)

print("All pipeline stages completed:")
for name in expected:
    print(f"  - {name}: completed")
print("job_id=" + detail["job_id"] + " correlation_id=" + detail["correlation_id"])
' <<<"${DETAIL}"

echo "E2E pipeline smoke test passed."
