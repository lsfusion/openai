# inject_tools.py (фрагмент)
import os, json, logging
from typing import Any, Dict, List

logger = logging.getLogger("inject_tools")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [inject_tools] %(levelname)s %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

def _env(name: str, default: str = "") -> str:
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
    return {"servers": {"default_mcp": {"server_url": url, "headers": headers}}}

class InjectToolsGuardrail:
    def __init__(self, *args, **kwargs):
        logger.info("Initializing InjectToolsGuardrail args=%s kwargs=%s", args, kwargs)

    # --- ONE CORE METHOD ---
    def _inject_tools_into_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        # single place to add/merge tools for both Chat + Responses
        tools = list(kwargs.get("tools", []))
        existing = {t.get("type") for t in tools if isinstance(t, dict)}

        # file_search
        vs_ids = _vector_store_ids()
        if vs_ids and "file_search" not in existing:
            tools.append({"type": "file_search", "file_search": {"vector_store_ids": vs_ids}})
            logger.info("Added file_search tool vector_store_ids=%s", vs_ids)

        # mcp (dedupe by URL)
        mcp_url = _env("MCP_URL")
        if mcp_url:
            has_same = False
            for t in tools:
                if t.get("type") == "mcp":
                    for s in t.get("mcp", {}).get("servers", {}).values():
                        if s.get("server_url") == mcp_url:
                            has_same = True
                            break
                if has_same:
                    break
            if not has_same:
                tools.append({"type": "mcp", "mcp": _mcp_server_def()})
                logger.info("Added mcp tool server_url=%s", mcp_url)
            else:
                logger.info("MCP tool with same URL already present: %s", mcp_url)

        if tools:
            kwargs["tools"] = tools
            kwargs.setdefault("tool_choice", "auto")

        # short summary for logs
        try:
            short = {"tools": [{"type": t.get("type")} for t in kwargs.get("tools", [])],
                     "tool_choice": kwargs.get("tool_choice")}
            logger.info("Injected: %s", json.dumps(short))
        except Exception:
            logger.exception("Failed to log summary")

        return kwargs

    # --- Chat Completions hook (wrapper) ---
    async def async_pre_call_hook(self, model: str, messages: List[Dict[str, Any]], kwargs: Dict[str, Any], **_):
        logger.info("pre_call_hook (chat) model=%s", model)
        kwargs = self._inject_tools_into_kwargs(kwargs)
        return {"messages": messages, "kwargs": kwargs}  # required shape

    # --- Responses API hook (wrapper) ---
    async def async_pre_response_call_hook(self, model: str, input: Any, kwargs: Dict[str, Any], **_):
        logger.info("pre_response_call_hook (responses) model=%s", model)
        kwargs = self._inject_tools_into_kwargs(kwargs)
        return {"input": input, "kwargs": kwargs}  # required shape
