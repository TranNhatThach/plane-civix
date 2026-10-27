# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
from typing import Dict, Any, Optional


class EventStream:
    """
    Standard Server-Sent Events (SSE) Formatter for Civix Autonomous Runtime (CAR-v2).
    Generates structured SSE data frames without artificial delays or blocking.
    """

    @staticmethod
    def _format(event_name: str, data: Dict[str, Any]) -> str:
        payload = {"event": event_name, **data}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    @classmethod
    def step_start(cls, turn_id: str, step: int, max_steps: int = 8) -> str:
        return cls._format(
            "run.step.start",
            {"turn_id": str(turn_id), "step": step, "max_steps": max_steps},
        )

    @classmethod
    def thinking_delta(cls, delta: str, turn_id: Optional[str] = None) -> str:
        return cls._format(
            "model.thinking",
            {"delta": delta, "turn_id": str(turn_id) if turn_id else None},
        )

    @classmethod
    def content_delta(cls, delta: str, turn_id: Optional[str] = None) -> str:
        return cls._format(
            "model.content.delta",
            {"delta": delta, "turn_id": str(turn_id) if turn_id else None},
        )

    @classmethod
    def tool_start(
        cls,
        tool_call_id: str,
        tool_name: str,
        args: Dict[str, Any],
        turn_id: Optional[str] = None,
    ) -> str:
        return cls._format(
            "tool.call.start",
            {
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "args": args,
                "turn_id": str(turn_id) if turn_id else None,
            },
        )

    @classmethod
    def tool_result(
        cls,
        tool_call_id: str,
        tool_name: str,
        status: str,
        result: Any,
        duration_ms: int = 0,
        turn_id: Optional[str] = None,
    ) -> str:
        return cls._format(
            "tool.call.result",
            {
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "status": status,
                "result": result,
                "duration_ms": duration_ms,
                "turn_id": str(turn_id) if turn_id else None,
            },
        )

    @classmethod
    def approval_required(
        cls,
        approval_id: str,
        action: str,
        title: str,
        details: str,
        pending_payload: Dict[str, Any],
        turn_id: Optional[str] = None,
    ) -> str:
        return cls._format(
            "approval.required",
            {
                "approval_id": approval_id,
                "action": action,
                "title": title,
                "details": details,
                "pending_payload": pending_payload,
                "turn_id": str(turn_id) if turn_id else None,
            },
        )

    @classmethod
    def run_completed(
        cls,
        turn_id: str,
        usage: Dict[str, Any],
        card_type: Optional[str] = None,
        card_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        return cls._format(
            "run.completed",
            {
                "turn_id": str(turn_id),
                "done": True,
                "usage": usage,
                "card_type": card_type,
                "card_data": card_data or {},
            },
        )

    @classmethod
    def run_error(
        cls,
        code: str,
        message: str,
        turn_id: Optional[str] = None,
    ) -> str:
        return cls._format(
            "run.error",
            {
                "code": code,
                "message": message,
                "turn_id": str(turn_id) if turn_id else None,
            },
        )
