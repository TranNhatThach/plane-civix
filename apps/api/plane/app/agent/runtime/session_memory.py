# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
from typing import List, Dict, Any, Optional


class SessionMemory:
    """
    Intelligent Multi-Turn Session Memory with Dynamic Sliding Window & Compaction.
    Prevents context overflow while preserving essential project entities and user intentions.
    """

    def __init__(
        self,
        system_prompt: str,
        session_id: str = "",
        max_active_messages: int = 12,
    ):
        self.system_prompt = system_prompt
        self.session_id = session_id
        self.max_active_messages = max_active_messages
        self.messages: List[Dict[str, Any]] = []
        self.working_summary: str = ""

    def add_user_message(self, content: str, active_context_info: Optional[List[str]] = None):
        prefix = ""
        if active_context_info:
            prefix = "Context màn hình hiện tại:\n" + "\n".join(active_context_info) + "\n\n"
        self.messages.append({"role": "user", "content": f"{prefix}{content}".strip()})

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ):
        msg: Dict[str, Any] = {"role": "assistant", "content": content or ""}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)

    def add_tool_result(self, tool_call_id: str, tool_name: str, result: Any):
        payload_str = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
        # Guard against overly large tool outputs (Spilling threshold ~4KB)
        if len(payload_str) > 4000:
            payload_str = (
                payload_str[:3800]
                + f"\n... [Dữ liệu quá dài đã được tóm lược, hiển thị 3800/{len(payload_str)} ký tự]"
            )
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": payload_str,
            }
        )

    def build_llm_messages(self) -> List[Dict[str, Any]]:
        """Assembles prompt list including System Instructions, Working Summary, and Active Window."""
        prompt_list: List[Dict[str, Any]] = []

        # 1. System Prompt + Working Summary
        effective_system = self.system_prompt
        if self.working_summary:
            effective_system += (
                f"\n\n[TÓM TẮT NGỮ CẢNH CÁC LƯỢT TRƯỚC ĐÓ]:\n{self.working_summary}"
            )
        prompt_list.append({"role": "system", "content": effective_system})

        # 2. Active Messages Window
        if len(self.messages) > self.max_active_messages:
            # Compact the older messages into working summary
            older = self.messages[: -self.max_active_messages]
            recent = self.messages[-self.max_active_messages :]
            self._compact_older_messages(older)
            prompt_list.extend(recent)
        else:
            prompt_list.extend(self.messages)

        return prompt_list

    def _compact_older_messages(self, older_messages: List[Dict[str, Any]]):
        """Extracts key points from older messages to keep memory compact."""
        summarized_points = []
        for msg in older_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user" and content:
                summarized_points.append(f"• User yêu cầu: {content[:100]}")
            elif role == "assistant" and content:
                summarized_points.append(f"• AI đã trả lời/xử lý: {content[:100]}")
        if summarized_points:
            self.working_summary = "\n".join(summarized_points[-6:])
