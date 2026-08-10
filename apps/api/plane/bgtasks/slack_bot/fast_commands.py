"""
Fast Track Commands Engine for Slack Integration.
Provides direct database query handlers for fast Slack slash commands:
- /progress: Project progress report with visual progress bar and status stats
- /tasks: List active tasks assigned to the user
- /members: List project members and workload statistics
"""
from typing import Dict, Any, List
from django.db.models import Count, Q


def render_progress_bar(percentage: float, length: int = 10) -> str:
    """Render a visual ascii progress bar for Slack."""
    filled_length = int(round(length * percentage / 100))
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"`{bar}` {percentage:.1f}%"


def handle_slack_progress_command(project, workspace_slug: str) -> Dict[str, Any]:
    """
    Direct logic handler for /progress command.
    Generates a fast progress report for a given project.
    """
    from plane.db.models import Issue

    total_issues = Issue.objects.filter(project=project).count()
    if total_issues == 0:
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📊 *Project Progress: {project.name}*\nNo work items/tasks found in this project.",
                    },
                }
            ],
        }

    # Status counts
    state_counts = (
        Issue.objects.filter(project=project)
        .values("state__group")
        .annotate(count=Count("id"))
    )
    group_map = {item["state__group"]: item["count"] for item in state_counts}

    backlog_count = group_map.get("backlog", 0) + group_map.get("unstarted", 0)
    in_progress_count = group_map.get("started", 0)
    completed_count = group_map.get("completed", 0)
    cancelled_count = group_map.get("cancelled", 0)

    # Calculate completion percentage
    effective_total = total_issues - cancelled_count
    if effective_total > 0:
        completion_pct = (completed_count / effective_total) * 100
    else:
        completion_pct = 0.0

    progress_bar = render_progress_bar(completion_pct)

    # Overdue count
    from django.utils import timezone
    now = timezone.now().date()
    overdue_count = Issue.objects.filter(
        project=project,
        target_date__lt=now,
    ).exclude(state__group__in=["completed", "cancelled"]).count()

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 Progress Report: {project.name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Completion Progress:*\n{progress_bar}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Total Tasks:*\n{total_issues}"},
                {"type": "mrkdwn", "text": f"*Completed:*\n✅ {completed_count}"},
                {"type": "mrkdwn", "text": f"*In Progress:*\n🔄 {in_progress_count}"},
                {"type": "mrkdwn", "text": f"*Backlog:*\n📥 {backlog_count}"},
                {"type": "mrkdwn", "text": f"*Overdue:*\n⚠️ {overdue_count}"},
                {"type": "mrkdwn", "text": f"*Cancelled:*\n🚫 {cancelled_count}"},
            ],
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"⚡ *Fast Track Engine* | Project Code: `{project.identifier}`",
                }
            ],
        },
    ]

    return {"response_type": "in_channel", "blocks": blocks}


def handle_slack_tasks_command(project, user=None, limit: int = 5) -> Dict[str, Any]:
    """
    Direct logic handler for /tasks command.
    Retrieves active tasks for the project or assigned to user.
    """
    from plane.db.models import Issue

    qs = Issue.objects.filter(project=project).exclude(state__group__in=["completed", "cancelled"])
    if user:
        qs = qs.filter(assignees=user)

    issues = list(qs.select_related("state").prefetch_related("assignees").order_by("-updated_at")[:limit])

    if not issues:
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📋 *Tasks: {project.name}*\nNo active tasks found matching criteria.",
                    },
                }
            ],
        }

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 Active Tasks: {project.name}",
                "emoji": True,
            },
        }
    ]

    priority_emojis = {
        "urgent": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
        "none": "⚪",
    }

    for issue in issues:
        p_emoji = priority_emojis.get(str(issue.priority).lower(), "⚪")
        assignees_str = ", ".join([a.first_name or a.email for a in issue.assignees.all()]) or "Unassigned"
        state_name = issue.state.name if issue.state else "No State"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{project.identifier}-{issue.sequence_id}*: *{issue.name}*\n"
                    f"Status: `{state_name}` | Priority: {p_emoji} `{issue.priority}` | Assignee: `{assignees_str}`"
                ),
            },
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Showing top {len(issues)} active items | ⚡ Fast Track Engine",
            }
        ],
    })

    return {"response_type": "in_channel", "blocks": blocks}


def handle_slack_members_command(project) -> Dict[str, Any]:
    """
    Direct logic handler for /members command.
    Lists project members and their workload (# of active tasks).
    """
    from plane.db.models import ProjectMember, Issue

    memberships = ProjectMember.objects.filter(project=project).select_related("member")
    if not memberships.exists():
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"👥 *Members: {project.name}*\nNo members found in this project.",
                    },
                }
            ],
        }

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"👥 Project Members & Workload: {project.name}",
                "emoji": True,
            },
        }
    ]

    for pm in memberships:
        user = pm.member
        active_task_count = Issue.objects.filter(
            project=project,
            assignees=user,
        ).exclude(state__group__in=["completed", "cancelled"]).count()

        role_str = "Admin" if pm.role == 20 else "Member" if pm.role == 15 else "Guest"
        name_str = f"{user.first_name} {user.last_name}".strip() or user.email

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*• {name_str}* (`{role_str}`)\nActive Tasks Assigned: *{active_task_count}*",
            },
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": "⚡ Fast Track Engine | Workload Summary"}
        ],
    })

    return {"response_type": "in_channel", "blocks": blocks}
