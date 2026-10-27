# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from typing import List, Dict, Any
from plane.app.agent.session.events import SessionEvent, EventTypes


def derive_messages(events: List[SessionEvent]) -> List[Dict[str, Any]]:
    """
    Pure Projection Function:
    Transforms an Append-Only SessionEvent[] stream into standard OpenAI-compatible
    ChatMessage[] history for the LLM.
    
    Guarantees:
    1. Recombines streaming chunks into full assistant messages.
    2. Pairs tool_calls with subsequent tool_results using tool_call_id.
    3. Maintains strict conversation flow order: system -> user -> assistant -> tool.
    """
    messages: List[Dict[str, Any]] = []
    current_assistant_chunks: List[str] = []
    current_tool_calls: List[Dict[str, Any]] = []

    def flush_assistant():
        nonlocal current_assistant_chunks, current_tool_calls
        if current_assistant_chunks or current_tool_calls:
            msg: Dict[str, Any] = {
                "role": "assistant",
                "content": "".join(current_assistant_chunks).strip(),
            }
            if current_tool_calls:
                msg["tool_calls"] = list(current_tool_calls)
            messages.append(msg)
            current_assistant_chunks = []
            current_tool_calls = []

    for event in events:
        etype = event.type
        p = event.payload

        if etype == EventTypes.USER_MESSAGE:
            flush_assistant()
            messages.append({
                "role": "user",
                "content": p.get("content", ""),
            })

        elif etype == EventTypes.ASSISTANT_CHUNK:
            delta = p.get("delta", "")
            if delta:
                current_assistant_chunks.append(delta)

        elif etype == EventTypes.ASSISTANT_MESSAGE:
            flush_assistant()
            msg: Dict[str, Any] = {
                "role": "assistant",
                "content": p.get("content", "") or "",
            }
            if "tool_calls" in p and p["tool_calls"]:
                msg["tool_calls"] = p["tool_calls"]
            messages.append(msg)

        elif etype == EventTypes.TOOL_CALL:
            # Tool call requested by assistant in this turn
            tool_call = {
                "id": p.get("tool_call_id") or p.get("id"),
                "type": "function",
                "function": {
                    "name": p.get("name"),
                    "arguments": p.get("arguments_str") or (
                        p.get("args") if isinstance(p.get("args"), str) else None
                    ),
                },
            }
            current_tool_calls.append(tool_call)

        elif etype == EventTypes.TOOL_RESULT:
            flush_assistant()
            messages.append({
                "role": "tool",
                "tool_call_id": p.get("tool_call_id") or p.get("id"),
                "name": p.get("name", ""),
                "content": str(p.get("result", "")),
            })

    flush_assistant()
    return messages
