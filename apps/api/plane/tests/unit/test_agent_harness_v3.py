# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest
from plane.app.agent.kernel import KernelContext, KernelEvents
from plane.app.agent.session import (
    SessionEvent,
    EventTypes,
    InMemoryEventLog,
    derive_messages,
    SpillingEngine,
    SessionMemory,
)
from plane.app.agent.seams.approval import StandardApprovalProvider, ApprovalPolicy
from plane.app.agent.loop import AgentLoopDriver, FastPathMatcher, EventStream


@pytest.mark.unit
def test_kernel_context_and_disposers():
    ctx = KernelContext()
    disposed = []

    unbind = ctx.provide("test_service", {"name": "mock_service"}, disposer=lambda: disposed.append(True))
    assert ctx.has("test_service") is True
    assert ctx.get("test_service")["name"] == "mock_service"

    # Child context inherits
    child_ctx = ctx.create_subcontext()
    assert child_ctx.has("test_service") is True

    # Unbind cleans up
    unbind()
    assert ctx.has("test_service") is False
    assert len(disposed) == 1


@pytest.mark.unit
def test_kernel_events_waterfall_pipeline():
    events = KernelEvents()

    # Interceptor 1: Uppercase input
    def step1(payload, next_fn):
        payload["text"] = payload["text"].upper()
        return next_fn(payload)

    # Interceptor 2: Append suffix
    def step2(payload, next_fn):
        payload["text"] += " [PROCESSED]"
        return next_fn(payload)

    events.use_waterfall("test/pipeline", step1)
    events.use_waterfall("test/pipeline", step2)

    result = events.execute_waterfall("test/pipeline", {"text": "hello civix"})
    assert result["text"] == "HELLO CIVIX [PROCESSED]"


@pytest.mark.unit
def test_event_sourcing_projection_and_forking():
    log = InMemoryEventLog(session_id="session_01")
    log.append(SessionEvent(type=EventTypes.USER_MESSAGE, payload={"content": "Kiểm tra tiến độ"}))
    log.append(SessionEvent(type=EventTypes.ASSISTANT_CHUNK, payload={"delta": "Đang "}))
    log.append(SessionEvent(type=EventTypes.ASSISTANT_CHUNK, payload={"delta": "xử lý..."}))
    log.append(SessionEvent(type=EventTypes.TOOL_CALL, payload={"tool_call_id": "c1", "name": "tool_get_progress", "arguments_str": "{}"}))
    log.append(SessionEvent(type=EventTypes.TOOL_RESULT, payload={"tool_call_id": "c1", "name": "tool_get_progress", "result": '{"completion_percentage": 75}'}))

    events = log.get_events()
    messages = derive_messages(events)

    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Kiểm tra tiến độ"

    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Đang xử lý..."
    assert len(messages[1]["tool_calls"]) == 1
    assert messages[1]["tool_calls"][0]["function"]["name"] == "tool_get_progress"

    assert messages[2]["role"] == "tool"
    assert messages[2]["tool_call_id"] == "c1"

    # Test Session Forking
    forked = log.fork(up_to_index=2, new_session_id="session_02")
    assert len(forked.get_events()) == 2
    assert forked.get_events()[0].session_id == "session_02"


@pytest.mark.unit
def test_spilling_engine_threshold():
    engine = SpillingEngine(threshold=100)
    small_text = "Dữ liệu ngắn"
    preview1, cit1 = engine.process_output("test_tool", small_text)
    assert cit1 is None
    assert preview1 == small_text

    large_text = "A" * 500
    preview2, cit2 = engine.process_output("test_tool", large_text)
    assert cit2 is not None
    assert cit2.startswith("spill_")
    assert "DỮ LIỆU ĐÃ ĐƯỢC TÓM LƯỢC" in preview2

    # Check read spill slice
    slice_data = engine.read_spill(cit2, offset=0, limit=10)
    assert slice_data == "AAAAAAAAAA"


@pytest.mark.unit
def test_fast_path_matcher():
    tool, args = FastPathMatcher.match("báo cáo tiến độ dự án")
    assert tool == "tool_get_progress"

    tool, args = FastPathMatcher.match("cho anh xem các task quá hạn")
    assert tool == "tool_query_tasks"
    assert args.get("is_overdue") is True

    tool, args = FastPathMatcher.match("phiên bản mới có những bug nào đã sửa")
    assert tool == "tool_get_changelog"
    assert args.get("only_fixes") is True


@pytest.mark.unit
def test_hitl_approval_policy():
    provider = StandardApprovalProvider(policy=ApprovalPolicy.PROMPT_ON_DESTRUCTIVE)

    # Safe read tool -> Auto approve
    ok, _ = provider.request_approval("tool_query_tasks", {})
    assert ok is True

    # Destructive tool with dry_run=False -> Requires approval
    ok, reason = provider.request_approval("tool_rebalance_workload", {"dry_run": False})
    assert ok is False
    assert "cần người dùng xác nhận" in reason


@pytest.mark.unit
def test_car_v3_loop_driver_stream():
    memory = SessionMemory(system_prompt="Bạn là Civix Agent.")
    events = KernelEvents()

    # Track lifecycle interceptor execution
    waterfall_hit = []
    events.use_waterfall("agent/pre-step", lambda p, n: (waterfall_hit.append("pre-step"), n(p))[1])
    events.use_waterfall("tools/pre-execute", lambda p, n: (waterfall_hit.append("pre-tool"), n(p))[1])

    def mock_llm_stream(messages, tools):
        yield {"thinking_delta": "Suy nghĩ..."}
        yield {
            "tool_call_deltas": [
                {
                    "index": 0,
                    "id": "mock_call_1",
                    "name": "mock_get_data",
                    "arguments_delta": '{"param": 123}',
                }
            ]
        }

    driver = AgentLoopDriver(
        memory=memory,
        tools_schema=[],
        tool_executor=lambda name, args: {"status": "ok", "val": args.get("param")},
        llm_stream_fn=mock_llm_stream,
        events=events,
        model_name="gpt-4o-mini",
    )

    # Run 1 turn
    sse_frames = list(driver.run_turn_stream("Chạy thử nghiệm"))
    assert len(sse_frames) > 0
    assert "pre-step" in waterfall_hit
    assert "pre-tool" in waterfall_hit
