import logging
import json
import inspect
from typing import Dict, Any, Optional
from plane.app.agent.prompts import PLANE_AGENT_SYSTEM_PROMPT
from plane.app.agent.tools import (
    tool_query_tasks,
    tool_get_progress,
    tool_get_members_workload,
    tool_create_task_with_subtasks,
    tool_update_task_status,
    tool_list_projects,
    tool_manage_cycles,
    tool_rebalance_workload,
    tool_export_report,
    tool_tag_labels,
)
from plane.db.models import Project, ProjectMember
from plane.app.views.external.base import get_llm_config

logger = logging.getLogger(__name__)


def check_user_project_permission(user, project, min_role=15, strict=False) -> bool:
    """Check if user has member (>=15) or admin (20) role in project.

    By default, strict=False allows team members on Slack to freely query and test.
    """
    if not strict:
        return True
    if not user or not getattr(user, "is_authenticated", True):
        return True
    if getattr(user, "is_superuser", False):
        return True
    pm = ProjectMember.objects.filter(project=project, member=user, is_active=True, deleted_at__isnull=True).first()
    if not pm:
        return False
    return pm.role >= min_role


TOOLS_MAP = {
    "tool_query_tasks": tool_query_tasks,
    "tool_get_progress": tool_get_progress,
    "tool_get_members_workload": tool_get_members_workload,
    "tool_create_task_with_subtasks": tool_create_task_with_subtasks,
    "tool_update_task_status": tool_update_task_status,
    "tool_list_projects": tool_list_projects,
    "tool_manage_cycles": tool_manage_cycles,
    "tool_rebalance_workload": tool_rebalance_workload,
    "tool_export_report": tool_export_report,
    "tool_tag_labels": tool_tag_labels,
}

OPENAI_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "tool_query_tasks",
            "description": "Tra cứu danh sách công việc (tasks) trong dự án theo tên người làm, trạng thái, quá hạn hoặc mức độ ưu tiên.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID UUID của dự án Plane."},
                    "assignee_name": {"type": "string", "description": "Tên hoặc email của thành viên cần lọc task."},
                    "status_group": {"type": "string", "enum": ["backlog", "started", "completed", "all"], "description": "Nhóm trạng thái công việc."},
                    "is_overdue": {"type": "boolean", "description": "True nếu chỉ tìm các công việc đã quá hạn."},
                    "priority": {"type": "string", "enum": ["urgent", "high", "medium", "low"], "description": "Mức độ ưu tiên."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_get_progress",
            "description": "Lấy báo cáo tổng quan về phần trăm tiến độ dự án, tổng số task hoàn thành, đang làm và quá hạn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID UUID của dự án Plane."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_get_members_workload",
            "description": "Thống kê danh sách thành viên dự án và số lượng khối lượng công việc họ đang đảm nhận.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID UUID của dự án Plane."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_create_task_with_subtasks",
            "description": "Tạo một công việc (task) mới trong dự án kèm danh sách các task con (sub-tasks) nếu có.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID UUID của dự án Plane."},
                    "title": {"type": "string", "description": "Tiêu đề công việc chính."},
                    "description": {"type": "string", "description": "Mô tả chi tiết công việc."},
                    "assignee_name": {"type": "string", "description": "Tên hoặc email người được gán việc."},
                    "priority": {"type": "string", "enum": ["urgent", "high", "medium", "low"], "description": "Mức ưu tiên."},
                    "due_date": {"type": "string", "description": "Hạn chót định dạng YYYY-MM-DD."},
                    "subtasks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Danh sách tiêu đề các task con."
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_update_task_status",
            "description": "Cập nhật trạng thái hoặc thông tin của một task theo mã task key (ví dụ: CIVIX-10).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_key": {"type": "string", "description": "Mã công việc, ví dụ: CIVIX-10."},
                    "status": {"type": "string", "description": "Tên hoặc nhóm trạng thái mới (backlog, started, completed, done, cancelled)."},
                    "assignee_name": {"type": "string", "description": "Tên người được đổi gán việc."}
                },
                "required": ["task_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_list_projects",
            "description": "Tra cứu danh sách tất cả các dự án (Projects) đang có trong hệ thống Plane.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workspace_slug": {"type": "string", "description": "Mã slug workspace (nếu có)."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_manage_cycles",
            "description": "Xem hoặc quản lý danh sách các Sprint / Cycle của dự án.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID UUID của dự án Plane."},
                    "action": {"type": "string", "enum": ["list", "create"], "description": "Hành động (list hoặc create)."},
                    "name": {"type": "string", "description": "Tên Cycle khi tạo mới."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_rebalance_workload",
            "description": "Đề xuất hoặc thực hiện tái phân bổ khối lượng công việc trễ hạn giữa các thành viên bận và rảnh.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID UUID của dự án Plane."},
                    "dry_run": {"type": "boolean", "description": "True nếu chỉ đề xuất (không đổi DB), False để áp dụng ngay."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_export_report",
            "description": "Xuất báo cáo chi tiết dự án dưới dạng Markdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID UUID của dự án Plane."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_tag_labels",
            "description": "Gán nhãn (Label) cho công việc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_key": {"type": "string", "description": "Mã task, ví dụ CIVIX-5."},
                    "label_name": {"type": "string", "description": "Tên nhãn cần gán."}
                },
                "required": ["task_key", "label_name"]
            }
        }
    }
]


