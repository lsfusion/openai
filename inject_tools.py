# inject_tools.py
import os, json
from typing import Any, Dict, Optional

def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default

def _vector_store_ids() -> list[str]:
    raw = _env("VECTOR_STORE_IDS", "")
    ids = [x.strip() for x in raw.split(",") if x.strip()]
    return ids or []

def _mcp_server_def() -> Dict[str, Any]:
    base = _env("MCP_BASE_URL")
    path = _env("MCP_PATH", "")
    if base and path and path.startswith('/'):
        server_url = f"{base}{path}"
    else:
        server_url = base or path

    headers_json = _env("MCP_HEADERS_JSON", "")
    headers: Dict[str, str] = {}
    if headers_json:
        try:
            headers = json.loads(headers_json)
            if not isinstance(headers, dict):
                headers = {}
        except Exception:
            headers = {}

    label = _env("MCP_SERVER_LABEL", "my_mcp")
    return {
        "servers": {
            label: {
                "server_url": server_url,
                "headers": headers
            }
        }
    }

class InjectToolsGuardrail:
    async def async_pre_call_hook(
        self,
        model: str,
        messages: list[dict],
        kwargs: Dict[str, Any],
        **_
    ) -> Optional[Dict[str, Any]]:
        tools = kwargs.get("tools", [])
        existing_types = {t.get("type") for t in tools}

        # file_search
        vs_ids = _vector_store_ids()
        if vs_ids and "file_search" not in existing_types:
            tools.append({
                "type": "file_search",
                "file_search": { "vector_store_ids": vs_ids }
            })

        # mcp
        if ("mcp" not in existing_types) and (_env("MCP_BASE_URL") or _env("MCP_PATH")):
            tools.append({
                "type": "mcp",
                "mcp": _mcp_server_def()
            })

        kwargs["tools"] = tools
        kwargs.setdefault("tool_choice", "auto")
        return kwargs
