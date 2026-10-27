# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import time
import uuid
import json
import logging
from typing import Generator, Dict, Any, List, Optional, Callable

from plane.app.agent.kernel.events import KernelEvents
from plane.app.agent.session.events import SessionEvent, EventTypes
from plane.app.agent.session.event_log import BaseEventLog, InMemoryEventLog
from plane.app.agent.session.memory import SessionMemory
from plane.app.agent.seams.llm.base import BaseLLMProvider
from plane.app.agent.seams.approval.base import BaseApprovalProvider
from plane.app.agent.seams.approval.policy import StandardApprovalProvider
from plane.app.agent.loop.event_stream import EventStream
from plane.app.agent.loop.quota_guard import QuotaGuard

logger = logging.getLogger(__name__)


class AgentLoopDriver:
    """
    Core Autonomous ReAct Loop Driver (CAR-v3 Engine).
    Implements multi-step reasoning, native token streaming,
    waterfall lifecycle hooks, human-in-the-loop approval, and event-sourced logging.
    """

    MAX_STEPS = 8
    LOOP_TIMEOUT_SECONDS = 60

    def __init__(
        self,
        memory: SessionMemory,
        tools_schema: List[Dict[str, Any]],
        tool_executor: Callable[[str, Dict[str, Any]], Any],
        llm_provider: Optional[BaseLLMProvider] = None,
        llm_stream_fn: Optional[Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Generator[Any, None, None]]] = None,
        events: Optional[KernelEvents] = None,
        event_log: Optional[BaseEventLog] = None,
        approval_provider: Optional[BaseApprovalProvider] = None,
        quota_guard: Optional[QuotaGuard] = None,
        model_name: str = "gpt-4o-mini",
        turn_id: Optional[str] = None,
    ):
        self.memory = memory
        self.tools_schema = tools_schema
        self.tool_executor = tool_executor
        self.llm_provider = llm_provider
        self.llm_stream_fn = llm_stream_fn
        self.events = events or KernelEvents()
        self.event_log = event_log or InMemoryEventLog()
        self.approval_provider = approval_provider or StandardApprovalProvider()
        self.quota_guard = quota_guard or QuotaGuard()
        self.model_name = model_name
        self.turn_id = turn_id or str(uuid.uuid4())

    def _get_stream_generator(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]):
        if self.llm_stream_fn:
            return self.llm_stream_fn(messages, tools)
        if self.llm_provider:
            return self.llm_provider.generate_stream(messages, tools)
        raise RuntimeError("No LLM provider or stream function configured for AgentLoopDriver")

    def run_turn_stream(self, user_prompt: str) -> Generator[str, None, None]:
        """
        Executes an autonomous ReAct turn, yielding Server-Sent Events in real-time.
        """
        start_time = time.time()
        turn_id = self.turn_id

        # 1. Quota Pre-check
        can_proceed, quota_err = self.quota_guard.check_quota(estimated_prompt_tokens=500)
        if not can_proceed:
            self.event_log.append(SessionEvent(type=EventTypes.RUN_ERROR, payload={"code": "QUOTA_EXCEEDED", "msg": quota_err}, turn_id=turn_id))
            yield EventStream.run_error("QUOTA_EXCEEDED", quota_err, turn_id=turn_id)
            return

        # 2. Append User Message
        self.memory.add_user_message(user_prompt)
        self.event_log.append(SessionEvent(type=EventTypes.TURN_START, payload={"user_prompt": user_prompt}, turn_id=turn_id))
        self.event_log.append(SessionEvent(type=EventTypes.USER_MESSAGE, payload={"content": user_prompt}, turn_id=turn_id))

        step = 1
        total_prompt_tokens = 0
        total_completion_tokens = 0
        executed_tool_calls_count = 0
        last_card_type = None
        last_card_data = None

        while step <= self.MAX_STEPS:
            # Check timeout
            if time.time() - start_time > self.LOOP_TIMEOUT_SECONDS:
                msg = "Lượt thực thi vượt quá 60s, hệ thống tự động dừng để bảo vệ tài nguyên."
                self.event_log.append(SessionEvent(type=EventTypes.RUN_ERROR, payload={"code": "TIMEOUT", "msg": msg}, turn_id=turn_id))
                yield EventStream.run_error("TIMEOUT", msg, turn_id=turn_id)
                break

            # Lifecycle: agent/pre-step
            pre_step_payload = self.events.execute_waterfall("agent/pre-step", {"step": step, "user_prompt": user_prompt})
            if pre_step_payload.get("abort"):
                break

            self.event_log.append(SessionEvent(type=EventTypes.STEP_START, payload={"step": step}, turn_id=turn_id, step=step))
            yield EventStream.step_start(turn_id=turn_id, step=step, max_steps=self.MAX_STEPS)

            llm_messages = self.memory.build_llm_messages()
            step_prompt_tokens = sum(len(str(m.get("content", ""))) // 4 for m in llm_messages)
            total_prompt_tokens += step_prompt_tokens

            accumulated_content = []
            tool_calls_buffer: Dict[int, Dict[str, Any]] = {}

            # Execute streaming LLM
            try:
                stream_gen = self._get_stream_generator(llm_messages, self.tools_schema)
                for chunk in stream_gen:
                    # Thinking delta
                    if chunk.get("thinking_delta"):
                        td = chunk["thinking_delta"]
                        self.event_log.append(SessionEvent(type=EventTypes.ASSISTANT_CHUNK, payload={"thinking": td}, turn_id=turn_id, step=step))
                        yield EventStream.thinking_delta(td, turn_id=turn_id)

                    # Content delta
                    if chunk.get("content_delta"):
                        cd = chunk["content_delta"]
                        accumulated_content.append(cd)
                        total_completion_tokens += max(1, len(cd) // 4)
                        self.event_log.append(SessionEvent(type=EventTypes.ASSISTANT_CHUNK, payload={"delta": cd}, turn_id=turn_id, step=step))
                        yield EventStream.content_delta(cd, turn_id=turn_id)

                    # Tool call deltas
                    if chunk.get("tool_call_deltas"):
                        for tcd in chunk["tool_call_deltas"]:
                            idx = tcd.get("index", 0)
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {
                                    "id": tcd.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                                    "name": tcd.get("name") or "",
                                    "args_str": "",
                                }
                            if tcd.get("name"):
                                tool_calls_buffer[idx]["name"] = tcd["name"]
                            if tcd.get("arguments_delta"):
                                tool_calls_buffer[idx]["args_str"] += tcd["arguments_delta"]
            except Exception as stream_err:
                logger.exception(f"Error during LLM stream: {stream_err}")
                self.event_log.append(SessionEvent(type=EventTypes.RUN_ERROR, payload={"code": "STREAM_ERROR", "msg": str(stream_err)}, turn_id=turn_id))
                yield EventStream.run_error("STREAM_ERROR", f"Lỗi streaming từ LLM: {stream_err}", turn_id=turn_id)
                break

            # If tool calls were initiated
            if tool_calls_buffer:
                formatted_tool_calls = []
                for _, tc in sorted(tool_calls_buffer.items()):
                    args_parsed = {}
                    if tc["args_str"]:
                        try:
                            args_parsed = json.loads(tc["args_str"])
                        except Exception:
                            args_parsed = {"raw": tc["args_str"]}
                    formatted_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["args_str"] if isinstance(tc["args_str"], str) else json.dumps(tc["args_str"]),
                        },
                        "name": tc["name"],
                        "args": args_parsed,
                        "arguments_str": tc["args_str"],
                    })

                self.memory.add_assistant_message(content="".join(accumulated_content), tool_calls=formatted_tool_calls)

                for tc in formatted_tool_calls:
                    executed_tool_calls_count += 1
                    t_name = tc["name"]
                    t_args = tc["args"]
                    t_id = tc["id"]

                    # Log tool/call
                    self.event_log.append(SessionEvent(type=EventTypes.TOOL_CALL, payload=tc, turn_id=turn_id, step=step))

                    # Lifecycle: tools/pre-execute
                    pre_tool = self.events.execute_waterfall("tools/pre-execute", {"name": t_name, "args": t_args})
                    t_name = pre_tool.get("name", t_name)
                    t_args = pre_tool.get("args", t_args)

                    # HITL Approval check
                    is_approved, reason = self.approval_provider.request_approval(t_name, t_args)
                    if not is_approved:
                        denied_msg = f"Yêu cầu phê duyệt hành động: {reason}"
                        self.memory.add_tool_result(t_id, t_name, {"status": "requires_approval", "message": denied_msg})
                        yield EventStream.tool_start(t_id, t_name, t_args, turn_id=turn_id)
                        yield EventStream.tool_result(t_id, t_name, {"status": "requires_approval", "message": denied_msg}, duration_ms=0, turn_id=turn_id)
                        continue

                    yield EventStream.tool_start(t_id, t_name, t_args, turn_id=turn_id)

                    t_start = time.time()
                    try:
                        raw_result = self.tool_executor(t_name, t_args)
                        duration_ms = int((time.time() - t_start) * 1000)

                        # Lifecycle: tools/post-execute
                        post_tool = self.events.execute_waterfall("tools/post-execute", {"name": t_name, "result": raw_result})
                        processed_result = post_tool.get("result", raw_result)

                        self.memory.add_tool_result(t_id, t_name, processed_result)
                        self.event_log.append(SessionEvent(type=EventTypes.TOOL_RESULT, payload={"tool_call_id": t_id, "name": t_name, "result": processed_result}, turn_id=turn_id, step=step))
                        yield EventStream.tool_result(t_id, t_name, processed_result, duration_ms=duration_ms, turn_id=turn_id)

                        # Check structured card preview
                        if isinstance(processed_result, dict) and processed_result.get("tasks"):
                            last_card_type = "task_list"
                            last_card_data = processed_result
                            yield EventStream.ui_card("task_list", processed_result, turn_id=turn_id)
                        elif isinstance(processed_result, dict) and "completion_percentage" in processed_result:
                            last_card_type = "progress_summary"
                            last_card_data = processed_result
                            yield EventStream.ui_card("progress_summary", processed_result, turn_id=turn_id)

                    except Exception as tool_err:
                        duration_ms = int((time.time() - t_start) * 1000)
                        err_payload = {"error": str(tool_err)}
                        self.memory.add_tool_result(t_id, t_name, err_payload)
                        self.event_log.append(SessionEvent(type=EventTypes.TOOL_RESULT, payload={"tool_call_id": t_id, "name": t_name, "result": err_payload}, turn_id=turn_id, step=step))
                        yield EventStream.tool_result(t_id, t_name, err_payload, duration_ms=duration_ms, turn_id=turn_id)

                self.event_log.append(SessionEvent(type=EventTypes.STEP_END, payload={"step": step}, turn_id=turn_id, step=step))
                step += 1
                continue
            else:
                # Normal text completion reached
                self.memory.add_assistant_message(content="".join(accumulated_content))
                self.event_log.append(SessionEvent(type=EventTypes.ASSISTANT_MESSAGE, payload={"content": "".join(accumulated_content)}, turn_id=turn_id, step=step))
                self.event_log.append(SessionEvent(type=EventTypes.STEP_END, payload={"step": step}, turn_id=turn_id, step=step))
                break

        # Lifecycle: agent/turn-stopping
        self.events.execute_waterfall("agent/turn-stopping", {"turn_id": turn_id, "total_steps": step})

        total_duration_ms = int((time.time() - start_time) * 1000)
        cost_usd = self.quota_guard.calculate_cost(self.model_name, total_prompt_tokens, total_completion_tokens)
        self.quota_guard.record_usage(total_prompt_tokens, total_completion_tokens)

        usage = {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "cost_usd": float(cost_usd),
            "duration_ms": total_duration_ms,
            "tool_calls_count": executed_tool_calls_count,
            "card_type": last_card_type,
            "card_data": last_card_data,
        }

        self.event_log.append(SessionEvent(type=EventTypes.RUN_COMPLETED, payload=usage, turn_id=turn_id))
        self.event_log.append(SessionEvent(type=EventTypes.TURN_END, payload={"turn_id": turn_id}, turn_id=turn_id))
        yield EventStream.run_completed(turn_id=turn_id, total_steps=step, usage=usage)
