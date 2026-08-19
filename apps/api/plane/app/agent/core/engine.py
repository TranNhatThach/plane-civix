import os
import logging
import inspect
from typing import Dict, Any, Optional
from plane.license.utils.instance_value import get_configuration_value
from plane.db.models import Project, ProjectMember
from plane.app.agent.registry import ToolRegistry
from plane.app.agent.core.llm_client import SystemLLMClient
from plane.app.agent.core.scope_guard import AgentContext, scope_guard, ScopeViolationError
from plane.app.agent.core.context_resolver import ContextResolver

# Ensure all tools are registered into ToolRegistry
import plane.app.agent.tools  # noqa

logger = logging.getLogger(__name__)


def check_user_project_permission(user, project, min_role=15, strict=False) -> bool:
    """Check if user has member (>=15) or admin (20) role in project."""
    if not user:
        return True
    if getattr(user, "is_superuser", False):
        return True
    pm = ProjectMember.objects.filter(project=project, member=user, is_active=True, deleted_at__isnull=True).first()
    if not pm:
        return False
    return pm.role >= min_role



class PlaneAgentEngine:
    """
    Modular Decoupled Core Plane AI Agent Engine.
    Executes natural language queries strictly using system-configured LLM provider/model
    with dynamic Tool Registry, Scope Guard Security Boundary, and Fast Path Deterministic Rendering.
    """

    def __init__(self, project, user=None, context: Optional[AgentContext] = None):
        self.project = project
        self.user = user
        self.project_id_str = str(project.id) if project else None
        
        # Build or attach Context Object
        if context:
            self.context = context
        else:
            workspace_id = str(project.workspace_id) if project else ""
            user_id_str = str(user.id) if user else ""
            self.context = AgentContext(
                slack_user_id="user_slack",
                plane_user_id=user_id_str,
                is_superuser=getattr(user, "is_superuser", False) if user else False,
                workspace_id=workspace_id,
                project_id=self.project_id_str,
            )

    def process_request(self, user_prompt: str) -> dict:
        """
        Main entrypoint to process user prompt and execute tools via system configured LLM.
        Applies Response Generation Policy: Direct Deterministic Fast Path vs Analytical Synthesis Path.
        """
        (fast_path_cfg,) = get_configuration_value(
            [
                {"key": "AGENT_FAST_PATH_ENABLED", "default": os.environ.get("AGENT_FAST_PATH_ENABLED", "1")},
            ]
        )
        is_fast_path_enabled = str(fast_path_cfg or "1").strip().lower() in ["1", "true", "yes"]

        prompt_lower = (user_prompt or "").lower()
        # 1. Fast-Path Pattern Matcher: Instant sub-50ms execution for standard read-only queries
        fast_path_tool = None
        fast_path_args = {}

        if is_fast_path_enabled:
            if any(kw in prompt_lower for kw in ["báo cáo workspace", "tổng quan workspace", "tất cả task workspace", "tiến độ workspace"]):
                fast_path_tool = "tool_get_workspace_summary"
            elif any(kw in prompt_lower for kw in ["báo cáo tiến độ", "xem tiến độ", "tiến độ dự án"]):
                fast_path_tool = "tool_get_progress"
            elif any(kw in prompt_lower for kw in ["task của tôi", "công việc của tôi", "việc của tôi", "tasks của tôi"]):
                fast_path_tool = "tool_query_tasks"
                if self.user:
                    fast_path_args["assignee_id"] = str(self.user.id)
                    fast_path_args["assignee_name"] = self.user.email or self.user.display_name or self.user.first_name
                elif self.context and self.context.plane_user_id:
                    fast_path_args["assignee_id"] = str(self.context.plane_user_id)
            elif any(kw in prompt_lower for kw in ["quá hạn", "trễ hạn"]) and not any(kw in prompt_lower for kw in ["phân bổ", "điều chuyển", "rebalance"]):
                fast_path_tool = "tool_query_tasks"
                fast_path_args["is_overdue"] = True

            elif any(kw in prompt_lower for kw in ["danh sách task", "xem task", "danh sách công việc"]):
                has_specific_filters = any(word in prompt_lower for word in ["của ", "trạng thái", "in progress", "done", "completed", "lọc", "ưu tiên"])
                if not has_specific_filters:
                    fast_path_tool = "tool_query_tasks"

            elif any(kw in prompt_lower for kw in ["thành viên", "khối lượng công việc", "ai làm gì", "phân bổ công việc"]):
                fast_path_tool = "tool_get_members_workload"
            elif any(kw in prompt_lower for kw in ["danh sách dự án", "xem các dự án", "tất cả dự án"]):
                fast_path_tool = "tool_list_projects"
            elif any(kw in prompt_lower for kw in ["changelog", "phiên bản", "cập nhật gì", "bản cập nhật", "có gì mới", "bug nào", "lỗi đã sửa"]):
                fast_path_tool = "tool_get_changelog"
                if any(w in prompt_lower for w in ["bug", "lỗi", "fix", "sửa"]):
                    fast_path_args["only_fixes"] = True

        if fast_path_tool:
            registered_tool = ToolRegistry.get_tool(fast_path_tool)
            if registered_tool:
                target_func = registered_tool.func
                sig_params = inspect.signature(target_func).parameters
                has_var_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig_params.values())

                fast_path_args["_context"] = self.context
                if "workspace_id" in sig_params or has_var_kwargs:
                    fast_path_args["workspace_id"] = self.context.workspace_id

                valid_proj_id = self.project_id_str if (self.project_id_str and str(self.project_id_str).strip() not in ["None", "null", ""]) else None
                if "project_id" in sig_params and valid_proj_id and fast_path_tool not in ["tool_list_projects", "tool_get_workspace_summary"]:
                    fast_path_args["project_id"] = valid_proj_id

                filtered_args = {k: v for k, v in fast_path_args.items() if has_var_kwargs or k in sig_params}
                try:
                    tool_result = target_func(**filtered_args)
                    return self._format_tool_response(fast_path_tool, tool_result)
                except ScopeViolationError as scope_err:
                    return {"action_taken": "scope_violation_error", "text": str(scope_err), "data": {"error": str(scope_err)}}




        try:
            llm_client = SystemLLMClient()
            proj_name = self.project.name if self.project else "Không chỉ định"
            context_prompt = (
                f"Context hiện tại: Workspace ID là '{self.context.workspace_id}', Dự án mặc định là '{proj_name}' (ID: {self.project_id_str}).\n"
                f"Yêu cầu từ người dùng: {user_prompt}"
            )

            text_response, tool_call = llm_client.generate_completion(user_prompt, context_prompt)

            if tool_call:
                func_name = tool_call["name"]
                func_args = tool_call["args"]

                registered_tool = ToolRegistry.get_tool(func_name)
                if registered_tool:
                    target_func = registered_tool.func
                    sig_params = inspect.signature(target_func).parameters
                    has_var_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig_params.values())


                    # Inject authoritative Context and Parameters
                    func_args["_context"] = self.context
                    if "workspace_id" in sig_params or has_var_kwargs:
                        func_args["workspace_id"] = self.context.workspace_id
                    if "project_id" in sig_params and self.project_id_str and func_name != "tool_list_projects":
                        func_args["project_id"] = self.project_id_str
                    if "created_by_user_id" in sig_params and self.user:
                        func_args["created_by_user_id"] = str(self.user.id)

                    filtered_args = {}
                    for k, v in func_args.items():
                        if has_var_kwargs or k in sig_params:
                            filtered_args[k] = v

                    try:
                        tool_result = target_func(**filtered_args)

                    except ScopeViolationError as scope_err:
                        return {
                            "action_taken": "scope_violation_error",
                            "text": str(scope_err),
                            "data": {"error": str(scope_err)},
                        }

                    # Fast Path: Direct Deterministic Rendering Policy
                    return self._format_tool_response(func_name, tool_result)

            return {
                "action_taken": "system_llm_chat",
                "text": text_response or "",
                "data": {},
            }

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

    def _format_tool_response(self, func_name: str, tool_result: dict) -> dict:
        res_data = {"action_taken": func_name, "text": "", "data": tool_result}
        proj_name = self.project.name if self.project else "Dự án"

        if func_name == "tool_get_progress":
            res_data["text"] = (
                f"📊 *Dạ em xin gửi báo cáo tiến độ dự án {tool_result.get('project_name', proj_name)}:*\n\n"
                f"• Mức độ hoàn thành: *{tool_result.get('completion_percentage', 0)}%*\n"
                f"• Công việc đã xong: *{tool_result.get('completed_tasks', 0)}* / {tool_result.get('total_tasks', 0)} tasks\n"
                f"• Công việc đang làm: *{tool_result.get('started_tasks', 0)}* tasks\n"
                f"• Công việc trễ hạn: *{tool_result.get('overdue_tasks', 0)}* tasks\n\n"
                f"Anh/chị có cần em kiểm tra chi tiết các task nào không ạ?"
            )
        elif func_name == "tool_query_tasks":
            tasks = tool_result.get("tasks", [])
            if not tasks:
                res_data["text"] = f"ℹ️ Dạ em kiểm tra trong dự án *{proj_name}* không tìm thấy công việc nào thỏa mãn."
            else:
                lines = [f"📋 *Dạ em xin gửi danh sách {tool_result.get('count', len(tasks))} công việc trong dự án {proj_name}:*"]
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
            lines = [f"👥 *Phân bổ công việc thành viên dự án {tool_result.get('project_name', proj_name)} ({tool_result.get('total_members', len(members))} thành viên):*\n"]
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
                    res_data["text"] = f"ℹ️ Hiện tại dự án *{proj_name}* không có công việc quá hạn nào cần điều chuyển."
                else:
                    text = (
                        f"🤖 *ĐỀ XUẤT TÁI PHÂN BỔ CÔNG VIỆC DỰ ÁN {tool_result.get('project_name', proj_name).upper()}*\n\n"
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
            lines = [f"🚀 *Danh sách {tool_result.get('count', len(cycles))} Sprint/Cycle của dự án {tool_result.get('project_name', proj_name)}:*"]
            for c in cycles:
                lines.append(f"• *{c['name']}* ({c['issue_count']} tasks)")
            res_data["text"] = "\n".join(lines)
        elif func_name == "tool_export_report":
            res_data["text"] = tool_result.get("report_markdown", "")
        elif func_name == "tool_get_workspace_summary":
            projects = tool_result.get("projects", [])
            lines = [
                f"🏢 *BÁO CÁO TỔNG HỢP TOÀN WORKSPACE*\n",
                f"• *Tổng số dự án*: `{tool_result.get('total_projects', len(projects))}`",
                f"• *Mức độ hoàn thành*: `{tool_result.get('workspace_completion_percentage', 0)}%`",
                f"• *Tổng số task*: `{tool_result.get('total_workspace_tasks', 0)}` tasks (Đã xong: `{tool_result.get('total_workspace_completed', 0)}` | Quá hạn: `{tool_result.get('total_workspace_overdue', 0)}`)\n",
                "📊 *Chi tiết theo từng dự án:*"
            ]
            for p in projects:
                lines.append(f"• *{p['name']}* (`{p['identifier']}`): {p['completion_percentage']}% hoàn thành ({p['completed_tasks']}/{p['total_tasks']} tasks | `{p['overdue_tasks']}` quá hạn)")
            res_data["text"] = "\n".join(lines)
        elif func_name == "tool_get_changelog":
            v_name = tool_result.get("version", "Mới nhất")
            title = tool_result.get("title", "")
            r_date = tool_result.get("release_date", "")
            summary = tool_result.get("summary", "")
            fixes = tool_result.get("fixes", [])
            features = tool_result.get("features", [])
            only_fixes = tool_result.get("only_fixes", False)

            lines = [f"🚀 *Nhật Ký Phiên Bản Civix — {v_name} ({r_date})*"]
            lines.append(f"*{title}*\n_{summary}_\n")

            if not only_fixes and features:
                lines.append("*✨ Tính năng mới:*")
                for f in features:
                    lines.append(f"• {f}")
                lines.append("")

            if fixes:
                lines.append("*🐛 Các lỗi đã khắc phục (Bug Fixes):*")
                for fix in fixes:
                    lines.append(f"• {fix}")
                lines.append("")

            lines.append("💡 _Anh/chị có thể truy cập Web Plane → /changelog để xem đầy đủ chi tiết mọi phiên bản._")
            res_data["text"] = "\n".join(lines)
        else:
            res_data["text"] = f"Dạ em đã thực hiện xong tác vụ *{func_name}* cho dự án {proj_name} rồi ạ! 😊"


        return res_data

