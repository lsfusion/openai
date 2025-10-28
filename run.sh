#!/usr/bin/env bash
set -euo pipefail

: "${LITELLM_PROXY_API_BASE:=http://127.0.0.1:4000}"
export LITELLM_PROXY_API_BASE

MODEL_ID="${MODEL_ID:-gpt-4o-mini}"
WORKERS="${WORKERS:-2}"  # >= 2 чтобы не было дедлока на самовызовах

# Render runtime config from template
sed "s/__MODEL_ID__/${MODEL_ID}/g" /app/litellm_config.template.yaml > /app/litellm_config.yaml
exec litellm --port 4000 --config /app/litellm_config.yaml --workers "${WORKERS}"
