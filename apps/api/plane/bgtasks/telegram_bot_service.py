# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
import re
from html import escape
from typing import Dict, Any, Optional

from django.conf import settings
from plane.db.models import TelegramAutomation, Project, Issue, IssueComment
from plane.bgtasks.telegram_publisher import send_telegram_message, strip_html_tags
from plane.app.views.external.base import get_llm_config, get_llm_response

logger = logging.getLogger("plane.worker")


def get_project_and_automation(chat_id: str) -> tuple[Optional[TelegramAutomation], Optional[Project]]:
    """Retrieves active TelegramAutomation & Project for the given Telegram chat_id."""
    str_chat_id = str(chat_id)
    automation = (
        TelegramAutomation.objects.filter(chat_id=str_chat_id, is_active=True)
        .select_related("project", "workspace")
        .first()
    )
    if not automation:
        # Fallback: check without minus sign or with minus sign for group chat IDs
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

    # Check if query format is PROJECT-SEQ (e.g. CIVIX-12)
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
        # Try numeric sequence_id in current project
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

    # Fetch top 3 recent comments
    comments = (
        IssueComment.objects.filter(issue=issue)
        .select_related("actor")
        .order_by("-created_at")[:3]
    )

    workspace_slug = project.workspace.slug if project.workspace else "default"
    issue_url = f"{app_url}/{workspace_slug}/projects/{issue.project.id}/issues/{issue.id}" if app_url else "#"

    msg_lines = [
        f"📌 <b>[{identifier}] {name}</b>",
        f"📁 <b>Dự án:</b> {escape(issue.project.name)}",
        f"🏷️ <b>Trạng thái:</b> <code>{escape(state_name)}</code>",
        f"⚡ <b>Ưu tiên:</b> {priority}",
        f"👤 <b>Người phụ trách:</b> {escape(assignees_str)}",
    ]

    if desc_clean:
        msg_lines.append(f"\n📖 <b>Mô tả:</b>\n<i>{escape(desc_clean)}</i>")

    if comments.exists():
        msg_lines.append("\n💬 <b>Bình luận gần nhất:</b>")
        for c in reversed(list(comments)):
            c_author = c.actor.display_name if c.actor else "Thành viên"
            c_text = strip_html_tags(c.comment_html or c.comment_json or "")
            if len(c_text) > 100:
                c_text = c_text[:97] + "..."
            msg_lines.append(f"• <b>{escape(c_author)}</b>: <i>\"{escape(c_text)}\"</i>")

    msg_lines.append(f"\n🔗 <a href='{issue_url}'>Xem Task trên Plane</a>")
    return "\n".join(msg_lines)


def handle_tasks_list(project: Project, app_url: str) -> str:
    """Lists top 10 open/active tasks in project."""
    issues = (
        Issue.objects.filter(project=project)
        .exclude(state__group__in=["completed", "cancelled"])
        .select_related("state")
        .order_by("-updated_at")[:10]
    )

    if not issues.exists():
        return f"🎉 Dự án <b>{escape(project.name)}</b> hiện không có Task nào đang mở!"

    workspace_slug = project.workspace.slug if project.workspace else "default"
    lines = [f"📋 <b>Danh sách Task đang mở ({escape(project.name)}):</b>\n"]

    for issue in issues:
        identifier = f"{project.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue.id}" if app_url else "#"
        lines.append(f"• <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)} [<code>{escape(state_name)}</code>]")

    lines.append(f"\n💡 <i>Gõ <code>/task &lt;mã&gt;</code> để xem chi tiết task.</i>")
    return "\n".join(lines)


def handle_search_query(project: Project, keyword: str, app_url: str) -> str:
    """Searches tasks in project by keyword."""
    if not keyword:
        return "⚠️ Vui lòng nhập từ khóa tìm kiếm. Ví dụ: <code>/search telegram</code>"

    issues = (
        Issue.objects.filter(project=project, name__icontains=keyword)
        .select_related("state")
        .order_by("-updated_at")[:7]
    )

    if not issues.exists():
        return f"🔍 Không tìm thấy Task nào khớp với từ khóa <b>\"{escape(keyword)}\"</b> trong dự án {escape(project.name)}."

    workspace_slug = project.workspace.slug if project.workspace else "default"
    lines = [f"🔍 <b>Kết quả tìm kiếm cho \"{escape(keyword)}\" ({len(issues)} tasks):</b>\n"]

    for issue in issues:
        identifier = f"{project.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue.id}" if app_url else "#"
        lines.append(f"• <a href='{issue_url}'><b>{identifier}</b></a>: {escape(issue.name)} [<code>{escape(state_name)}</code>]")

    return "\n".join(lines)


