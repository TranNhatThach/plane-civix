# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import time
import uuid
import json
import logging
from typing import Generator, Dict, Any, List, Optional, Callable

from plane.app.agent.runtime.event_stream import EventStream
from plane.app.agent.runtime.quota_guard import QuotaGuard
from plane.app.agent.runtime.session_memory import SessionMemory

logger = logging.getLogger(__name__)


class AgentLoopDriver:
    """
    Core Autonomous ReAct Loop Driver (CAR-v2 Engine).
    Executes multi-step reasoning, native token-by-token streaming,
    tool execution pipelines, and commercial token metering.
    """

    MAX_STEPS = 8
    LOOP_TIMEOUT_SECONDS = 60

    DESTRUCTIVE_TOOLS = {
        "tool_rebalance_workload",
        "tool_batch_update_tasks",
        "tool_delete_task",
    }

    def __init__(
        self,
        memory: SessionMemory,
        tools_schema: List[Dict[str, Any]],
        tool_executor: Callable[[str, Dict[str, Any]], Any],
        llm_stream_fn: Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Generator[Any, None, None]],
        quota_guard: Optional[QuotaGuard] = None,
        model_name: str = "gpt-4o-mini",
        turn_id: Optional[str] = None,
    ):
        self.memory = memory
        self.tools_schema = tools_schema
        self.tool_executor = tool_executor
        self.llm_stream_fn = llm_stream_fn
        self.quota_guard = quota_guard or QuotaGuard()
        self.model_name = model_name
        self.turn_id = turn_id or str(uuid.uuid4())

    def run_turn_stream(self, user_prompt: str) -> Generator[str, None, None]:
        """
        Main generator yielding Server-Sent Events (SSE) in real-time.
        Executes ReAct loops with zero blocking delays.
        """
        start_time = time.time()
        turn_id = self.turn_id

        # 1. Quota Pre-check
        can_proceed, quota_err = self.quota_guard.check_quota(estimated_prompt_tokens=500)
        if not can_proceed:
            yield EventStream.run_error("QUOTA_EXCEEDED", quota_err, turn_id=turn_id)
            return

        # 2. Append User Message into Session Memory
        self.memory.add_user_message(user_prompt)

        step = 1
        total_prompt_tokens = 0
        total_completion_tokens = 0
        executed_tool_calls_count = 0
        last_card_type = None
        last_card_data = None

        while step <= self.MAX_STEPS:
            # Check hygiene timeout
            if time.time() - start_time > self.LOOP_TIMEOUT_SECONDS:
                yield EventStream.run_error("TIMEOUT", "Lượt thực thi vượt quá 60s, hệ thống tự động dừng để bảo vệ tài nguyên.", turn_id=turn_id)
                break

            yield EventStream.step_start(turn_id, step=step, max_steps=self.MAX_STEPS)

            llm_messages = self.memory.build_llm_messages()
            # Estimate prompt tokens for this step
            step_prompt_chars = sum(len(str(m.get("content", ""))) for m in llm_messages)
            total_prompt_tokens += QuotaGuard.estimate_tokens_from_text(" " * step_prompt_chars)

            step_content_buffer: List[str] = []
            tool_calls_buffer: Dict[int, Dict[str, Any]] = {}
            has_tool_call = False

            try:
                stream_generator = self.llm_stream_fn(llm_messages, self.tools_schema)

                for chunk in stream_generator:
                    # A. Thinking/Reasoning delta (DeepSeek-R1, Thinking models)
                    thinking_delta = getattr(chunk, "thinking_delta", None)
                    if not thinking_delta and isinstance(chunk, dict):
                        thinking_delta = chunk.get("thinking_delta")
                    if thinking_delta:
                        yield EventStream.thinking_delta(thinking_delta, turn_id=turn_id)

                    # B. Content delta (Normal response text)
                    content_delta = getattr(chunk, "content_delta", None)
                    if not content_delta and isinstance(chunk, dict):
                        content_delta = chunk.get("content_delta")
                    if content_delta:
                        step_content_buffer.append(content_delta)
                        total_completion_tokens += QuotaGuard.estimate_tokens_from_text(content_delta)
                        yield EventStream.content_delta(content_delta, turn_id=turn_id)

                    # C. Tool call chunks
                    tool_deltas = getattr(chunk, "tool_call_deltas", None)
                    if not tool_deltas and isinstance(chunk, dict):
                        tool_deltas = chunk.get("tool_call_deltas")
                    if tool_deltas:
                        has_tool_call = True
                        for td in tool_deltas:
                            idx = td.get("index", 0)
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {
                                    "id": td.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                                    "name": td.get("name", ""),
                                    "arguments": "",
                                }
                            if td.get("name"):
                                tool_calls_buffer[idx]["name"] = td.get("name")
                            if td.get("arguments"):
                                tool_calls_buffer[idx]["arguments"] += td.get("arguments")

            except Exception as e:
                logger.exception(f"Error during LLM stream in step {step}: {e}")
                yield EventStream.run_error("LLM_ERROR", f"Lỗi kết nối mô hình AI: {str(e)}", turn_id=turn_id)
                return

            full_step_content = "".join(step_content_buffer)

            # If no tools were called, this step produced the final answer
            if not has_tool_call:
                self.memory.add_assistant_message(full_step_content)
                break

            # Process requested tool calls
            parsed_tool_calls_for_memory = []
            for tc_info in tool_calls_buffer.values():
                tc_id = tc_info["id"]
                tc_name = tc_info["name"]
                raw_args = tc_info["arguments"]
                
                try:
                    parsed_args = json.loads(raw_args) if raw_args.strip() else {}
                except Exception:
                    parsed_args = {}

                parsed_tool_calls_for_memory.append({
                    "id": tc_id,
                    "type": "function",
                    "function": {"name": tc_name, "arguments": json.dumps(parsed_args, ensure_ascii=False)},
                })

            self.memory.add_assistant_message(full_step_content, tool_calls=parsed_tool_calls_for_memory)

            # Execute each tool
            for tc_item in parsed_tool_calls_for_memory:
                tc_id = tc_item["id"]
                tc_name = tc_item["function"]["name"]
                args = json.loads(tc_item["function"]["arguments"])
                executed_tool_calls_count += 1

                # Check Human-in-the-loop (HITL) approval
                if tc_name in self.DESTRUCTIVE_TOOLS:
                    approval_id = f"appr_{uuid.uuid4().hex[:8]}"
                    yield EventStream.approval_required(
                        approval_id=approval_id,
                        action=tc_name,
                        title="Yêu cầu phê duyệt hành động hệ thống",
                        details=f"Agent đề xuất thực hiện: {tc_name}",
                        pending_payload=args,
                        turn_id=turn_id,
                    )
                    # Pause loop execution pending user confirmation
                    return

                # Normal tool execution
                tool_start_t = time.time()
                yield EventStream.tool_start(tc_id, tc_name, args, turn_id=turn_id)

                try:
                    tool_output = self.tool_executor(tc_name, args)
                    tool_duration_ms = int((time.time() - tool_start_t) * 1000)
                    yield EventStream.tool_result(tc_id, tc_name, "success", tool_output, duration_ms=tool_duration_ms, turn_id=turn_id)
                    self.memory.add_tool_result(tc_id, tc_name, tool_output)

                    # Extract card presentation metadata if available
                    if isinstance(tool_output, dict):
                        if tc_name == "tool_query_tasks":
                            last_card_type = "task_list"
                            last_card_data = tool_output
                        elif tc_name in ["tool_get_progress", "tool_get_workspace_summary"]:
                            last_card_type = "progress_metrics"
                            last_card_data = tool_output
                        elif tc_name == "tool_get_changelog":
                            last_card_type = "changelog_card"
                            last_card_data = tool_output

                except Exception as tool_err:
                    tool_duration_ms = int((time.time() - tool_start_t) * 1000)
                    err_msg = str(tool_err)
                    yield EventStream.tool_result(tc_id, tc_name, "error", {"error": err_msg}, duration_ms=tool_duration_ms, turn_id=turn_id)
                    self.memory.add_tool_result(tc_id, tc_name, {"error": err_msg})

            step += 1

        # 3. Finalize Turn & Token Metrics
        total_tokens = total_prompt_tokens + total_completion_tokens
        duration_ms = int((time.time() - start_time) * 1000)
        cost_usd = QuotaGuard.calculate_cost(self.model_name, total_prompt_tokens, total_completion_tokens)

        # Update quota usage in memory/guard
        self.quota_guard.current_used += total_tokens

        usage_summary = {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": float(cost_usd),
            "duration_ms": duration_ms,
            "tool_calls_count": executed_tool_calls_count,
            "steps": min(step, self.MAX_STEPS),
            "model": self.model_name,
        }

        yield EventStream.run_completed(
            turn_id=turn_id,
            usage=usage_summary,
            card_type=last_card_type,
            card_data=last_card_data,
        )
