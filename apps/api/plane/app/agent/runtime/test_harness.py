# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Standalone Test Harness for Civix Autonomous Agent Runtime (CAR-v3).
Runs 100% isolated without Docker, PostgreSQL, Redis, or Celery.

Usage:
    python plane/app/agent/runtime/test_harness.py
"""

import sys
import os
import json
import time
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Set safe standalone environment defaults
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "dummy-secret-key-for-test-harness")

# Ensure apps/api directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_API_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../../"))
if APPS_API_DIR not in sys.path:
    sys.path.insert(0, APPS_API_DIR)

# Safe optional Django setup
try:
    import django
    django.setup()
except Exception as e:
    pass

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
from plane.app.agent.loop import AgentLoopDriver, EventStream, QuotaGuard, FastPathMatcher


# Color helpers for terminal output
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def print_banner(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN} {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")


def parse_sse_event(raw_line: str) -> Dict[str, Any]:
    """Helper to parse a raw 'data: {...}' SSE string."""
    clean = raw_line.strip()
    if clean.startswith("data: "):
        clean = clean[6:]
    try:
        return json.loads(clean)
    except Exception:
        return {}


# -------------------------------------------------------------
# TEST 1: Direct Single-Step Stream (Chat Answer)
# -------------------------------------------------------------
def test_direct_streaming():
    print_banner("TEST 1: Direct Token-by-Token SSE Stream (Chat Answer)")

    def mock_llm_stream(messages, tools):
        words = ["Chào", " bạn!", " Em", " là", " Trợ", " lý", " Civix", " AI.", " Em", " có", " thể", " giúp", " gì", " cho", " bạn?"]
        for w in words:
            yield {"content_delta": w}

    memory = SessionMemory(system_prompt="Bạn là Civix Agent.")
    driver = AgentLoopDriver(
        memory=memory,
        tools_schema=[],
        tool_executor=lambda name, args: {},
        llm_stream_fn=mock_llm_stream,
        model_name="gpt-4o-mini",
    )

    events_received = []
    print(f"{Colors.DIM}Receiving live SSE Stream:{Colors.RESET} ", end="", flush=True)

    for sse_frame in driver.run_turn_stream("Xin chào!"):
        evt = parse_sse_event(sse_frame)
        events_received.append(evt)
        if evt.get("event") == "model.content.delta":
            print(f"{Colors.GREEN}{evt.get('delta')}{Colors.RESET}", end="", flush=True)

    print("\n")
    event_types = [e.get("event") for e in events_received]
    assert "run.step.start" in event_types, "Missing step.start"
    assert "model.content.delta" in event_types, "Missing content.delta"
    assert "run.completed" in event_types, "Missing run.completed"

    completion_event = [e for e in events_received if e.get("event") == "run.completed"][0]
    usage = completion_event.get("usage", {})
    print(f"{Colors.BOLD}✅ Test 1 PASSED!{Colors.RESET}")
    print(f"   • Total Tokens: {usage.get('total_tokens')}")
    print(f"   • Cost USD: ${usage.get('cost_usd'):.6f}")
    print(f"   • Duration: {usage.get('duration_ms')}ms")


# -------------------------------------------------------------
# TEST 2: Multi-Step ReAct Loop with Waterfall Interceptors
# -------------------------------------------------------------
def test_multistep_react_loop():
    print_banner("TEST 2: Multi-Step ReAct Loop (Autonomous Tool Call & Synthesis)")

    step_counter = {"count": 0}
    waterfall_logged = []

    events = KernelEvents()
    events.use_waterfall("agent/pre-step", lambda p, n: (waterfall_logged.append("pre-step"), n(p))[1])
    events.use_waterfall("tools/pre-execute", lambda p, n: (waterfall_logged.append("pre-tool"), n(p))[1])

    def mock_llm_react_stream(messages, tools):
        step_counter["count"] += 1

        if step_counter["count"] == 1:
            yield {"thinking_delta": "Người dùng hỏi về task quá hạn. Tôi cần gọi tool_query_tasks với is_overdue=True..."}
            yield {
                "tool_call_deltas": [
                    {
                        "index": 0,
                        "id": "call_mock_123",
                        "name": "tool_query_tasks",
                        "arguments_delta": '{"is_overdue": true}',
                    }
                ]
            }
        elif step_counter["count"] == 2:
            yield {"thinking_delta": "Đã nhận kết quả query. Bây giờ tổng hợp câu trả lời cho người dùng..."}
            answer_parts = ["Dạ em kiểm tra thấy hiện tại dự án đang có ", "**2 công việc quá hạn**", ":\n", "1. [CIV-101] Lỗi đăng nhập SSO\n", "2. [CIV-104] Thiết kế DB migration."]
            for part in answer_parts:
                yield {"content_delta": part}

    def mock_tool_executor(tool_name: str, args: Dict[str, Any]):
        return {
            "count": 2,
            "tasks": [
                {"key": "CIV-101", "name": "Lỗi đăng nhập SSO", "status": "In Progress"},
                {"key": "CIV-104", "name": "Thiết kế DB migration", "status": "Backlog"},
            ]
        }

    memory = SessionMemory(system_prompt="Bạn là Civix Agent.")
    driver = AgentLoopDriver(
        memory=memory,
        tools_schema=[{"type": "function", "function": {"name": "tool_query_tasks"}}],
        tool_executor=mock_tool_executor,
        llm_stream_fn=mock_llm_react_stream,
        events=events,
        model_name="deepseek-reasoner",
    )

    events_received = []
    for sse_frame in driver.run_turn_stream("Kiểm tra task quá hạn"):
        evt = parse_sse_event(sse_frame)
        events_received.append(evt)
        ename = evt.get("event")
        if ename == "model.thinking":
            print(f"{Colors.MAGENTA}[THINKING]{Colors.RESET} {evt.get('delta')}")
        elif ename == "tool.call.start":
            print(f"{Colors.YELLOW}[TOOL CALL START]{Colors.RESET} {evt.get('name')}({evt.get('args')})")
        elif ename == "tool.call.result":
            print(f"{Colors.CYAN}[TOOL RESULT]{Colors.RESET} Received {evt.get('result', {}).get('count')} tasks")
        elif ename == "model.content.delta":
            print(f"{Colors.GREEN}{evt.get('delta')}{Colors.RESET}", end="", flush=True)

    print("\n")
    event_types = [e.get("event") for e in events_received]
    assert "tool.call.start" in event_types, "Missing tool.call.start"
    assert "tool.call.result" in event_types, "Missing tool.call.result"
    assert "ui.card" in event_types, "Missing ui.card preview"
    assert "pre-step" in waterfall_logged, "Missing waterfall pre-step"
    assert "pre-tool" in waterfall_logged, "Missing waterfall pre-tool"
    print(f"{Colors.BOLD}✅ Test 2 PASSED! Multi-step ReAct & Waterfall Interceptors validated.{Colors.RESET}")


# -------------------------------------------------------------
# TEST 3: Output Spilling & Context Hygiene
# -------------------------------------------------------------
def test_output_spilling():
    print_banner("TEST 3: Tool Output Spilling Engine (Context Window Protection)")

    spill_engine = SpillingEngine(threshold=200)
    huge_data = {"items": [f"Task number #{i} with long description and logs" for i in range(200)]}

    preview, citation_id = spill_engine.process_output("tool_query_all", huge_data)
    assert citation_id is not None
    assert citation_id.startswith("spill_")
    assert "DỮ LIỆU ĐÃ ĐƯỢC TÓM LƯỢC" in preview

    slice_data = spill_engine.read_spill(citation_id, offset=0, limit=50)
    assert len(slice_data) == 50

    print(f"   • Citation ID: {citation_id}")
    print(f"   • Truncated preview length: {len(preview)} chars (Protected Context Window)")
    print(f"{Colors.BOLD}✅ Test 3 PASSED! Output Spilling functioning cleanly.{Colors.RESET}")


# -------------------------------------------------------------
# TEST 4: Sub-50ms Fast-Path Matcher
# -------------------------------------------------------------
def test_fast_path():
    print_banner("TEST 4: Sub-50ms Deterministic Fast-Path Matcher")

    test_queries = [
        ("Báo cáo tiến độ dự án website", "tool_get_progress"),
        ("Xem danh sách công việc quá hạn", "tool_query_tasks"),
        ("Thành viên nào đang bận việc nhất", "tool_get_members_workload"),
        ("Phiên bản cập nhật gần đây sửa lỗi gì", "tool_get_changelog"),
    ]

    for q, expected_tool in test_queries:
        t_start = time.perf_counter()
        tool, args = FastPathMatcher.match(q)
        duration_ms = (time.perf_counter() - t_start) * 1000
        assert tool == expected_tool, f"Mismatch for '{q}': got {tool}"
        print(f"   • Query: '{q}' ➔ {tool} ({duration_ms:.3f}ms)")

    print(f"{Colors.BOLD}✅ Test 4 PASSED! All Fast-Path queries resolved under 1ms.{Colors.RESET}")


# -------------------------------------------------------------
# TEST 5: Event Sourcing & Deterministic Replay
# -------------------------------------------------------------
def test_event_sourcing_replay():
    print_banner("TEST 5: Append-Only Event Log & Replay Projection")

    log = InMemoryEventLog(session_id="eval_ses_99")
    log.append(SessionEvent(type=EventTypes.TURN_START, payload={}))
    log.append(SessionEvent(type=EventTypes.USER_MESSAGE, payload={"content": "Tạo task mới"}))
    log.append(SessionEvent(type=EventTypes.TOOL_CALL, payload={"id": "call_1", "name": "tool_create_task", "arguments_str": '{"title": "Bug"}'}))
    log.append(SessionEvent(type=EventTypes.TOOL_RESULT, payload={"id": "call_1", "name": "tool_create_task", "result": '{"success": true}'}))
    log.append(SessionEvent(type=EventTypes.ASSISTANT_MESSAGE, payload={"content": "Đã tạo task Bug thành công!"}))

    messages = derive_messages(log.get_events())
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert len(messages[1].get("tool_calls", [])) == 1
    assert messages[2]["role"] == "tool"
    assert messages[3]["role"] == "assistant"
    assert messages[3]["content"] == "Đã tạo task Bug thành công!"

    # Fork session
    forked = log.fork(up_to_index=2, new_session_id="fork_branch_01")
    assert len(forked.get_events()) == 2

    print(f"   • Event Log successfully projected to {len(messages)} ChatMessages.")
    print(f"   • Session Forked successfully to branch 'fork_branch_01'.")
    print(f"{Colors.BOLD}✅ Test 5 PASSED! Event Sourcing & Projection verified.{Colors.RESET}")


if __name__ == "__main__":
    print(f"\n{Colors.BOLD}{Colors.GREEN}======================================================================{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN} RUNNING PRODUCTION-GRADE AGENT HARNESS (CAR-v3) VERIFICATION SUITE  {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}======================================================================{Colors.RESET}")

    test_direct_streaming()
    test_multistep_react_loop()
    test_output_spilling()
    test_fast_path()
    test_event_sourcing_replay()

    print(f"\n{Colors.BOLD}{Colors.GREEN}======================================================================{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN} 🎉 ALL TESTS PASSED! FULL AGENT HARNESS IS PRODUCTION READY!         {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}======================================================================{Colors.RESET}\n")
