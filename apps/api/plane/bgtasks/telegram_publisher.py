# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
import re
import requests
from html import escape, unescape
from typing import Dict, Any, Optional
from celery import shared_task

from django.conf import settings
from plane.db.models import TelegramAutomation, Project, Issue, IssueComment

logger = logging.getLogger("plane.worker")


import threading

def send_telegram_message(bot_token: str, chat_id: str, text: str, parse_mode: str = "HTML") -> tuple[bool, Any]:
    """
    Sends a formatted message to a Telegram Chat ID via Telegram Bot API.
    Returns (success, response_dict_or_error_string).
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram bot_token or chat_id missing. Notification skipped.")
        return False, "Bot Token or Chat ID is missing."

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response_data = response.json()
        if not response_data.get("ok"):
            err_desc = response_data.get("description", "Unknown Telegram API error")
            logger.error(f"Telegram API Error: {err_desc}")
            return False, err_desc
        return True, response_data
    except Exception as e:
        logger.error(f"Failed to dispatch Telegram message: {str(e)}")
        return False, str(e)


def delete_telegram_message(bot_token: str, chat_id: str, message_id: int) -> bool:
    """Deletes a message in a Telegram chat by message_id."""
    if not bot_token or not chat_id or not message_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
        payload = {"chat_id": chat_id, "message_id": message_id}
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Failed to delete Telegram message {message_id}: {e}")
        return False


def schedule_auto_delete(bot_token: str, chat_id: str, message_ids: list, delay_seconds: float = 45.0):
    """Schedules auto-deletion of telegram messages after delay_seconds."""
    def _delete_job():
        for msg_id in message_ids:
            if msg_id:
                delete_telegram_message(bot_token, chat_id, msg_id)

    timer = threading.Timer(delay_seconds, _delete_job)
    timer.daemon = True
    timer.start()


def strip_html_tags(text: str) -> str:
    if not text:
        return ""
    # Replace line breaks and paragraphs
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Trim multiple empty newlines
    clean = unescape(clean.strip())
    clean = re.sub(r'\n\s*\n', '\n', clean)
    return clean


def format_issue_created_message(issue_obj: Issue, project: Project, app_url: str = "") -> str:
    """Formats HTML message for newly created issues with rich details."""
    identifier = f"{project.identifier}-{issue_obj.sequence_id}"
    name = escape(issue_obj.name)
    priority = (issue_obj.priority or "none").capitalize()

    priority_emoji = "⚪"
    if priority.lower() == "urgent":
        priority_emoji = "🔴"
    elif priority.lower() == "high":
        priority_emoji = "🟠"
    elif priority.lower() == "medium":
        priority_emoji = "🟡"
    elif priority.lower() == "low":
        priority_emoji = "🔵"

    state_name = issue_obj.state.name if issue_obj.state else "Backlog"

    assignees_list = [a.display_name for a in issue_obj.assignees.all() if a.display_name]
    assignees_str = ", ".join(assignees_list) if assignees_list else "Unassigned"

    creator_name = issue_obj.created_by.display_name if issue_obj.created_by else "Member"

    desc_clean = strip_html_tags(issue_obj.description_html or "")
    if len(desc_clean) > 250:
        desc_clean = desc_clean[:247] + "..."

    workspace_slug = project.workspace.slug if project.workspace else "default"
    issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue_obj.id}" if app_url else "#"

    msg_lines = [
        f"📌 <b>[{identifier}] New Task Created</b>",
        f"📁 <b>Project:</b> {escape(project.name)}",
        f"📝 <b>Title:</b> <b>{name}</b>",
        f"🏷️ <b>Status:</b> <code>{escape(state_name)}</code>",
        f"{priority_emoji} <b>Priority:</b> {priority}",
        f"👤 <b>Assignee:</b> {escape(assignees_str)}",
        f"✍️ <b>Created By:</b> {escape(creator_name)}",
    ]

    if desc_clean:
        msg_lines.append(f"\n📖 <b>Description:</b>\n<i>{escape(desc_clean)}</i>")

    msg_lines.append(f"\n🔗 <a href='{issue_url}'>View Task in Plane</a>")

    return "\n".join(msg_lines)


def format_issue_updated_message(issue_obj: Issue, project: Project, old_state: str, new_state: str, actor_name: str = "Member", app_url: str = "") -> str:
    """Formats HTML message for issue status changes."""
    identifier = f"{project.identifier}-{issue_obj.sequence_id}"
    name = escape(issue_obj.name)
    workspace_slug = project.workspace.slug if project.workspace else "default"
    issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue_obj.id}" if app_url else "#"

    message = (
        f"🔄 <b>[{identifier}] Status Changed</b>\n\n"
        f"📁 <b>Project:</b> {escape(project.name)}\n"
        f"📝 <b>Task:</b> <b>{name}</b>\n"
        f"👤 <b>Updated By:</b> {escape(actor_name)}\n"
        f"🔀 <b>Status:</b> <code>{escape(old_state)}</code> ➔ <b><code>{escape(new_state)}</code></b>\n\n"
        f"🔗 <a href='{issue_url}'>View Task in Plane</a>"
    )
    return message


def format_comment_added_message(comment_data: Dict[str, Any], issue_obj: Issue, project: Project, app_url: str = "") -> str:
    """Formats HTML message for new comments."""
    identifier = f"{project.identifier}-{issue_obj.sequence_id}"
    name = escape(issue_obj.name)

    author = comment_data.get("actor_detail", {}).get("display_name", "Member")
    comment_text_raw = comment_data.get("comment_html", "") or comment_data.get("comment_json", "") or comment_data.get("comment_stripped", "")
    comment_clean = strip_html_tags(str(comment_text_raw))
    if len(comment_clean) > 250:
        comment_clean = comment_clean[:247] + "..."

    workspace_slug = project.workspace.slug if project.workspace else "default"
    issue_url = f"{app_url}/{workspace_slug}/projects/{project.id}/issues/{issue_obj.id}" if app_url else "#"

    message = (
        f"💬 <b>[{identifier}] New Comment</b>\n\n"
        f"📁 <b>Project:</b> {escape(project.name)}\n"
        f"📝 <b>Task:</b> <b>{name}</b>\n"
        f"👤 <b>Author:</b> {escape(author)}\n\n"
        f"💬 <b>Content:</b>\n<i>\"{escape(comment_clean)}\"</i>\n\n"
        f"🔗 <a href='{issue_url}'>View Task in Plane</a>"
    )
    return message


@shared_task
def dispatch_telegram_event(event_type: str, project_id: str, data: Dict[str, Any], extra_context: Optional[Dict[str, Any]] = None):
    """
    Celery task to dispatch Telegram notifications for project events.
    """
    from django.db.models import Q

    if extra_context and extra_context.get("skip_telegram_notify"):
        return

    try:
        project = Project.objects.select_related("workspace").get(pk=project_id)
        workspace_id = project.workspace_id
    except Project.DoesNotExist:
        return

    if workspace_id:
        automations = TelegramAutomation.objects.filter(
            Q(project_id=project_id) | Q(workspace_id=workspace_id),
            is_active=True,
        )
    else:
        automations = TelegramAutomation.objects.filter(project_id=project_id, is_active=True)

    if not automations.exists():
        return

    app_url = (getattr(settings, "WEB_URL", None) or os.environ.get("WEB_URL") or "http://localhost:3000").rstrip("/")

    # Retrieve issue object from DB for complete data
    issue_id = data.get("id") or (extra_context.get("issue_id") if extra_context else None)
    issue_obj = None
    if issue_id:
        issue_obj = (
            Issue.objects.filter(pk=issue_id)
            .select_related("state", "created_by", "project")
            .prefetch_related("assignees")
            .first()
        )

    sent_targets = set()

    for auto in automations:
        target_key = (auto.bot_token, auto.chat_id)
        if target_key in sent_targets:
            continue

        if auto.events and not auto.events.get(event_type, True):
            continue

        message_text = None

        if event_type == "issue_created":
            if issue_obj:
                message_text = format_issue_created_message(issue_obj, project, app_url)
            else:
                message_text = f"📌 <b>New Task in {escape(project.name)}</b>: {escape(data.get('name', ''))}"

        elif event_type == "issue_updated" and extra_context:
            old_state = extra_context.get("old_state", "Previous")
            new_state = extra_context.get("new_state", "Current")
            actor_name = extra_context.get("actor_name", "Member")
            if issue_obj:
                message_text = format_issue_updated_message(issue_obj, project, old_state, new_state, actor_name, app_url)
            else:
                identifier = f"{project.identifier}-{data.get('sequence_id', '')}"
                message_text = f"🔄 <b>[{identifier}] Status Changed</b> by {escape(actor_name)}: <code>{escape(old_state)}</code> ➔ <b>{escape(new_state)}</b>"

        elif event_type == "comment_added":
            if issue_obj:
                message_text = format_comment_added_message(data, issue_obj, project, app_url)
            else:
                message_text = f"💬 <b>New Comment in {escape(project.name)}</b>"

        if message_text:
            success, _ = send_telegram_message(auto.bot_token, auto.chat_id, message_text)
            if success:
                sent_targets.add(target_key)
