# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import re
import json
from html import escape
from typing import Optional

from plane.db.models import TelegramAutomation, Project, Issue, IssueComment, State
from plane.bgtasks.telegram_publisher import strip_html_tags
from plane.app.views.external.base import get_llm_config, get_llm_response


def get_project_and_automation(chat_id: str) -> tuple[Optional[TelegramAutomation], Optional[Project]]:
    """Retrieves active TelegramAutomation & Project for the given Telegram chat_id."""
    str_chat_id = str(chat_id)
    automation = (
        TelegramAutomation.objects.filter(chat_id=str_chat_id, is_active=True)
        .select_related("project", "workspace")
        .first()
    )
    if not automation:
        alt_chat_id = str_chat_id[1:] if str_chat_id.startswith("-") else f"-{str_chat_id}"
        automation = (
            TelegramAutomation.objects.filter(chat_id=alt_chat_id, is_active=True)
            .select_related("project", "workspace")
            .first()
        )

    if automation and automation.project:
        return automation, automation.project
    return automation, None


def get_workspace_and_project(chat_id: str):
    """Retrieves active TelegramAutomation, Workspace, & default Project for chat_id."""
    automation, project = get_project_and_automation(chat_id)
    workspace = None
    if automation:
        workspace = automation.workspace or (project.workspace if project else None)
    return automation, workspace, project


def handle_task_query(automation: TelegramAutomation, project: Optional[Project], query_arg: str, app_url: str) -> str:
    """Handles /task <identifier> query (e.g. CIVIX-12 or 12)."""
    if not query_arg:
        return "⚠️ Vui lòng cung cấp mã Task. Ví dụ: <code>/task CIVIX-12</code> hoặc <code>/task 12</code>"

    query_arg = query_arg.strip().upper()
    workspace = automation.workspace if automation and automation.workspace else (project.workspace if project else None)

    match = re.search(r"([a-zA-Z0-9]+)-(\d+)", query_arg)
    if match:
        proj_ident = match.group(1)
        seq_id = int(match.group(2))
        filter_kwargs = {"project__identifier__iexact": proj_ident, "sequence_id": seq_id}
        if workspace:
            filter_kwargs["project__workspace"] = workspace

        issue = (
            Issue.objects.filter(**filter_kwargs)
            .select_related("state", "created_by", "project", "project__workspace")
            .prefetch_related("assignees")
            .first()
        )
    else:
        try:
            seq_id = int(re.sub(r"\D", "", query_arg))
            filter_kwargs = {"sequence_id": seq_id}
            if project:
                filter_kwargs["project"] = project
            elif workspace:
                filter_kwargs["project__workspace"] = workspace

            issue = (
                Issue.objects.filter(**filter_kwargs)
                .select_related("state", "created_by", "project", "project__workspace")
                .prefetch_related("assignees")
                .first()
            )
        except ValueError:
            issue = None

    if not issue:
        proj_name = project.name if project else "Workspace"
        return f"🔍 Không tìm thấy Task nào với mã <b>{escape(query_arg)}</b> trong {escape(proj_name)}."

    target_project = issue.project
    identifier = f"{target_project.identifier}-{issue.sequence_id}"
    name = escape(issue.name)
    priority = (issue.priority or "none").capitalize()
    state_name = issue.state.name if issue.state else "Backlog"

    assignees_list = [a.display_name for a in issue.assignees.all() if a.display_name]
    assignees_str = ", ".join(assignees_list) if assignees_list else "Chưa phân công"

    desc_clean = strip_html_tags(issue.description_html or "")
    if len(desc_clean) > 300:
        desc_clean = desc_clean[:297] + "..."

    comments = (
        IssueComment.objects.filter(issue=issue)
        .select_related("actor")
        .order_by("-created_at")[:3]
    )

    ws_slug = target_project.workspace.slug if target_project.workspace else "default"
    issue_url = f"{app_url}/{ws_slug}/projects/{target_project.id}/issues/{issue.id}" if app_url else "#"

    lines = [
        f"📌 <b>[{identifier}] {name}</b>\n",
        f"🏷️ <b>Trạng thái:</b> <code>{escape(state_name)}</code>",
        f"⚡ <b>Ưu tiên:</b> {priority}",
        f"👤 <b>Người thực hiện:</b> {escape(assignees_str)}",
        f"📁 <b>Dự án:</b> {escape(target_project.name)} (Mã: <code>{escape(target_project.identifier)}</code>)",
    ]

    if desc_clean:
        lines.append(f"\n📖 <b>Mô tả:</b>\n<i>{escape(desc_clean)}</i>")

    if comments.exists():
        lines.append("\n💬 <b>Bình luận gần đây:</b>")
        for c in comments:
            actor_name = c.actor.display_name if c.actor else "Thành viên"
            c_clean = strip_html_tags(c.comment_html or "")
            if len(c_clean) > 100:
                c_clean = c_clean[:97] + "..."
            lines.append(f"• <b>{escape(actor_name)}</b>: <i>\"{escape(c_clean)}\"</i>")

    lines.append(f"\n🔗 <a href='{issue_url}'>Xem chi tiết Task trên Plane</a>")
    return "\n".join(lines)