def handle_project_summary(project: Project) -> str:
    """Generates project progress report & state breakdown."""
    total_issues = Issue.objects.filter(project=project).count()
    if total_issues == 0:
        return f"📊 Dự án <b>{escape(project.name)}</b> chưa có Task nào."

    completed_count = Issue.objects.filter(project=project, state__group="completed").count()
    started_count = Issue.objects.filter(project=project, state__group="started").count()
    unstarted_count = Issue.objects.filter(project=project, state__group="unstarted").count()
    backlog_count = Issue.objects.filter(project=project, state__group="backlog").count()
    cancelled_count = Issue.objects.filter(project=project, state__group="cancelled").count()

    completion_rate = int((completed_count / total_issues) * 100) if total_issues > 0 else 0
    filled = int(completion_rate / 10)
    progress_bar = "▓" * filled + "░" * (10 - filled)

    lines = [
        f"📊 <b>Báo cáo Tiến độ Dự án: {escape(project.name)}</b>\n",
        f"📈 <b>Tiến độ:</b> <code>{progress_bar}</code> <b>{completion_rate}%</b>",
        f"📦 <b>Tổng số Task:</b> {total_issues}\n",
        f"• ✅ <b>Hoàn thành (Completed):</b> {completed_count}",
        f"• 🔄 <b>Đang thực hiện (In Progress):</b> {started_count}",
        f"• ⏳ <b>Chưa bắt đầu (Todo):</b> {unstarted_count}",
        f"• 📥 <b>Backlog:</b> {backlog_count}",
        f"• 🚫 <b>Đã hủy (Cancelled):</b> {cancelled_count}",
    ]
    return "\n".join(lines)


def handle_ai_ask(project: Project, question: str) -> str:
    """Invokes God Mode AI configuration to answer natural questions about the project."""
    if not question:
        return "🤖 Bạn có thể hỏi tôi bất cứ điều gì về dự án! Ví dụ: <code>/ask Tiến độ dự án hiện tại thế nào?</code>"

    # Get LLM Config from God Mode / Instance Config
    api_key, model, provider, base_url = get_llm_config()

    # Build Project Context
    recent_issues = (
        Issue.objects.filter(project=project)
        .select_related("state")
        .prefetch_related("assignees")
        .order_by("-updated_at")[:15]
    )

    issue_context_lines = []
    for issue in recent_issues:
        identifier = f"{project.identifier}-{issue.sequence_id}"
        state_name = issue.state.name if issue.state else "Backlog"
        assignees = ", ".join([a.display_name for a in issue.assignees.all() if a.display_name]) or "Unassigned"
        issue_context_lines.append(f"- {identifier}: {issue.name} | Status: {state_name} | Assignee: {assignees}")

    context_str = "\n".join(issue_context_lines)

    system_prompt = (
        f"Bạn là Trợ lý AI Telegram cho dự án '{project.name}' (Mã dự án: {project.identifier}).\n"
        f"Dưới đây là thông tin thực tế về các Task gần đây trong dự án:\n"
        f"{context_str}\n\n"
        f"Hãy trả lời câu hỏi của người dùng một cách ngắn gọn, chính xác, lịch sự bằng tiếng Việt (hoặc ngôn ngữ người dùng hỏi). "
        f"Sử dụng định dạng HTML Telegram đơn giản (dùng <b>, <i>, <code>) nếu cần."
    )

    if not provider or not model or (not api_key and provider not in ["custom", "ollama"] and not base_url):
        return (
            f"🤖 <b>Plane AI Assistant</b>\n\n"
            f"⚠️ AI trong God Mode chưa được cấu hình API Key hoặc Provider.\n"
            f"Vui lòng vào <b>God Mode / Admin Settings ➔ AI Configuration</b> để thiết lập LLM API Key."
        )

    response_text, error_msg = get_llm_response(
        task=system_prompt,
        prompt=question,
        api_key=api_key,
        model=model,
        provider=provider,
        base_url=base_url,
    )

    if error_msg:
        return f"⚠️ <b>Lỗi kết nối AI ({provider}):</b> {escape(error_msg)}"

    return f"🤖 <b>Plane AI Assistant ({model}):</b>\n\n{response_text}"


