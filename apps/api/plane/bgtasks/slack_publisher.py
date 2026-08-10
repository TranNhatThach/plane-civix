# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import os
import logging
import re
import requests
from html import unescape
from typing import Dict, Any, Optional, Tuple
from celery import shared_task

from django.conf import settings
from plane.db.models import SlackAutomation, Project, Issue, IssueComment

logger = logging.getLogger("plane.worker")


def strip_html_tags(text: str) -> str:
    """Removes HTML tags and cleans up extra whitespace for plain markdown formatting."""
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    clean = re.sub(r'<[^>]+>', '', text)
    clean = unescape(clean.strip())
    clean = re.sub(r'\n\s*\n', '\n', clean)
    return clean


def send_slack_webhook(webhook_url: str, payload: Dict[str, Any]) -> Tuple[bool, Any]:
    """
    Sends a formatted Slack Block Kit JSON payload to a Slack Incoming Webhook URL.
    Returns (success, response_text_or_error).
    """
    if not webhook_url:
        logger.warning("Slack webhook_url is missing. Notification skipped.")
        return False, "Webhook URL is missing."

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code != 200:
            err_desc = f"Slack Webhook returned HTTP {response.status_code}: {response.text}"
            logger.error(err_desc)
            return False, err_desc
        return True, response.text
    except Exception as e:
        logger.error(f"Failed to dispatch Slack webhook: {str(e)}")
        return False, str(e)


def format_slack_issue_created(issue_obj: Issue, project: Project, app_url: str = "") -> Dict[str, Any]:
    """Formats Slack Block Kit payload for newly created issues."""
    identifier = f"{project.identifier}-{issue_obj.sequence_id}"
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

    state_name = issue_obj.state.name if issue_obj.state else "No State"
    assignees = ", ".join([a.display_name for a in issue_obj.assignees.all()]) or "Unassigned"
    creator = issue_obj.created_by.display_name if issue_obj.created_by else "System"

    issue_url = ""
    if app_url and project.workspace:
        issue_url = f"{app_url.rstrip('/')}/{project.workspace.slug}/projects/{project.id}/issues/{issue_obj.id}"

    title_text = f"*{identifier}* {issue_obj.name}"
    if issue_url:
        title_text = f"*<{issue_url}|[{identifier}] {issue_obj.name}>*"

    description_snippet = strip_html_tags(issue_obj.description_html or "")
    if len(description_snippet) > 200:
        description_snippet = description_snippet[:197] + "..."

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📌 New Issue Created in {project.name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": title_text,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Project:*\n{project.name} (`{project.identifier}`)"},
                {"type": "mrkdwn", "text": f"*Status:*\n{state_name}"},
                {"type": "mrkdwn", "text": f"*Priority:*\n{priority_emoji} {priority}"},
                {"type": "mrkdwn", "text": f"*Assignee:*\n{assignees}"},
            ],
        },
    ]

    if description_snippet:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n>{description_snippet}",
            },
        })

    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"Created by *{creator}*"},
        ],
    })

    return {"blocks": blocks}


def format_slack_issue_updated(
    issue_obj: Issue,
    project: Project,
    old_state_name: str,
    new_state_name: str,
    actor_name: str = "Someone",
    app_url: str = "",
) -> Dict[str, Any]:
    """Formats Slack Block Kit payload for status updates."""
    identifier = f"{project.identifier}-{issue_obj.sequence_id}"
    issue_url = ""
    if app_url and project.workspace:
        issue_url = f"{app_url.rstrip('/')}/{project.workspace.slug}/projects/{project.id}/issues/{issue_obj.id}"

    title_text = f"*{identifier}* {issue_obj.name}"
    if issue_url:
        title_text = f"*<{issue_url}|[{identifier}] {issue_obj.name}>*"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔄 Status Update in {project.name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": title_text,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Previous State:*\n`{old_state_name}`"},
                {"type": "mrkdwn", "text": f"*New State:*\n`{new_state_name}`"},
            ],
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"Updated by *{actor_name}*"},
            ],
        },
    ]

    return {"blocks": blocks}


