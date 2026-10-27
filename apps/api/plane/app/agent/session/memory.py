# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
from typing import List, Dict, Any, Optional
from plane.app.agent.session.spilling import SpillingEngine

logger = logging.getLogger(__name__)


class SessionMemory:
    """
    Multi-Turn Conversation Memory with Dynamic Sliding Window,
    Context Compaction, and Integrated Spilling.
    """

    def __init__(
        self,
        system_prompt: str,
        session_id: str = "",
        max_active_messages: int = 12,
        spilling_engine: Optional[SpillingEngine] = None,
    ):
        self.system_prompt = system_prompt
        self.session_id = session_id
        self.max_active_messages = max_active_messages
        self.spilling_engine = spilling_engine or SpillingEngine()
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
        payload_str, citation = self.spilling_engine.process_output(tool_name, result)
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": payload_str,
            }
        )

    def compact_history(self):
        """
        Compacts older conversation turns when total messages exceed threshold.
        Extracts key entities into a working summary.
        """
        if len(self.messages) <= self.max_active_messages:
            return

        overflow_count = len(self.messages) - self.max_active_messages
        older_messages = self.messages[:overflow_count]
        self.messages = self.messages[overflow_count:]

        # Extract brief points into working summary
        summaries = []
        for m in older_messages:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            if role == "user":
                summaries.append(f"User: {content[:80]}")
            elif role == "assistant" and content:
                summaries.append(f"AI: {content[:80]}")
            elif role == "tool":
                summaries.append(f"Tool {m.get('name')}: Đã xử lý")

        if summaries:
            summary_addition = " | ".join(summaries)
            if self.working_summary:
                self.working_summary += " || " + summary_addition
            else:
                self.working_summary = summary_addition

            # Keep summary bounded
            if len(self.working_summary) > 2000:
                self.working_summary = self.working_summary[-1800:]

    def build_llm_messages(self) -> List[Dict[str, Any]]:
        """Constructs final payload for LLM completion."""
        self.compact_history()

        effective_system_prompt = self.system_prompt
        if self.working_summary:
            effective_system_prompt += (
                f"\n\n[TÓM TẮT NGỮ CẢNH CÁC LƯỢT TRƯỚC]:\n{self.working_summary}"
            )

        return [{"role": "system", "content": effective_system_prompt}] + self.messages
