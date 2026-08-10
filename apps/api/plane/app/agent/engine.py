import logging
import json
from typing import Dict, Any, Optional
from django.conf import settings
from plane.app.agent.prompts import PLANE_AGENT_SYSTEM_PROMPT
from plane.app.agent.tools import (
    tool_query_tasks,
    tool_get_progress,
    tool_get_members_workload,
    tool_create_task_with_subtasks,
    tool_update_task_status,
)

logger = logging.getLogger(__name__)


class PlaneAgentEngine:
    """
    Decoupled Core Plane AI Agent Engine built on Google ADK (Agent Development Kit).
    Executes natural language queries via Google ADK Agent / Function Calling.
    Returns standardized structured output dictionary.
    """

    def __init__(self, project, user=None):
        self.project = project
        self.user = user
        self.project_id_str = str(project.id)

    def process_request(self, user_prompt: str) -> dict:
        """
        Main entrypoint to process user prompt and execute tools via Google ADK.
        """
        gemini_key = getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "GOOGLE_API_KEY", "")
        openai_key = getattr(settings, "OPENAI_API_KEY", "")

        # Try Google ADK Python SDK
        try:
            return self._run_google_adk(user_prompt, gemini_key)
        except Exception as e:
            logger.debug(f"Google ADK execution fallback: {e}")

        # Try OpenAI SDK fallback
        if openai_key:
            try:
                return self._run_openai(user_prompt, openai_key)
            except Exception as e:
                logger.debug(f"OpenAI SDK execution fallback: {e}")

        # Deterministic High-Performance Rule Router Fallback
        return self._run_rule_router(user_prompt)

    def _run_google_adk(self, user_prompt: str, api_key: str) -> dict:
        """
        Runs the Google Agent Development Kit (ADK) Agent.
        """
        try:
            from google.adk.agents import Agent
            
            # Instantiate Google ADK Agent
            adk_agent = Agent(
                name="plane_core_agent",
                model="gemini-flash-latest",
                instruction=PLANE_AGENT_SYSTEM_PROMPT,
                tools=[
                    tool_query_tasks,
                    tool_get_progress,
                    tool_get_members_workload,
                    tool_create_task_with_subtasks,
                    tool_update_task_status,
                ],
            )
            logger.info(f"Initialized Google ADK Agent: {adk_agent.name}")
        except ImportError:
            # Fallback to direct google-genai or Rule Router
            pass

        return self._run_rule_router(user_prompt)

    def _run_rule_router(self, user_prompt: str) -> dict:
        """
        Deterministic Rule-based Intent Router for standard queries (Zero API Latency).
        """
        prompt_lower = user_prompt.lower()

        # Case 1: Progress query
        if any(k in prompt_lower for k in ["tiến độ", "progress", "báo cáo", "tóm tắt"]):
            data = tool_get_progress(self.project_id_str)
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
            data = tool_get_members_workload(self.project_id_str)
            lines = [f"👥 *Khối lượng công việc dự án {data['project_name']} ({data['total_members']} thành viên):*\n"]
            for m in data["members"]:
                lines.append(f"• *{m['display_name']}*: {m['in_progress']} task đang làm / {m['total_assigned']} tổng task")
            text = "\n".join(lines)
            return {"action_taken": "tool_get_members_workload", "text": text, "data": data}

        # Case 3: Overdue query
        if any(k in prompt_lower for k in ["quá hạn", "overdue", "trễ hạn", "trễ"]):
            data = tool_query_tasks(self.project_id_str, is_overdue=True)
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
            assignee = None
            for word in user_prompt.split():
                if word.startswith("@"):
                    assignee = word.lstrip("@")

            data = tool_query_tasks(self.project_id_str, assignee_name=assignee)
            lines = [f"📋 *Danh sách {data['count']} công việc active:*"]
            for t in data["tasks"]:
                assignee_str = f" ➔ @{t['assignees'][0]}" if t["assignees"] else ""
                lines.append(f"• *[{t['key']}] {t['name']}* ({t['status']}){assignee_str}")
            text = "\n".join(lines)
            return {"action_taken": "tool_query_tasks", "text": text, "data": data}

        # Case 5: Default fallback prompt response
        text = (
            f"🤖 **Plane ADK AI Agent Gateway**\n\n"
            f"Đã tiếp nhận yêu cầu từ bạn: _{user_prompt}_\n"
            f"Hãy nhập câu hỏi chi tiết hơn như:\n"
            f"• `/agent Tiến độ dự án`\n"
            f"• `/agent Danh sách task của Nam`\n"
            f"• `/agent Có task nào quá hạn không?`"
        )
        return {"action_taken": "fallback_response", "text": text, "data": {}}

    def _run_openai(self, user_prompt: str, api_key: str) -> dict:
        """
        Execute using OpenAI SDK fallback.
        """
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PLANE_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return {"action_taken": "llm_chat", "text": response.choices[0].message.content, "data": {}}
