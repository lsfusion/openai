#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID:-gpt-4o-mini}"
echo "[startup] Using MODEL_ID=${MODEL_ID}"

# Render runtime config from template
sed "s/__MODEL_ID__/${MODEL_ID}/g" /app/litellm_config.template.yaml > /app/litellm_config.yaml

exec litellm --port 4000 --config /app/litellm_config.yaml --debug
