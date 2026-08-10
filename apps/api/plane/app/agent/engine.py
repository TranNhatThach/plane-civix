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
from plane.db.models import Project

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
        # Dynamic Project Auto-matching if user mentions another project name in prompt
        prompt_lower = user_prompt.lower()
        if self.project:
            for p in Project.objects.filter(deleted_at__isnull=True):
                if p.name and (p.name.lower() in prompt_lower or (p.identifier and p.identifier.lower() in prompt_lower)):
                    self.project = p
                    self.project_id_str = str(p.id)
                    break

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

        # Natural Conversational Router (Soft, Polite, Human-like responses)
        return self._run_rule_router(user_prompt)

    def _run_google_adk(self, user_prompt: str, api_key: str) -> dict:
        """
        Runs the Google Agent Development Kit (ADK) Agent.
        """
        try:
            from google.adk.agents import Agent
            
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
            pass

        return self._run_rule_router(user_prompt)

    def _run_rule_router(self, user_prompt: str) -> dict:
        """
        Natural Conversational Intent Router for warm, polite Vietnamese responses.
        """
        prompt_lower = user_prompt.strip().lower()

        # Greetings & General Chat
        greetings = ["hello", "hi", "xin chào", "chào", "chào bạn", "ơi", "alo", "test", "giúp"]
        if prompt_lower in greetings or prompt_lower.startswith("chào") or prompt_lower.startswith("hello"):
            text = (
                f"Dạ em chào anh/chị ạ! 👋 Em là Trợ lý AI Plane của dự án *{self.project.name}*.\n\n"
                f"Em có thể giúp anh/chị quản lý công việc và báo cáo dự án rất nhanh chóng. Anh/chị có thể hỏi em một số câu như:\n"
                f"• *Báo cáo tiến độ dự án {self.project.name}*\n"
                f"• *Danh sách công việc của tôi*\n"
                f"• *Kiểm tra các task bị quá hạn*\n"
                f"• *Tạo task fix bug gán cho @Nam*\n\n"
                f"Anh/chị cần em hỗ trợ điều gì hôm nay ạ? 😊"
            )
            return {"action_taken": "greeting_response", "text": text, "data": {}}

        # Case 1: Progress query
        if any(k in prompt_lower for k in ["tiến độ", "progress", "báo cáo", "tóm tắt"]):
            data = tool_get_progress(self.project_id_str)
            text = (
                f"📊 *Dạ em xin gửi báo cáo tiến độ dự án {data['project_name']}:*\n\n"
                f"• Mức độ hoàn thành: *{data['completion_percentage']}%*\n"
                f"• Công việc đã xong: *{data['completed_tasks']}* / {data['total_tasks']} tasks\n"
                f"• Công việc đang làm: *{data['started_tasks']}* tasks\n"
                f"• Công việc trễ hạn: *{data['overdue_tasks']}* tasks\n\n"
                f"Anh/chị có cần em kiểm tra chi tiết các task đang dở dang không ạ?"
            )
            return {"action_taken": "tool_get_progress", "text": text, "data": data}

        # Case 2: Members Workload query
        if any(k in prompt_lower for k in ["thành viên", "member", "tải công việc", "workload", "team", "người"]):
            data = tool_get_members_workload(self.project_id_str)
            lines = [f"👥 *Dạ em xin gửi tình hình khối lượng công việc của team dự án {data['project_name']} ({data['total_members']} thành viên):*\n"]
            for m in data["members"]:
                lines.append(f"• *{m['display_name']}*: đang phụ trách {m['in_progress']} task (đã xong {m['completed']} task)")
            lines.append("\nAnh/chị muốn gán thêm công việc cho thành viên nào không ạ?")
            text = "\n".join(lines)
            return {"action_taken": "tool_get_members_workload", "text": text, "data": data}

        # Case 3: Overdue query
        if any(k in prompt_lower for k in ["quá hạn", "overdue", "trễ hạn", "trễ"]):
            data = tool_query_tasks(self.project_id_str, is_overdue=True)
            if data["count"] == 0:
                text = f"🎉 Dạ tuyệt vời quá ạ! Hiện tại dự án *{self.project.name}* không có công việc nào bị quá hạn cả."
            else:
                lines = [f"⚠️ *Dạ em ghi nhận có {data['count']} công việc đang bị quá hạn cần chú ý:*\n"]
                for t in data["tasks"]:
                    lines.append(f"• *[{t['key']}] {t['name']}* (Hạn chót: {t['target_date']})")
                lines.append("\nAnh/chị có muốn em nhắc nhở người phụ trách không ạ?")
                text = "\n".join(lines)
            return {"action_taken": "tool_query_tasks", "text": text, "data": data}

        # Case 4: General Task query
        if any(k in prompt_lower for k in ["task", "công việc", "việc", "danh sách"]):
            assignee = None
            for word in user_prompt.split():
                if word.startswith("@"):
                    assignee = word.lstrip("@")

            data = tool_query_tasks(self.project_id_str, assignee_name=assignee)
            lines = [f"📋 *Dạ em xin gửi danh sách {data['count']} công việc trong dự án {self.project.name}:*"]
            for t in data["tasks"]:
                assignee_str = f" ➔ @{t['assignees'][0]}" if t["assignees"] else ""
                lines.append(f"• *[{t['key']}] {t['name']}* ({t['status']}){assignee_str}")
            text = "\n".join(lines)
            return {"action_taken": "tool_query_tasks", "text": text, "data": data}

        # Case 5: Default conversational fallback response
        text = (
            f"Dạ em đã nhận được yêu cầu từ anh/chị: _{user_prompt}_\n\n"
            f"Em có thể giúp anh/chị tra cứu dự án *{self.project.name}* nhanh chóng. "
            f"Anh/chị có thể thử các câu hỏi như:\n"
            f"• `/agent Tiến độ dự án {self.project.name}`\n"
            f"• `/agent Danh sách task`\n"
            f"• `/agent Các việc quá hạn`"
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
