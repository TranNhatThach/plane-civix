import logging
import json
from typing import Optional, Dict, Any, Tuple
from openai import OpenAI
from plane.app.views.external.base import get_llm_config, sanitize_base_url
from plane.app.agent.registry import ToolRegistry
from plane.app.agent.core.prompts import PLANE_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class SystemLLMClient:
    """
    Unified client for executing System-configured LLMs (OpenRouter, OpenAI, DeepSeek, Gemini, Groq, Ollama)
    with OpenAI-compatible Function / Tool Calling schemas.
    """

    def __init__(self):
        self.api_key, self.model, self.provider, self.base_url = get_llm_config()

    def generate_completion(
        self,
        user_prompt: str,
        context_prompt: str,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Invokes system LLM with registered tools schemas.
        Returns Tuple: (text_content, tool_call_info_dict)
        """
        eff_model = self.model or "gpt-4o-mini"
        eff_provider = (self.provider or "openai").lower()
        eff_api_key = self.api_key or "sk-dummy-key"

        # Resolve effective base_url
        eff_base_url = sanitize_base_url(self.base_url)
        if not eff_base_url:
            if eff_provider == "openrouter":
                eff_base_url = "https://openrouter.ai/api/v1"
            elif eff_provider == "deepseek":
                eff_base_url = "https://api.deepseek.com/v1"
            elif eff_provider == "groq":
                eff_base_url = "https://api.groq.com/openai/v1"
            elif eff_provider == "civix":
                eff_base_url = "https://api.civix.com.vn/api"

        client_kwargs = {
            "api_key": eff_api_key,
            "default_headers": {"User-Agent": "Plane-AI/1.0"},
        }
        if eff_base_url:
            client_kwargs["base_url"] = eff_base_url

        client = OpenAI(**client_kwargs)

        messages = [
            {"role": "system", "content": PLANE_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": context_prompt},
        ]

        tools_schema = ToolRegistry.get_openai_schemas()

        try:
            response = client.chat.completions.create(
                model=eff_model,
                messages=messages,
                tools=tools_schema,
                temperature=0.2,
            )
        except Exception as call_err:
            logger.warning(f"LLM tool calling failed, falling back to plain chat: {call_err}")
            response = client.chat.completions.create(
                model=eff_model,
                messages=messages,
                temperature=0.2,
            )

        choice = response.choices[0]
        message = choice.message

        if getattr(message, "tool_calls", None) and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments or "{}")
            except Exception:
                func_args = {}

            return None, {
                "name": func_name,
                "args": func_args,
            }

        return message.content or "", None
