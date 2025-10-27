# inject_tools.py
import os, json
from typing import Any, Dict, List

def _env(name: str, default: str = "") -> str:
    # get env var as trimmed string
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default

def _vector_store_ids() -> List[str]:
    # return VECTOR_STORE_IDS as list[str]
    raw = _env("VECTOR_STORE_IDS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]

def _mcp_server_def() -> Dict[str, Any]:
    # build MCP server config
    url = _env("MCP_URL", "")
    headers_json = _env("MCP_HEADERS_JSON", "")
    headers: Dict[str, str] = {}

    if headers_json:
        try:
            val = json.loads(headers_json)
            if isinstance(val, dict):
                headers = {str(k): str(v) for k, v in val.items()}
        except Exception:
            pass

    return {
        "servers": {
            "default_mcp": {"server_url": url, "headers": headers}
        }
    }

class InjectToolsGuardrail:
    def __init__(self, *args, **kwargs):
        # accept constructor args from LiteLLM (guardrail_name, mode, etc.)
        pass

    # hook to modify model request before API call
    async def async_pre_call_hook(self, model: str, messages: List[Dict[str, Any]], kwargs: Dict[str, Any], **_):
        tools = kwargs.get("tools", [])
        existing = {t.get("type") for t in tools if isinstance(t, dict)}

        # vector-search tool
        vs_ids = _vector_store_ids()
        if vs_ids and "file_search" not in existing:
            tools.append({
                "type": "file_search",
                "file_search": {"vector_store_ids": vs_ids}
            })

        # mcp tool (avoid duplicates with same URL)
        mcp_url = _env("MCP_URL")
        if mcp_url:
            has_same_mcp = False
            for t in tools:
                if t.get("type") == "mcp":
                    servers = t.get("mcp", {}).get("servers", {})
                    for s in servers.values():
                        if s.get("server_url") == mcp_url:
                            has_same_mcp = True
                            break
                if has_same_mcp:
                    break
            if not has_same_mcp:
                tools.append({
                    "type": "mcp",
                    "mcp": _mcp_server_def()
                })

        if tools:
            kwargs["tools"] = tools
            kwargs.setdefault("tool_choice", "auto")

        # must return both messages and kwargs
        return {"messages": messages, "kwargs": kwargs}
