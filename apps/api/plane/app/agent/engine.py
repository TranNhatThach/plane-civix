import logging
import json
from django.conf import settings
from plane.app.agent.prompts import PLANE_AGENT_SYSTEM_PROMPT
from plane.app.agent.tools import (
    AGENT_TOOLS_SCHEMA,
    execute_query_tasks,
    execute_get_progress,
    execute_get_members_workload,
    execute_create_task_with_subtasks,
    execute_update_task_status,
)

logger = logging.getLogger(__name__)


class PlaneAgentEngine:
    """
    Decoupled Core Plane AI Agent Engine.
    Executes natural language queries via Function Calling / ReAct loop.
    Returns standardized structured output JSON.
    """

    def __init__(self, project, user=None):
        self.project = project
        self.user = user

    def process_request(self, user_prompt: str) -> dict:
        """
        Main entrypoint to process user prompt and execute tools.
        Returns standardized dictionary response:
        {
            "action_taken": "tool_query_tasks",
            "text": "Human readable Markdown answer",
            "data": {... structured JSON tool output ...}
        }
        """
        prompt_lower = user_prompt.lower()

        # Step 1: Check LLM API Key availability
        gemini_key = getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "GOOGLE_API_KEY", "")
        openai_key = getattr(settings, "OPENAI_API_KEY", "")

        # Try Google GenAI SDK if key present
        if gemini_key:
            try:
                return self._run_google_genai(user_prompt, gemini_key)
            except Exception as e:
                logger.warning(f"Google GenAI SDK execution failed: {e}. Falling back to OpenAI/Rule Router.")

        # Try OpenAI SDK if key present
        if openai_key:
            try:
                return self._run_openai(user_prompt, openai_key)
            except Exception as e:
                logger.warning(f"OpenAI SDK execution failed: {e}. Falling back to Rule Router.")

        # Step 2: High-Performance Rule-based Natural Language Tool Router (Zero API Latency Fallback)
        return self._run_rule_router(user_prompt)

    def _run_rule_router(self, user_prompt: str) -> dict:
        """
        Deterministic Rule-based Intent Router for standard queries.
        Ensures 100% availability even without external LLM keys.
        """
        prompt_lower = user_prompt.lower()

        # Case 1: Progress query
        if any(k in prompt_lower for k in ["tiến độ", "progress", "báo cáo", "tóm tắt"]):
            data = execute_get_progress(self.project)
            text = (
                f"📊 *Báo cáo tiến độ dự án {data['project_name']}*\n\n"
                f"• Tiến độ: *{data['completion_percentage']}%* hoàn thành\n"
                f"• Task hoàn thành: *{data['completed_tasks']}* / {data['total_tasks']}\n"
                f"• Task đang thực hiện: *{data['started_tasks']}*\n"
                f"• Task quá hạn: *{data['overdue_tasks']}*"
            )
            return {"action_taken": "tool_get_progress", "text": text, "data": data}

        # Case 2: Members Workload query
        if any(k in prompt_lower for k in ["thành viên", "member", "tải công việc", "workload", "team"]):
            data = execute_get_members_workload(self.project)
            lines = [f"👥 *Khối lượng công việc dự án {data['project_name']} ({data['total_members']} thành viên):*\n"]
            for m in data["members"]:
                lines.append(f"• *{m['display_name']}*: {m['in_progress']} task đang làm / {m['total_assigned']} tổng task")
            text = "\n".join(lines)
            return {"action_taken": "tool_get_members_workload", "text": text, "data": data}

        # Case 3: Overdue query
        if any(k in prompt_lower for k in ["quá hạn", "overdue", "trễ hạn", "trễ"]):
            data = execute_query_tasks(self.project, is_overdue=True)
            if data["count"] == 0:
                text = "🎉 Tuyệt vời! Không có task nào bị quá hạn trong dự án này."
            else:
                lines = [f"⚠️ *Có {data['count']} công việc đang bị quá hạn:*\n"]
                for t in data["tasks"]:
                    lines.append(f"• *[{t['key']}] {t['name']}* (Hạn chót: {t['target_date']})")
                text = "\n".join(lines)
            return {"action_taken": "tool_query_tasks", "text": text, "data": data}

        # Case 4: General Task query
        if any(k in prompt_lower for k in ["task", "công việc", "việc", "danh sách"]):
            # Extract assignee if mentioned
            assignee = None
            for word in user_prompt.split():
                if word.startswith("@"):
                    assignee = word.lstrip("@")

            data = execute_query_tasks(self.project, assignee_name=assignee)
            lines = [f"📋 *Danh sách {data['count']} công việc active:*"]
            for t in data["tasks"]:
                assignee_str = f" ➔ @{t['assignees'][0]}" if t["assignees"] else ""
                lines.append(f"• *[{t['key']}] {t['name']}* ({t['status']}){assignee_str}")
            text = "\n".join(lines)
            return {"action_taken": "tool_query_tasks", "text": text, "data": data}

        # Case 5: Default fallback prompt response
        text = (
            f"🤖 **Plane AI Agent Gateway**\n\n"
            f"Đã tiếp nhận yêu cầu từ bạn: _{user_prompt}_\n"
            f"Hãy nhập câu hỏi chi tiết hơn như:\n"
            f"• `/agent Tiến độ dự án`\n"
            f"• `/agent Danh sách task của Nam`\n"
            f"• `/agent Có task nào quá hạn không?`"
        )
        return {"action_taken": "fallback_response", "text": text, "data": {}}

    def _run_google_genai(self, user_prompt: str, api_key: str) -> dict:
        """
        Execute using official google-genai SDK.
        """
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        config = types.GenerateContentConfig(
            system_instruction=PLANE_AGENT_SYSTEM_PROMPT,
            tools=[{"function_declarations": AGENT_TOOLS_SCHEMA}],
            temperature=0.2,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=config,
        )

        # Check function call
        if response.function_calls:
            fc = response.function_calls[0]
            tool_name = fc.name
            args = fc.args or {}
            return self._dispatch_tool(tool_name, args)

        return {"action_taken": "llm_chat", "text": response.text, "data": {}}

    def _run_openai(self, user_prompt: str, api_key: str) -> dict:
        """
        Execute using openai SDK Function Calling.
        """
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        openai_tools = [{"type": "function", "function": t} for t in AGENT_TOOLS_SCHEMA]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PLANE_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            tools=openai_tools,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            tool_name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            return self._dispatch_tool(tool_name, args)

        return {"action_taken": "llm_chat", "text": msg.content, "data": {}}

    def _dispatch_tool(self, tool_name: str, args: dict) -> dict:
        """
        Dispatch tool call execution to tools.py functions.
        """
        if tool_name == "tool_query_tasks":
            data = execute_query_tasks(
                self.project,
                assignee_name=args.get("assignee_name"),
                status_group=args.get("status_group"),
                is_overdue=args.get("is_overdue", False),
                priority=args.get("priority"),
            )
            text = f"📋 Đã tìm thấy {data['count']} công việc tương ứng."
            return {"action_taken": tool_name, "text": text, "data": data}

        elif tool_name == "tool_get_progress":
            data = execute_get_progress(self.project)
            text = f"📊 Tiến độ dự án {data['project_name']} hiện đạt {data['completion_percentage']}%."
            return {"action_taken": tool_name, "text": text, "data": data}

        elif tool_name == "tool_get_members_workload":
            data = execute_get_members_workload(self.project)
            text = f"👥 Đã thống kê khối lượng công việc của {data['total_members']} thành viên."
            return {"action_taken": tool_name, "text": text, "data": data}

        elif tool_name == "tool_create_task_with_subtasks":
            data = execute_create_task_with_subtasks(
                self.project,
                self.user,
                title=args.get("title"),
                description=args.get("description", ""),
                assignee_name=args.get("assignee_name"),
                priority=args.get("priority", "medium"),
                due_date=args.get("due_date"),
                subtasks=args.get("subtasks"),
            )
            text = f"✅ Đã khởi tạo công việc [{data['task_key']}] *{data['title']}* thành công!"
            return {"action_taken": tool_name, "text": text, "data": data}

        elif tool_name == "tool_update_task_status":
            data = execute_update_task_status(
                self.project,
                sequence_id=args.get("sequence_id"),
                new_status=args.get("new_status"),
            )
            text = f"🔄 Đã chuyển trạng thái task [{data.get('task_key')}] sang *{data.get('new_status')}*."
            return {"action_taken": tool_name, "text": text, "data": data}

        return self._run_rule_router("")
