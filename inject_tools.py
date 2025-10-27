# inject_tools.py
import os, json
from typing import Any, Dict, Optional

def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default

def _vector_store_ids() -> list[str]:
    raw = _env("VECTOR_STORE_IDS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]

def _mcp_server_def() -> Dict[str, Any]:
    url = _env("MCP_URL", "")
    headers_json = _env("MCP_HEADERS_JSON", "")
    headers = {}

    if headers_json:
        try:
            val = json.loads(headers_json)
            if isinstance(val, dict):
                headers = val
        except Exception:
            pass

    return {
        "servers": {
            "default_mcp": { "server_url": url, "headers": headers }
        }
    }

class InjectToolsGuardrail:
    async def async_pre_call_hook(self, model: str, messages: list[dict], kwargs: Dict[str, Any], **_):
        tools = kwargs.get("tools", [])
        existing = {t.get("type") for t in tools}

        vs_ids = _vector_store_ids()
        if vs_ids and "file_search" not in existing:
            tools.append({
                "type": "file_search",
                "file_search": { "vector_store_ids": vs_ids }
            })

        if _env("MCP_URL") and "mcp" not in existing:
            tools.append({
                "type": "mcp",
                "mcp": _mcp_server_def()
            })

        kwargs["tools"] = tools
        kwargs.setdefault("tool_choice", "auto")
        return kwargs
