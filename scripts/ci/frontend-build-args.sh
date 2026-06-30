#!/usr/bin/env bash
# Print docker build --build-arg flags from SSM parameters (frontend NEXT_PUBLIC_*).
set -euo pipefail

PATH_PREFIX="${FRONTEND_BUILD_SSM_PATH:-/eventforge/dev/frontend-build}"
REGION="${AWS_REGION:-eu-west-2}"

ARGS=()
while IFS=$'\t' read -r name value; do
  key="${name##*/}"
  ARGS+=("--build-arg" "${key}=${value}")
done < <(
  aws ssm get-parameters-by-path \
    --region "$REGION" \
    --path "$PATH_PREFIX" \
    --recursive \
    --query 'sort_by(Parameters, &Name)[].[Name,Value]' \
    --output text
)

if [ "${#ARGS[@]}" -eq 0 ]; then
  echo "No SSM parameters found under $PATH_PREFIX" >&2
  exit 1
fi

printf '%s\n' "${ARGS[@]}"