def handle_projects_list(project_or_workspace, app_url: str = "") -> str:
    """Lists all active projects in the workspace with item index for easy user selection."""
    workspace = project_or_workspace.workspace if isinstance(project_or_workspace, Project) else project_or_workspace
    if not workspace:
        return "⚠️ Không xác định được Workspace."

    projects = list(Project.objects.filter(workspace=workspace).order_by("name"))
    if not projects:
        return "📁 Không có dự án nào trong Workspace."

    lines = ["📁 <b>Danh sách các Dự án trong Workspace:</b>\n"]
    lines.append("• /tasks_all — 🌟 <b>Tất cả các Dự án</b> (Toàn Workspace)\n")

    for idx, proj in enumerate(projects, 1):
        open_count = Issue.objects.filter(project=proj).exclude(state__group__in=["completed", "cancelled"]).count()
        lines.append(
            f"• /tasks_{idx} — 📁 <b>{escape(proj.name)}</b> (Mã: <code>{escape(proj.identifier)}</code>) — {open_count} task đang mở"
        )

    lines.append("\n💡 <i>Mẹo: Nhấn trực tiếp <code>/tasks_1</code> để xem Dự án 1, hoặc <code>/tasks_all</code> để xem tất cả.</i>")
    lines.append("💡 <i>Khi tạo task: Gõ <code>/create 1: Tên task</code> hoặc <code>/create Tên dự án: Tên task</code>.</i>")
    return "\n".join(lines)


def handle_tasks_list(project_or_workspace, app_url: str = "", query_arg: str = "") -> str:
    """Handles /tasks query with flexible options: index (1, 2..), 'all' (0), project name, or identifier."""
    workspace = None
    project = None

    if isinstance(project_or_workspace, Project):
        project = project_or_workspace
        workspace = project.workspace
    else:
        workspace = project_or_workspace

    if not workspace and not project:
        return "⚠️ Không xác định được Workspace hoặc Dự án."

    all_projects = list(Project.objects.filter(workspace=workspace).order_by("name")) if workspace else ([project] if project else [])
    query_arg = (query_arg or "").strip().lower()

    target_project = None
    show_all = False

    if not query_arg:
        # Default behavior with no arguments:
        if len(all_projects) == 1:
            target_project = all_projects[0]
        else:
            show_all = True
    elif query_arg in ["0", "all", "tat ca", "tất cả", "all projects"]:
        show_all = True
    elif query_arg.isdigit():
        idx = int(query_arg)
        if idx == 0:
            show_all = True
        elif 1 <= idx <= len(all_projects):
            target_project = all_projects[idx - 1]
        else:
            return f"⚠️ Chỉ số dự án không hợp lệ. Vui lòng nhập từ <code>1</code> đến <code>{len(all_projects)}</code> hoặc <code>0</code> cho tất cả."
    else:
        # Try matching by identifier or name
        for proj in all_projects:
            if proj.identifier.lower() == query_arg or proj.name.lower() == query_arg or query_arg in proj.name.lower():
                target_project = proj
                break

    if target_project:
        issues = (
            Issue.objects.filter(project=target_project)
            .exclude(state__group__in=["completed", "cancelled"])
            .select_related("state", "project", "project__workspace")
            .order_by("-updated_at")[:15]
        )
        header_title = f"📁 <b>{escape(target_project.name)}</b> (Mã: <code>{escape(target_project.identifier)}</code>)"
    else:
        issues = (
            Issue.objects.filter(project__workspace=workspace)
            .exclude(state__group__in=["completed", "cancelled"])
            .select_related("state", "project", "project__workspace")
            .order_by("-updated_at")[:20]
        ) if workspace else Issue.objects.none()
        header_title = "🌟 <b>Tất cả các Dự án (Toàn Workspace)</b>"

    if not issues.exists():
        if target_project:
            msg = f"🎉 Dự án <b>{escape(target_project.name)}</b> hiện không có Task nào đang mở."
        else:
            msg = "🎉 Không có Task nào đang mở trên toàn bộ Workspace."
        if len(all_projects) > 1 and not query_arg:
            msg += "\n\n" + handle_projects_list(project_or_workspace, app_url)
        return msg

    lines = [f"📋 <b>Danh sách Task đang mở — {header_title}:</b>\n"]

    if len(all_projects) > 1 and show_all and not query_arg:
        lines.append("👇 <b>Nhấn để lọc theo dự án:</b>")
        for idx, p in enumerate(all_projects, 1):
            lines.append(f"  • /tasks_{idx} — 📁 <b>{escape(p.name)}</b>")
        lines.append("  • /tasks_all — 🌟 <b>Tất cả dự án</b>")
        lines.append("\n<b>--- Các Task mới nhất ---</b>")

    for issue in issues:
        proj = issue.project
        identifier = f"{proj.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        ws_slug = proj.workspace.slug if proj.workspace else "default"
        issue_url = f"{app_url}/{ws_slug}/projects/{proj.id}/issues/{issue.id}" if app_url else "#"
        lines.append(
            f"• <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)} "
            f"[<code>{escape(state_name)}</code>] (<i>{escape(proj.name)}</i>)"
        )

    return "\n".join(lines)


