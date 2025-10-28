# inject_tools.py
import os, json, logging
from typing import Any, Dict, List

# Minimal logger that prints to stdout (Docker will capture it)
logger = logging.getLogger("inject_tools")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [inject_tools] %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def _env(name: str, default: str = "") -> str:
    # get env var as trimmed string
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default

def _vector_store_ids() -> List[str]:
    raw = _env("VECTOR_STORE_IDS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]

def _mcp_server_def() -> Dict[str, Any]:
    url = _env("MCP_URL", "")
    headers_json = _env("MCP_HEADERS_JSON", "")
    headers: Dict[str, str] = {}

    if headers_json:
        try:
            val = json.loads(headers_json)
            if isinstance(val, dict):
                headers = {str(k): str(v) for k, v in val.items()}
        except Exception:
            logger.exception("Failed to parse MCP_HEADERS_JSON")

    return {
        "servers": {
            "default_mcp": {"server_url": url, "headers": headers}
        }
    }

class InjectToolsGuardrail:
    def __init__(self, *args, **kwargs):
        # accept constructor args from LiteLLM (guardrail_name, mode, etc.)
        # minimal constructor; log its args for debugging
        logger.info("Initializing InjectToolsGuardrail args=%s kwargs=%s", args, kwargs)

    # hook to modify model request before API call
    async def async_pre_call_hook(self, model: str, messages: List[Dict[str, Any]], kwargs: Dict[str, Any], **_):
        logger.info("pre_call_hook invoked model=%s messages_count=%d", model, len(messages) if messages else 0)
        tools = kwargs.get("tools", [])
        existing = {t.get("type") for t in tools if isinstance(t, dict)}
        logger.info("existing tool types=%s", sorted([t for t in existing if t]))

        # vector-search tool
        vs_ids = _vector_store_ids()
        if vs_ids and "file_search" not in existing:
            tools.append({
                "type": "file_search",
                "file_search": {"vector_store_ids": vs_ids}
            })
            logger.info("Added file_search tool vector_store_ids=%s", vs_ids)

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
            if has_same_mcp:
                logger.info("MCP tool with same URL already present: %s", mcp_url)
            else:
                tools.append({
                    "type": "mcp",
                    "mcp": _mcp_server_def()
                })
                logger.info("Added mcp tool server_url=%s", mcp_url)

        if tools:
            kwargs["tools"] = tools
            kwargs.setdefault("tool_choice", "auto")

        # log final kwargs (but avoid dumping huge content)
        try:
            short = {
                "tools": [{ "type": t.get("type") } for t in kwargs.get("tools", [])],
                "tool_choice": kwargs.get("tool_choice")
            }
            logger.info("Returning from pre_call_hook: %s", json.dumps(short))
        except Exception:
            logger.exception("Failed to log final kwargs")

        # must return both messages and kwargs
        return {"messages": messages, "kwargs": kwargs}