class PlaneAgentEngine:
    """
    Decoupled Core Plane AI Agent Engine.
    Executes natural language queries strictly using system-configured LLM provider/model
    with Function / Tool Calling capabilities.
    """

    def __init__(self, project, user=None):
        self.project = project
        self.user = user
        self.project_id_str = str(project.id)

    def process_request(self, user_prompt: str) -> dict:
        """
        Main entrypoint to process user prompt and execute tools via system configured LLM.
        """
        # Dynamic Project Auto-matching if user mentions another project name in prompt
        prompt_lower = user_prompt.lower()
        if self.project:
            for p in Project.objects.filter(deleted_at__isnull=True):
                if p.name and (p.name.lower() in prompt_lower or (p.identifier and p.identifier.lower() in prompt_lower)):
                    self.project = p
                    self.project_id_str = str(p.id)
                    break

        # Fetch System Configured LLM Provider & Model from Plane Instance Settings
        sys_api_key, sys_model, sys_provider, sys_base_url = get_llm_config()

        try:
            return self._run_system_llm(user_prompt, sys_api_key, sys_model, sys_provider, sys_base_url)
        except Exception as e:
            logger.exception(f"Error executing System LLM: {e}")
            return {
                "action_taken": "system_llm_error",
                "text": (
                    f"⚠️ *Lỗi kết nối hoặc xử lý từ AI Agent System:*\n"
                    f"_{str(e)}_\n\n"
                    f"👉 *Hướng xử lý*: Vui lòng kiểm tra lại API Key hoặc cấu hình Model trong **Plane Settings → AI Configuration**."
                ),
                "data": {"error": str(e)},
            }

    def _run_system_llm(
        self,
        user_prompt: str,
        api_key: Optional[str],
        model: Optional[str],
        provider: Optional[str],
        base_url: Optional[str] = None,
    ) -> dict:
        """
        Executes query using system-configured LLM with OpenAI-compatible tool/function calling.
        """
        from openai import OpenAI

        eff_model = model or "gpt-4o-mini"
        eff_provider = (provider or "openai").lower()
        eff_api_key = api_key or "sk-dummy-key"

        # Sanitize base_url
        eff_base_url = base_url
        if eff_provider == "openrouter" and (not eff_base_url or "civix" in eff_base_url or "localhost" in eff_base_url or not eff_base_url.endswith("/v1")):
            eff_base_url = "https://openrouter.ai/api/v1"
        elif eff_provider == "deepseek" and (not eff_base_url or "civix" in eff_base_url or "localhost" in eff_base_url):
            eff_base_url = "https://api.deepseek.com/v1"
        elif eff_provider == "groq" and (not eff_base_url or "civix" in eff_base_url or "localhost" in eff_base_url):
            eff_base_url = "https://api.groq.com/openai/v1"

        client_kwargs = {"api_key": eff_api_key}
        if eff_base_url:
            client_kwargs["base_url"] = eff_base_url

        client = OpenAI(**client_kwargs)

        context_msg = (
            f"Context hiện tại: Dự án mặc định là '{self.project.name}' (ID: {self.project_id_str}, Identifier: {self.project.identifier}).\n"
            f"Yêu cầu từ người dùng: {user_prompt}"
        )

        messages = [
            {"role": "system", "content": PLANE_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": context_msg},
        ]

        try:
            response = client.chat.completions.create(
                model=eff_model,
                messages=messages,
                tools=OPENAI_TOOLS_SCHEMA,
                temperature=0.2,
            )
        except Exception as call_err:
            logger.warning(f"LLM tool calling failed, falling back to plain chat: {call_err}")
            response = client.chat.completions.create(
                model=eff_model,
                messages=messages,
                temperature=0.2,
            )

        choice = response.choices[0]
        message = choice.message

        if getattr(message, "tool_calls", None) and len(message.tool_calls) > 0:
            tool_call = message.tool_calls[0]
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments or "{}")
            except Exception:
                func_args = {}

            if func_name in TOOLS_MAP:
                target_func = TOOLS_MAP[func_name]
                sig_params = inspect.signature(target_func).parameters
                if "project_id" in sig_params and "project_id" not in func_args:
                    func_args["project_id"] = self.project_id_str
                if "created_by_user_id" in sig_params and self.user:
                    func_args["created_by_user_id"] = str(self.user.id)

                tool_result = target_func(**func_args)
                return self._format_tool_response(func_name, tool_result)

        return {
            "action_taken": "system_llm_chat",
            "text": message.content or "",
            "data": {},
        }

    def _format_tool_response(self, func_name: str, tool_result: dict) -> dict:
        res_data = {"action_taken": func_name, "text": "", "data": tool_result}

        if func_name == "tool_get_progress":
            res_data["text"] = (
                f"📊 *Báo cáo tiến độ dự án {tool_result.get('project_name', self.project.name)}:*\n\n"
                f"• Mức độ hoàn thành: *{tool_result.get('completion_percentage', 0)}%*\n"
                f"• Công việc đã xong: *{tool_result.get('completed_tasks', 0)}* / {tool_result.get('total_tasks', 0)} tasks\n"
                f"• Công việc đang làm: *{tool_result.get('started_tasks', 0)}* tasks\n"
                f"• Công việc trễ hạn: *{tool_result.get('overdue_tasks', 0)}* tasks\n\n"
                f"Anh/chị có cần em kiểm tra chi tiết các task nào không ạ?"
            )
        elif func_name == "tool_query_tasks":
            tasks = tool_result.get("tasks", [])
            if not tasks:
                res_data["text"] = f"ℹ️ Dạ em kiểm tra trong dự án *{self.project.name}* không tìm thấy công việc nào thỏa mãn."
            else:
                lines = [f"📋 *Danh sách {tool_result.get('count', len(tasks))} công việc trong dự án {self.project.name}:*"]
                for t in tasks:
                    assignee_str = f" ➔ @{t['assignees'][0]}" if t.get("assignees") else ""
                    lines.append(f"• *[{t['key']}] {t['name']}* ({t['status']}){assignee_str}")
                res_data["text"] = "\n".join(lines)
        elif func_name == "tool_create_task_with_subtasks":
            if tool_result.get("success"):
                subtasks = tool_result.get("subtasks", [])
                sub_lines = [f"  ▫️ [{s['key']}] {s['title']}" for s in subtasks]
                sub_str = "\n".join(sub_lines) if sub_lines else ""
                text = (
                    f"✨ *Khởi tạo công việc mới thành công!*\n\n"
                    f"• *Mã Task*: `{tool_result.get('task_key')}`\n"
                    f"• *Tiêu đề*: *{tool_result.get('title')}*\n"
                    f"• *Người phụ trách*: @{tool_result.get('assignee', 'Chưa gán')}\n"
                    f"• *Độ ưu tiên*: `{tool_result.get('priority', 'medium').upper()}`\n"
                )
                if sub_str:
                    text += f"\n*Task con (Sub-tasks):*\n{sub_str}"
                res_data["text"] = text
            else:
                res_data["text"] = f"❌ *Không thể tạo task*: {tool_result.get('error', 'Lỗi không xác định')}"
        elif func_name == "tool_get_members_workload":
            members = tool_result.get("members", [])
            lines = [f"👥 *Phân bổ công việc thành viên dự án {tool_result.get('project_name', self.project.name)} ({tool_result.get('total_members', len(members))} thành viên):*\n"]
            for m in members:
                lines.append(f"• *{m['display_name']}*: Đang làm `{m['in_progress']}` task | Đã xong `{m['completed']}` task")
            res_data["text"] = "\n".join(lines)
        elif func_name == "tool_list_projects":
            projects = tool_result.get("projects", [])
            lines = [f"📁 *Danh sách {tool_result.get('count', len(projects))} dự án trên hệ thống:*"]
            for p in projects:
                lines.append(f"• *{p['name']}* (`{p['identifier']}`) — {p['total_issues']} tasks | {p['members_count']} thành viên")
            res_data["text"] = "\n".join(lines)
        elif func_name == "tool_rebalance_workload":
            if tool_result.get("dry_run", True):
                if not tool_result.get("reassigned_count"):
                    res_data["text"] = f"ℹ️ Hiện tại dự án *{self.project.name}* không có công việc quá hạn nào cần điều chuyển."
                else:
                    text = (
                        f"🤖 *ĐỀ XUẤT TÁI PHÂN BỔ CÔNG VIỆC DỰ ÁN {tool_result.get('project_name', self.project.name).upper()}*\n\n"
                        f"Thành viên *{tool_result.get('most_busy')}* đang bận nhiều task trễ hạn.\n"
                        f"Đề xuất chuyển *{tool_result.get('reassigned_count')} task* cho *{tool_result.get('least_busy')}*:\n"
                    )
                    for t in tool_result.get("reassigned_tasks", []):
                        text += f"• Task *{t['key']}*: _{t['title']}_\n"
                    text += "\n*Anh/chị có đồng ý thực hiện điều chuyển ngay không ạ?*"
                    res_data["text"] = text
                    res_data["requires_confirmation"] = True
                    res_data["pending_action"] = {
                        "type": "rebalance_workload",
                        "project_id": self.project_id_str,
                    }
        elif func_name == "tool_manage_cycles":
            cycles = tool_result.get("cycles", [])
            lines = [f"🚀 *Danh sách {tool_result.get('count', len(cycles))} Sprint/Cycle của dự án {tool_result.get('project_name', self.project.name)}:*"]
            for c in cycles:
                lines.append(f"• *{c['name']}* ({c['issue_count']} tasks)")
            res_data["text"] = "\n".join(lines)
        elif func_name == "tool_export_report":
            res_data["text"] = tool_result.get("report_markdown", "")
        else:
            res_data["text"] = f"Dạ em đã thực hiện xong tác vụ *{func_name}* cho dự án {self.project.name} rồi ạ! 😊"

        return res_data
