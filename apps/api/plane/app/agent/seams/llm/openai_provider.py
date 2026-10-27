# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
import logging
from typing import List, Dict, Any, Tuple, Optional, Generator
from openai import OpenAI

from plane.app.agent.seams.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI-compatible LLM Provider implementation.
    Supports OpenRouter, DeepSeek, Gemini, OpenAI, Groq, and local Ollama.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        timeout: float = 45.0,
    ):
        self.api_key = api_key or "sk-dummy-key"
        self.model = model or "gpt-4o-mini"
        self.base_url = base_url
        self.timeout = timeout
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools_schema:
            kwargs["tools"] = tools_schema
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        tool_calls_list = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args_dict = json.loads(tc.function.arguments)
                except Exception:
                    args_dict = {"raw": tc.function.arguments}
                tool_calls_list.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": args_dict,
                })

        return msg.content, tool_calls_list or None

    def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Generator[Dict[str, Any], None, None]:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if tools_schema:
            kwargs["tools"] = tools_schema
            kwargs["tool_choice"] = "auto"

        stream_resp = self.client.chat.completions.create(**kwargs)
        for chunk in stream_resp:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Model content delta
            if getattr(delta, "content", None):
                yield {"content_delta": delta.content}

            # Model reasoning / thinking delta (DeepSeek R1 / OpenRouter / Nemotron / o1 / Gemini)
            reasoning = (
                getattr(delta, "reasoning", None)
                or getattr(delta, "reasoning_content", None)
                or getattr(delta, "thinking", None)
            )
            if reasoning:
                yield {"thinking_delta": reasoning}

            # Tool call deltas
            if getattr(delta, "tool_calls", None):
                deltas = []
                for tc in delta.tool_calls:
                    deltas.append({
                        "index": tc.index,
                        "id": getattr(tc, "id", None),
                        "name": getattr(tc.function, "name", None) if getattr(tc, "function", None) else None,
                        "arguments_delta": getattr(tc.function, "arguments", None) if getattr(tc, "function", None) else None,
                    })
                yield {"tool_call_deltas": deltas}