def format_slack_comment_added(
    issue_obj: Issue,
    project: Project,
    comment_obj: IssueComment,
    actor_name: str = "Someone",
    app_url: str = "",
) -> Dict[str, Any]:
    """Formats Slack Block Kit payload for new issue comments."""
    identifier = f"{project.identifier}-{issue_obj.sequence_id}"
    issue_url = ""
    if app_url and project.workspace:
        issue_url = f"{app_url.rstrip('/')}/{project.workspace.slug}/projects/{project.id}/issues/{issue_obj.id}"

    title_text = f"*{identifier}* {issue_obj.name}"
    if issue_url:
        title_text = f"*<{issue_url}|[{identifier}] {issue_obj.name}>*"

    comment_snippet = strip_html_tags(comment_obj.comment_html or comment_obj.comment_json or "")
    if len(comment_snippet) > 250:
        comment_snippet = comment_snippet[:247] + "..."

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"💬 New Comment in {project.name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": title_text,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{actor_name}* commented:\n>{comment_snippet}",
            },
        },
    ]

    return {"blocks": blocks}


@shared_task
def dispatch_slack_event(
    event_type: str, project_id: str, data: Dict[str, Any], extra_context: Optional[Dict[str, Any]] = None
):
    """
    Celery background task to format and post Slack notification via Webhook.
    """
    extra_context = extra_context or {}

    try:
        project = Project.objects.select_related("workspace").get(id=project_id)
    except Project.DoesNotExist:
        logger.error(f"Slack Dispatcher: Project {project_id} not found.")
        return

    # Check for Project-level Slack Automations
    automations = list(
        SlackAutomation.objects.filter(
            project_id=project_id,
            is_active=True,
        )
    )

    webhook_urls = [a.webhook_url for a in automations if a.webhook_url and a.events.get(event_type, True)]

    # Fallback to global environment variable if no active project automation found
    env_webhook = os.getenv("SLACK_WEBHOOK_URL") or getattr(settings, "SLACK_WEBHOOK_URL", "")
    if not webhook_urls and env_webhook:
        webhook_urls.append(env_webhook)

    if not webhook_urls:
        logger.info(f"Slack Dispatcher: No active Slack webhook configured for project {project_id}.")
        return

    app_url = getattr(settings, "WEB_URL", os.getenv("WEB_URL", "http://localhost:3000"))

    payload = None
    if event_type == "issue_created":
        issue_id = data.get("id")
        try:
            issue_obj = Issue.objects.select_related("state", "created_by").prefetch_related("assignees").get(id=issue_id)
            payload = format_slack_issue_created(issue_obj, project, app_url)
        except Issue.DoesNotExist:
            logger.error(f"Slack Dispatcher: Issue {issue_id} not found.")
            return

    elif event_type == "issue_updated":
        issue_id = data.get("id")
        old_state_name = extra_context.get("old_state_name", "Unknown")
        new_state_name = extra_context.get("new_state_name", "Unknown")
        actor_name = extra_context.get("actor_name", "Someone")
        try:
            issue_obj = Issue.objects.get(id=issue_id)
            payload = format_slack_issue_updated(issue_obj, project, old_state_name, new_state_name, actor_name, app_url)
        except Issue.DoesNotExist:
            logger.error(f"Slack Dispatcher: Issue {issue_id} not found.")
            return

    elif event_type == "comment_created":
        issue_id = data.get("issue_id")
        comment_id = data.get("comment_id")
        actor_name = extra_context.get("actor_name", "Someone")
        try:
            issue_obj = Issue.objects.get(id=issue_id)
            comment_obj = IssueComment.objects.get(id=comment_id)
            payload = format_slack_comment_added(issue_obj, project, comment_obj, actor_name, app_url)
        except (Issue.DoesNotExist, IssueComment.DoesNotExist) as e:
            logger.error(f"Slack Dispatcher: Comment/Issue not found: {e}")
            return

    if not payload:
        logger.warning(f"Slack Dispatcher: Unhandled event_type '{event_type}'.")
        return

    for webhook_url in webhook_urls:
        success, res = send_slack_webhook(webhook_url, payload)
        if success:
            logger.info(f"Slack notification sent successfully for event '{event_type}' to project {project.name}.")
        else:
            logger.error(f"Failed to send Slack notification for project {project.name}: {res}")
