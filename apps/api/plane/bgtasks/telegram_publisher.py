# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
import requests
from typing import Dict, Any, Optional
from celery import shared_task

from django.conf import settings
from plane.db.models import TelegramAutomation, Project, Issue, IssueComment

logger = logging.getLogger("plane.worker")


def send_telegram_message(bot_token: str, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """
    Sends a formatted message to a Telegram Chat ID via Telegram Bot API.
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram bot_token or chat_id missing. Notification skipped.")
        return False

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
            logger.error(f"Telegram API Error: {response_data.get('description')}")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch Telegram message: {str(e)}")
        return False


def format_issue_created_message(issue_data: Dict[str, Any], project_name: str, app_url: str = "") -> str:
    """Formats HTML message for newly created issues."""
    identifier = f"{issue_data.get('project_identifier', '')}-{issue_data.get('sequence_id', '')}"
    name = issue_data.get("name", "Untitled Issue")
    priority = issue_data.get("priority", "none").capitalize()
    state_name = issue_data.get("state_detail", {}).get("name", "Default")
    assignees = ", ".join([a.get("display_name", "") for a in issue_data.get("assignee_details", [])]) or "Unassigned"
    
    issue_url = f"{app_url}/workspaces/projects/{issue_data.get('project', '')}/issues/{issue_data.get('id', '')}" if app_url else "#"

    message = (
        f"📌 <b>New Issue in {project_name}</b>\n\n"
        f"<b><a href='{issue_url}'>[{identifier}] {name}</a></b>\n"
        f"🏷️ <b>State:</b> {state_name}\n"
        f"🔥 <b>Priority:</b> {priority}\n"
        f"👤 <b>Assignee:</b> {assignees}\n"
    )
    return message


def format_issue_updated_message(issue_data: Dict[str, Any], old_state: str, new_state: str, project_name: str) -> str:
    """Formats HTML message for issue status changes."""
    identifier = f"{issue_data.get('project_identifier', '')}-{issue_data.get('sequence_id', '')}"
    name = issue_data.get("name", "Untitled Issue")

    message = (
        f"🔄 <b>Status Update in {project_name}</b>\n\n"
        f"<b>[{identifier}] {name}</b>\n"
        f"Status changed: <code>{old_state}</code> ➔ <b>{new_state}</b>\n"
    )
    return message


def format_comment_added_message(comment_data: Dict[str, Any], issue_identifier: str, project_name: str) -> str:
    """Formats HTML message for new comments."""
    author = comment_data.get("actor_detail", {}).get("display_name", "Member")
    comment_text = comment_data.get("comment_stripped", comment_data.get("comment_html", ""))[:200]

    message = (
        f"💬 <b>New Comment in {project_name}</b>\n\n"
        f"<b>Issue [{issue_identifier}]</b>\n"
        f"<b>{author}:</b> <i>\"{comment_text}\"</i>\n"
    )
    return message


@shared_task
def dispatch_telegram_event(event_type: str, project_id: str, data: Dict[str, Any], extra_context: Optional[Dict[str, Any]] = None):
    """
    Celery task to dispatch Telegram notifications for project events.
    """
    automations = TelegramAutomation.objects.filter(project_id=project_id, is_active=True)
    if not automations.exists():
        return

    try:
        project = Project.objects.get(pk=project_id)
        project_name = project.name
    except Project.DoesNotExist:
        project_name = "Project"

    app_url = getattr(settings, "WEB_URL", "http://localhost:3000")

    for auto in automations:
        # Check event preferences if configured
        if auto.events and not auto.events.get(event_type, True):
            continue

        message_text = None

        if event_type == "issue_created":
            message_text = format_issue_created_message(data, project_name, app_url)
        elif event_type == "issue_updated" and extra_context:
            old_state = extra_context.get("old_state", "Previous")
            new_state = extra_context.get("new_state", "Current")
            message_text = format_issue_updated_message(data, old_state, new_state, project_name)
        elif event_type == "comment_added":
            issue_identifier = extra_context.get("issue_identifier", "Task") if extra_context else "Task"
            message_text = format_comment_added_message(data, issue_identifier, project_name)

        if message_text:
            send_telegram_message(auto.bot_token, auto.chat_id, message_text)
