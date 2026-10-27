# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, Generator


class BaseLLMProvider(ABC):
    """
    Abstract Service Definition for LLM Providers.
    Decouples the Agent Loop and tools from vendor-specific SDK implementations.
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Synchronous single-turn completion.
        Returns Tuple: (text_content, list_of_tool_calls)
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Token-by-token streaming generator.
        Yields chunk dicts: {"content_delta": ...}, {"thinking_delta": ...}, {"tool_call_deltas": ...}
        """
        pass