def handle_search_query(project_or_workspace, query_arg: str, app_url: str = "") -> str:
    """Handles /search <keyword> query across workspace or project."""
    if not query_arg:
        return "⚠️ Vui lòng nhập từ khóa tìm kiếm. Ví dụ: <code>/search login</code>"

    query_str = query_arg.strip()

    if isinstance(project_or_workspace, Project):
        workspace = project_or_workspace.workspace
        issues = Issue.objects.filter(
            project__workspace=workspace, name__icontains=query_str
        ) if workspace else Issue.objects.filter(project=project_or_workspace, name__icontains=query_str)
    else:
        workspace = project_or_workspace
        issues = Issue.objects.filter(project__workspace=workspace, name__icontains=query_str) if workspace else Issue.objects.none()

    issues = issues.select_related("state", "project", "project__workspace").order_by("-updated_at")[:10]

    if not issues.exists():
        return f"🔍 Không tìm thấy Task nào khớp với từ khóa <b>\"{escape(query_str)}\"</b> trong Workspace."

    lines = [f"🔍 <b>Kết quả tìm kiếm cho \"{escape(query_str)}\":</b>\n"]

    for issue in issues:
        proj = issue.project
        identifier = f"{proj.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        ws_slug = proj.workspace.slug if proj.workspace else "default"
        issue_url = f"{app_url}/{ws_slug}/projects/{proj.id}/issues/{issue.id}" if app_url else "#"
        lines.append(
            f"• <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)} "
            f"[<code>{escape(state_name)}</code>] (<i>{escape(proj.name)}</i>)"
        )

    return "\n".join(lines)


