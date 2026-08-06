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


def handle_task_query(automation: TelegramAutomation, project: Project, query_arg: str, app_url: str) -> str:
    """Handles /task <identifier> query (e.g. CIVIX-12 or 12)."""
    if not query_arg:
        return "⚠️ Vui lòng cung cấp mã Task. Ví dụ: <code>/task CIVIX-12</code> hoặc <code>/task 12</code>"

    query_arg = query_arg.strip().upper()

    match = re.search(r"(\w+)-(\d+)", query_arg)
    if match:
        proj_ident = match.group(1)
        seq_id = int(match.group(2))
        issue = (
            Issue.objects.filter(
                project__workspace=project.workspace,
                project__identifier=proj_ident,
                sequence_id=seq_id,
            )
            .select_related("state", "created_by", "project")
            .prefetch_related("assignees")
            .first()
        )
    else:
        try:
            seq_id = int(re.sub(r"\D", "", query_arg))
            issue = (
                Issue.objects.filter(
                    project=project,
                    sequence_id=seq_id,
                )
                .select_related("state", "created_by", "project")
                .prefetch_related("assignees")
                .first()
            )
        except ValueError:
            issue = None

    if not issue:
        return f"🔍 Không tìm thấy Task nào với mã <b>{escape(query_arg)}</b> trong dự án {escape(project.name)}."

    identifier = f"{issue.project.identifier}-{issue.sequence_id}"
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

    workspace_slug = project.workspace.slug if project.workspace else "default"
    issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue.id}" if app_url else "#"

    lines = [
        f"📌 <b>[{identifier}] {name}</b>\n",
        f"🏷️ <b>Trạng thái:</b> <code>{escape(state_name)}</code>",
        f"⚡ <b>Ưu tiên:</b> {priority}",
        f"👤 <b>Người thực hiện:</b> {escape(assignees_str)}",
        f"📁 <b>Dự án:</b> {escape(project.name)}",
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


def handle_tasks_list(project: Project, app_url: str) -> str:
    """Handles /tasks query to list active open tasks."""
    issues = (
        Issue.objects.filter(project=project)
        .exclude(state__group__in=["completed", "cancelled"])
        .select_related("state")
        .order_by("-updated_at")[:10]
    )

    if not issues.exists():
        return f"🎉 Dự án <b>{escape(project.name)}</b> không có Task nào đang mở!"

    workspace_slug = project.workspace.slug if project.workspace else "default"
    lines = [f"📋 <b>Danh sách Task đang mở ({escape(project.name)}):</b>\n"]

    for issue in issues:
        identifier = f"{project.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue.id}" if app_url else "#"
        lines.append(f"• <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)} [<code>{escape(state_name)}</code>]")

    return "\n".join(lines)


def handle_search_query(project: Project, query_arg: str, app_url: str) -> str:
    """Handles /search <keyword> query."""
    if not query_arg:
        return "⚠️ Vui lòng nhập từ khóa tìm kiếm. Ví dụ: <code>/search login</code>"

    issues = (
        Issue.objects.filter(project=project, name__icontains=query_arg.strip())
        .select_related("state")
        .order_by("-updated_at")[:8]
    )

    if not issues.exists():
        return f"🔍 Không tìm thấy Task nào khớp với từ khóa <b>\"{escape(query_arg)}\"</b>."

    workspace_slug = project.workspace.slug if project.workspace else "default"
    lines = [f"🔍 <b>Kết quả tìm kiếm cho \"{escape(query_arg)}\":</b>\n"]

    for issue in issues:
        identifier = f"{project.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue.id}" if app_url else "#"
        lines.append(f"• <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)} [<code>{escape(state_name)}</code>]")

    return "\n".join(lines)


def handle_create_task(project: Project, text_input: str, app_url: str) -> str:
    """Creates one or multiple tasks in Plane automatically using AI or direct text input."""
    if not text_input:
        return (
            "✨ <b>Tạo Task Tự Động bằng AI</b>\n\n"
            "Vui lòng cung cấp tên task hoặc danh sách task. Ví dụ:\n"
            "• <code>/create Thiết kế giao diện trang chủ</code>\n"
            "• <code>/create 1. Fix bug đăng nhập\n2. Viết API báo cáo\n3. Kiểm thử Telegram bot</code>\n\n"
            "💡 <i>Mẹo: Bạn có thể dán cả danh sách công việc/ghi chú cuộc họp, AI sẽ tự động phân tích và tạo từng Task!</i>"
        )

    default_state = (
        State.objects.filter(project=project, default=True).first()
        or State.objects.filter(project=project, group="backlog").first()
        or State.objects.filter(project=project).first()
    )

    task_items = []

    # Try AI Parsing first if LLM is configured
    api_key, model, provider, base_url = get_llm_config()
    if provider and model and (api_key or provider in ["custom", "ollama"] or base_url):
        system_prompt = (
            "Bạn là trợ lý AI quản lý dự án. Hãy phân tích đoạn văn bản hoặc danh sách công việc được cung cấp "
            "và trích xuất thành một danh sách các Task dưới dạng mảng JSON thuần túy (không kèm markdown format ```json).\n"
            "Cấu trúc JSON mỗi phần tử:\n"
            '{"name": "tên task ngắn gọn, rõ ràng", "description": "mô tả bổ sung nếu có", "priority": "urgent|high|medium|low|none"}\n'
            "Ví dụ output mong muốn:\n"
            '[{"name": "Tạo API login", "description": "Dùng JWT auth", "priority": "high"}, {"name": "Test UI", "description": "", "priority": "medium"}]'
        )
        response_text, error_msg = get_llm_response(
            task=system_prompt,
            prompt=text_input,
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
        lines = [line.strip() for line in text_input.split("\n") if line.strip()]
        for line in lines:
            clean_name = re.sub(r"^(\d+[\.\)]|\-|•|\*)\s*", "", line).strip()
            if clean_name:
                task_items.append({"name": clean_name, "description": "", "priority": "none"})

    if not task_items:
        return "⚠️ Không thể trích xuất task nào từ văn bản đã nhập. Vui lòng thử lại!"

    created_issues = []
    workspace_slug = project.workspace.slug if project.workspace else "default"

    for item in task_items:
        name = item.get("name")
        if not name:
            continue
        desc = item.get("description", "")
        priority = item.get("priority", "none").lower()
        if priority not in ["urgent", "high", "medium", "low", "none"]:
            priority = "none"

        issue = Issue.objects.create(
            name=name,
            description_html=f"<p>{escape(desc)}</p>" if desc else "<p></p>",
            project=project,
            workspace=project.workspace,
            state=default_state,
            priority=priority,
        )
        created_issues.append(issue)

    if not created_issues:
        return "⚠️ Lỗi khi tạo Task trong cơ sở dữ liệu."

    result_lines = [f"✅ <b>Đã tự động tạo thành công {len(created_issues)} Task vào dự án {escape(project.name)}:</b>\n"]
    for issue in created_issues:
        identifier = f"{project.identifier}-{issue.sequence_id}"
        issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue.id}" if app_url else "#"
        prio_icon = "🔥" if issue.priority == "urgent" else ("⚡" if issue.priority == "high" else "📌")
        result_lines.append(f"{prio_icon} <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)}")

    result_lines.append("\n💡 <i>Bạn có thể gõ <code>/task &lt;MÃ_TASK&gt;</code> để xem chi tiết task vừa tạo.</i>")
    return "\n".join(result_lines)
