import os, json, logging
from typing import Dict, Any

log = logging.getLogger("inject_tools_cb")
if not log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [inject_tools_cb] %(levelname)s %(message)s"))
    log.addHandler(h)
log.setLevel(logging.INFO)

def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default

def _vector_store_ids():
    raw = _env("VECTOR_STORE_IDS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]

class InjectToolsCallback:
    async def async_pre_call_hook(self, user_api_key_dict, cache, data: Dict[str, Any], call_type: str):
        # Only inject for Responses API
        if call_type != "responses":
            return data

        tools = list(data.get("tools", []))
        existing = {t.get("type") for t in tools if isinstance(t, dict)}

        # add file_search
        vs_ids = _vector_store_ids()
        if vs_ids and "file_search" not in existing:
            tools.append({
                "type": "file_search",
                "file_search": {"vector_store_ids": vs_ids}
            })
            log.info("Added file_search tool vector_store_ids=%s", vs_ids)

        # add MCP
        mcp_url = _env("MCP_URL", "")
        if mcp_url and "mcp" not in existing:
            tools.append({
                "type": "mcp",
                "mcp": {
                    "servers": {
                        "default_mcp": {
                            "server_url": mcp_url,
                            "headers": {}
                        }
                    }
                }
            })
            log.info("Added mcp tool server_url=%s", mcp_url)

        if tools:
            data["tools"] = tools
            data.setdefault("tool_choice", "auto")

        log.info("Injected for responses: %s", json.dumps(
            {"types": [t.get("type") for t in tools], "tool_choice": data.get("tool_choice")}
        ))

        return data

# ✅ ВАЖНО: LiteLLM ожидает instance, а не модуль
proxy_handler_instance = InjectToolsCallback()
