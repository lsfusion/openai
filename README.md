# OpenAI Proxy — single MODEL_ID (soft default)

## Model selection
- Set a single env var `MODEL_ID` to either a base model (e.g. `gpt-4o-mini`) or your fine-tuned id (e.g. `ft:gpt-4o-mini-2025:org_123:custom:xyz789`).
- If `MODEL_ID` is **not** set, the proxy will default to `gpt-4o-mini` at runtime (soft default).

## Quick start
1) Edit `docker-compose.yml` and set `OPENAI_API_KEY`. Optionally set `MODEL_ID`, `VECTOR_STORE_IDS`, MCP vars.
2) Run:
   ```bash
   docker compose up -d --build
   ```
3) Proxy: `http://localhost:4000`

### Examples
- Base model:
  ```bash
  MODEL_ID="gpt-4o-mini" OPENAI_API_KEY="sk-..." docker compose up -d --build
  ```
- Fine-tuned:
  ```bash
  MODEL_ID="ft:gpt-4o-mini-2025:org_123:custom:xyz789" OPENAI_API_KEY="sk-..." docker compose up -d --build
  ```

## Notes
- Tools auto-selection is on (`tool_choice: "auto"`). `file_search` & MCP are injected by `inject_tools.py`.
- `VECTOR_STORE_IDS`: comma-separated vector store IDs.
- MCP endpoint is parameterized by `MCP_BASE_URL` + `MCP_PATH`; headers via `MCP_HEADERS_JSON` (JSON object).
