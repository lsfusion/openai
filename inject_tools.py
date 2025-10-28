import os, json, logging
from typing import Dict, Any

from litellm.integrations.custom_logger import CustomLogger
import litellm
from litellm.proxy.proxy_server import UserAPIKeyAuth, DualCache
from litellm.types.utils import ModelResponseStream
from typing import Any, AsyncGenerator, Optional, Literal

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

class InjectToolsCallback(CustomLogger):
    # Class variables or attributes
    def __init__(self):
        pass

    async def async_pre_call_hook(self, user_api_key_dict, cache, data: Dict[str, Any], call_type: str):

        log.info("Inject %s", call_type)

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

    async def async_post_call_failure_hook(
            self,
            request_data: dict,
            original_exception: Exception,
            user_api_key_dict: UserAPIKeyAuth,
            traceback_str: Optional[str] = None,
    ):
        pass

    async def async_post_call_success_hook(
            self,
            data: dict,
            user_api_key_dict: UserAPIKeyAuth,
            response,
    ):
        pass

    async def async_moderation_hook( # call made in parallel to llm api call
            self,
            data: dict,
            user_api_key_dict: UserAPIKeyAuth,
            call_type: Literal["completion", "embeddings", "image_generation", "moderation", "audio_transcription"],
    ):
        pass

    async def async_post_call_streaming_hook(
            self,
            user_api_key_dict: UserAPIKeyAuth,
            response: str,
    ):
        pass

    async def async_post_call_streaming_iterator_hook(
            self,
            user_api_key_dict: UserAPIKeyAuth,
            response: Any,
            request_data: dict,
    ) -> AsyncGenerator[ModelResponseStream, None]:
        """
        Passes the entire stream to the guardrail

        This is useful for plugins that need to see the entire stream.
        """
        async for item in response:
            yield item

# exported instance for litellm_settings.callbacks
proxy_handler_instance = InjectToolsCallback()
