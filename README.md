# OpenAI Proxy (MODEL_ID + MCP_URL)

✅ Auto-injects file_search & MCP tools
✅ Single MODEL_ID (base or fine-tuned), soft-default to gpt-4o-mini
✅ Single MCP_URL for MCP integration
✅ GHCR image: ghcr.io/lsfusion/openai-proxy

## Quick run
```bash
OPENAI_API_KEY="sk-..." docker compose up -d --build
```

## Example: fine-tuned
```bash
MODEL_ID="ft:gpt-4o-mini-2025:org_xyz:cool:123"     OPENAI_API_KEY="sk-..."     docker compose up -d --build
```

## Example: enable file search & MCP
```bash
MODEL_ID="gpt-4o-mini"     VECTOR_STORE_IDS="vs_123,vs_456"     MCP_URL="https://my-mcp.example.com/api"     MCP_HEADERS_JSON='{"Authorization":"Bearer XYZ"}'     OPENAI_API_KEY="sk-..."     docker compose up -d --build
```

Proxy available at: http://localhost:4000