def process_telegram_update(update_data: Dict[str, Any]) -> None:
    """Processes incoming Telegram webhook update."""
    message = update_data.get("message") or update_data.get("channel_post")
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    chat_type = chat.get("type", "private")
    text = (message.get("text") or "").strip()

    if not text:
        return

    automation, project = get_project_and_automation(chat_id)
    bot_token = automation.bot_token if automation else None

    # Check if bot should respond in group / channel
    is_private = chat_type == "private"
    is_reply_to_bot = message.get("reply_to_message", {}).get("from", {}).get("is_bot", False)
    is_mentioned = False

    # Clean text if bot username mentioned e.g. /task@CivixBot
    bot_name = ""
    if "@" in text:
        parts = text.split("@")
        if len(parts) > 1:
            bot_name = parts[1].split()[0]
            is_mentioned = True
            text = text.replace(f"@{bot_name}", "").strip()

    is_command = text.startswith("/")

    # If not private, reply to bot, mentioned, or command, ignore to avoid spamming groups
    if not (is_private or is_command or is_mentioned or is_reply_to_bot):
        return

    if not automation or not project:
        if is_command or is_private:
            fallback_msg = (
                "⚠️ <b>Telegram Bot chưa được liên kết với Dự án Plane nào!</b>\n\n"
                "Vui lòng vào Plane Web App ➔ <b>Cài đặt Dự án ➔ Integrations ➔ Telegram</b> để cấu hình Bot Token và Chat ID này."
            )
            if bot_token:
                send_telegram_message(bot_token, chat_id, fallback_msg)
        return

    app_url = (getattr(settings, "WEB_URL", None) or "http://localhost:3000").rstrip("/")

    cmd_part = text.split()[0].lower() if text else ""
    arg_part = text[len(cmd_part):].strip() if len(text) > len(cmd_part) else ""

    if cmd_part in ["/start", "/help"]:
        reply_text = (
            "🤖 <b>Plane Telegram Assistant</b>\n\n"
            "Tôi có thể giúp bạn tra cứu thông tin dự án & hỏi đáp AI:\n\n"
            "• <code>/task &lt;MÃ_TASK&gt;</code>: Xem chi tiết task (vd: <code>/task CIVIX-12</code>)\n"
            "• <code>/tasks</code>: Xem danh sách các task đang mở\n"
            "• <code>/search &lt;từ khóa&gt;</code>: Tìm kiếm task theo từ khóa\n"
            "• <code>/summary</code> hoặc <code>/status</code>: Báo cáo tổng quan tiến độ dự án\n"
            "• <code>/ask &lt;câu hỏi&gt;</code>: Hỏi đáp AI bằng ngôn ngữ tự nhiên\n"
        )
    elif cmd_part == "/task":
        reply_text = handle_task_query(automation, project, arg_part, app_url)
    elif cmd_part == "/tasks":
        reply_text = handle_tasks_list(project, app_url)
    elif cmd_part == "/search":
        reply_text = handle_search_query(project, arg_part, app_url)
    elif cmd_part in ["/summary", "/status"]:
        reply_text = handle_project_summary(project)
    elif cmd_part == "/ask":
        reply_text = handle_ai_ask(project, arg_part)
    elif is_command and re.match(r"^/[a-zA-Z0-9]+-\d+$", cmd_part):
        task_id = cmd_part[1:]
        reply_text = handle_task_query(automation, project, task_id, app_url)
    elif re.match(r"^[a-zA-Z0-9]+-\d+$", text):
        reply_text = handle_task_query(automation, project, text, app_url)
    else:
        reply_text = handle_ai_ask(project, text)

    send_telegram_message(automation.bot_token, chat_id, reply_text)