def handle_create_task(project_or_workspace, text_input: str, app_url: str = "") -> str:
    """Creates one or multiple tasks in Plane automatically using AI or direct text input across Workspace projects."""
    workspace = project_or_workspace.workspace if isinstance(project_or_workspace, Project) else project_or_workspace
    default_project = project_or_workspace if isinstance(project_or_workspace, Project) else (Project.objects.filter(workspace=workspace).first() if workspace else None)

    all_projects = list(Project.objects.filter(workspace=workspace).order_by("name")) if workspace else ([default_project] if default_project else [])

    if not text_input:
        proj_help = ""
        if len(all_projects) > 1:
            proj_help = "\n\n📋 <b>Các dự án khả dụng:</b>\n" + "\n".join([f"• <code>{i}</code>. {escape(p.name)} (Mã: <code>{p.identifier}</code>)" for i, p in enumerate(all_projects, 1)])

        return (
            "✨ <b>Tạo Task Tự Động bằng AI</b>\n\n"
            "Vui lòng cung cấp tên task hoặc danh sách task. Ví dụ:\n"
            "• <code>/create Thiết kế giao diện trang chủ</code>\n"
            "• <code>/create 1: Fix bug đăng nhập</code>\n"
            "• <code>/create 1. Fix bug đăng nhập\n2. Viết API báo cáo</code>"
            f"{proj_help}\n\n"
            "💡 <i>Mẹo: Bạn có thể nhập số thứ tự dự án (vd: <code>1: ...</code>) hoặc tên dự án, AI sẽ tự động phân tích và tạo từng Task vào dự án tương ứng!</i>"
        )

    if not default_project and not workspace:
        return "⚠️ Không tìm thấy dự án mặc định trong Workspace để tạo task."

    # Pre-parse explicit project index/name/identifier prefix: "1: task" or "Dự án A: task" or "CIVIX: task"
    explicit_project = None
    clean_input = text_input.strip()
    match_prefix = re.match(r"^([^:\n]+):\s*(.+)$", clean_input, re.DOTALL)
    if match_prefix and all_projects:
        prefix_str = match_prefix.group(1).strip()
        rest_text = match_prefix.group(2).strip()

        if prefix_str.isdigit():
            idx = int(prefix_str)
            if 1 <= idx <= len(all_projects):
                explicit_project = all_projects[idx - 1]
                clean_input = rest_text
        else:
            prefix_lower = prefix_str.lower()
            for p in all_projects:
                if p.identifier.lower() == prefix_lower or p.name.lower() == prefix_lower or prefix_lower in p.name.lower():
                    explicit_project = p
                    clean_input = rest_text
                    break

    proj_map = {p.identifier.upper(): p for p in all_projects if p.identifier}
    proj_info_list = [f"Chỉ số: {i+1}, Mã: {p.identifier}, Tên: {p.name}" for i, p in enumerate(all_projects)]
    proj_list_str = "; ".join(proj_info_list)

    task_items = []

    # Try AI Parsing first if LLM is configured
    api_key, model, provider, base_url = get_llm_config()
    if provider and model and (api_key or provider in ["custom", "ollama"] or base_url):
        system_prompt = (
            f"Bạn là trợ lý AI quản lý dự án cho Workspace. Các dự án hiện có trong Workspace bao gồm: [{proj_list_str}].\n"
            "Hãy phân tích đoạn văn bản hoặc danh sách công việc được cung cấp và trích xuất thành một danh sách các Task dưới dạng mảng JSON thuần túy (không kèm markdown format ```json).\n"
            "Cấu trúc JSON mỗi phần tử:\n"
            '{"name": "tên task ngắn gọn, rõ ràng", "description": "mô tả bổ sung nếu có", "priority": "urgent|high|medium|low|none", "project_identifier": "mã dự án nếu xác định được"}\n'
            "Ví dụ output mong muốn:\n"
            '[{"name": "Tạo API login", "description": "Dùng JWT auth", "priority": "high", "project_identifier": "' + (default_project.identifier if default_project else "") + '"}]'
        )
        response_text, error_msg = get_llm_response(
            task=system_prompt,
            prompt=clean_input,
            api_key=api_key,
            model=model,
            provider=provider,
            base_url=base_url,
        )
        if response_text and not error_msg:
            try:
                clean_json = response_text.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r"^```[a-zA-Z]*\n?", "", clean_json)
                    clean_json = re.sub(r"\n?```$", "", clean_json).strip()
                parsed = json.loads(clean_json)
                if isinstance(parsed, list):
                    task_items = parsed
            except Exception:
                pass

    if not task_items:
        lines = [line.strip() for line in clean_input.split("\n") if line.strip()]
        for line in lines:
            clean_name = re.sub(r"^(\d+[\.\)]|\-|•|\*)\s*", "", line).strip()
            if clean_name:
                task_items.append({"name": clean_name, "description": "", "priority": "none"})

    if not task_items:
        return "⚠️ Không thể trích xuất task nào từ văn bản đã nhập. Vui lòng thử lại!"

    created_issues = []

    for item in task_items:
        name = item.get("name")
        if not name:
            continue
        desc = item.get("description", "")
        priority = item.get("priority", "none").lower()
        if priority not in ["urgent", "high", "medium", "low", "none"]:
            priority = "none"

        # Determine target project
        target_project = explicit_project
        if not target_project:
            item_ident = (item.get("project_identifier") or "").upper()
            if item_ident in proj_map:
                target_project = proj_map[item_ident]
            else:
                target_project = default_project

        if not target_project:
            continue

        default_state = (
            State.objects.filter(project=target_project, default=True).first()
            or State.objects.filter(project=target_project, group="backlog").first()
            or State.objects.filter(project=target_project).first()
        )

        ws_for_issue = target_project.workspace or workspace

        issue = Issue.objects.create(
            name=name,
            description_html=f"<p>{escape(desc)}</p>" if desc else "<p></p>",
            project=target_project,
            workspace=ws_for_issue,
            state=default_state,
            priority=priority,
        )
        created_issues.append((issue, target_project))

    if not created_issues:
        return "⚠️ Lỗi khi tạo Task trong cơ sở dữ liệu."

    result_lines = [f"✅ <b>Đã tự động tạo thành công {len(created_issues)} Task:</b>\n"]
    for issue, proj in created_issues:
        identifier = f"{proj.identifier}-{issue.sequence_id}"
        ws_slug = proj.workspace.slug if proj.workspace else "default"
        issue_url = f"{app_url}/{ws_slug}/projects/{proj.id}/issues/{issue.id}" if app_url else "#"
        prio_icon = "🔥" if issue.priority == "urgent" else ("⚡" if issue.priority == "high" else "📌")
        result_lines.append(
            f"{prio_icon} <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)} "
            f"(<i>{escape(proj.name)}</i>)"
        )

    result_lines.append("\n💡 <i>Gõ <code>/task &lt;MÃ_TASK&gt;</code> để xem chi tiết task vừa tạo.</i>")
    return "\n".join(result_lines)

