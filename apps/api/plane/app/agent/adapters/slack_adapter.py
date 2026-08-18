import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def get_app_url() -> str:
    """Gets the public frontend web application URL."""
    url = getattr(settings, "WEB_URL", None) or os.environ.get("WEB_URL") or "http://localhost:3000"
    return url.rstrip("/")


def build_plane_url(
    app_url: str = "",
    workspace_slug: str = "",
    project_id: str = "",
    issue_id: str = "",
) -> str:
    """Builds a contextual URL to Plane web application."""
    base = (app_url or get_app_url()).rstrip("/")
    if workspace_slug and project_id and issue_id:
        return f"{base}/{workspace_slug}/projects/{project_id}/issues/{issue_id}"
    elif workspace_slug and project_id:
        return f"{base}/{workspace_slug}/projects/{project_id}/issues"
    elif workspace_slug:
        return f"{base}/{workspace_slug}"
    return base


def render_slack_block_kit(
    agent_result: Dict[str, Any],
    user_name: str = "",
    app_url: str = "",
    workspace_slug: str = "",
    project_id: str = "",
) -> Dict[str, Any]:
    """
    Adapts standardized JSON results from Plane Core Agent Engine
    into rich, interactive, high-aesthetic Slack Block Kit Cards.
    """
    action = agent_result.get("action_taken", "")
    text = agent_result.get("text", "")
    data = agent_result.get("data", {})
    user_str = f"@{user_name}" if user_name else "bạn"

    # Contextual URL targets
    eff_app_url = app_url or get_app_url()
    eff_ws_slug = workspace_slug or data.get("workspace_slug", "")
    eff_proj_id = project_id or data.get("project_id", "")
    eff_task_id = data.get("task_id", "")

    # Default fallback Slack Block Card
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🤖 Plane Core AI Assistant", "emoji": True},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"⚡ *Plane Core AI Agent* • Đã phục vụ {user_str} • Dữ liệu real-time"}
            ],
        },
    ]

    # Render System LLM Chat Card
    if action in ["system_llm_chat", "llm_chat"]:
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🤖 Plane Core AI Assistant", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"⚡ *Plane Core AI Agent* • Đã phục vụ {user_str}"}
                ],
            },
        ]
    elif action == "system_llm_error":
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "⚠️ System LLM Alert", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🤖 *Plane Core AI Agent* • Vui lòng kiểm tra lại cấu hình AI Settings"}
                ],
            },
        ]

    # Render Progress Bar Card
    elif action == "tool_get_progress" and data:
        pct = data.get("completion_percentage", 0)
        filled = int(pct / 10)
        bar = "▓" * filled + "░" * (10 - filled)
        proj_name = data.get("project_name", "Dự án")
        status_emoji = "🟢" if pct >= 70 else ("🟡" if pct >= 30 else "🔴")

        progress_target_url = build_plane_url(
            app_url=eff_app_url,
            workspace_slug=eff_ws_slug,
            project_id=eff_proj_id,
        )

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📊 Báo Cáo Tiến Độ Dự Án: {proj_name}", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{status_emoji} Tiến độ tổng quan:* `{bar}` *{pct}%*\n"
                        f"_{data.get('completed_tasks', 0)} / {data.get('total_tasks', 0)} công việc đã hoàn thành_"
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*✅ Đã hoàn thành:*\n`{data.get('completed_tasks', 0)} tasks`"},
                    {"type": "mrkdwn", "text": f"*🏃 Đang thực hiện:*\n`{data.get('started_tasks', 0)} tasks`"},
                    {"type": "mrkdwn", "text": f"*📥 Trong Backlog:*\n`{data.get('backlog_tasks', 0)} tasks`"},
                    {"type": "mrkdwn", "text": f"*🚨 Đã quá hạn:*\n`{data.get('overdue_tasks', 0)} tasks`"},
                ],
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🌐 Mở trên Plane Web", "emoji": True},
                        "url": progress_target_url,
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📋 Xem danh sách Task", "emoji": True},
                        "value": "view_tasks",
                        "action_id": "agent_view_tasks_action",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🤖 *Plane AI Agent* • Báo cáo được yêu cầu bởi {user_str}"}
                ],
            },
        ]

    # Render Projects List Card
    elif action == "tool_list_projects" and data:
        projects = data.get("projects", [])
        fields = []
        for p in projects:
            fields.append({
                "type": "mrkdwn",
                "text": f"📁 *{p['name']}* (`{p['identifier']}`)\n`{p['total_issues']} tasks` | `{p['members_count']} thành viên`",
            })

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📁 Danh Sách Dự Án ({len(projects)} Projects)", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": fields[:10] if fields else [{"type": "mrkdwn", "text": "Không có dự án nào."}],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🤖 *Plane Core AI Agent* • Danh sách dự án trên hệ thống Plane"}
                ],
            },
        ]

    # Render Tasks List Card
    elif action == "tool_query_tasks" and data:
        tasks = data.get("tasks", [])
        tasks_target_url = build_plane_url(
            app_url=eff_app_url,
            workspace_slug=eff_ws_slug,
            project_id=eff_proj_id,
        )

        if not tasks:
            msg_text = text if text else "🎉 *Hiện tại không có công việc nào thỏa mãn điều kiện tìm kiếm!*"
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "📋 Danh Sách Công Việc", "emoji": True},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": msg_text},
                },
            ]
        else:
            task_lines = []
            for t in tasks:
                p_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(t.get("priority", "").lower(), "⚪")
                assignee = f" ➔ @{t['assignees'][0]}" if t.get("assignees") else ""
                due = f" | 🗓️ {t['target_date']}" if t.get("target_date") else ""
                task_lines.append(f"• {p_emoji} *[{t['key']}] {t['name']}* (`{t['status']}`){assignee}{due}")

            task_sections = []
            curr_str = ""
            for line in task_lines:
                if len(curr_str) + len(line) + 1 > 2500:
                    task_sections.append({"type": "section", "text": {"type": "mrkdwn", "text": curr_str}})
                    curr_str = line
                else:
                    curr_str = (curr_str + "\n" + line).strip()
            if curr_str:
                task_sections.append({"type": "section", "text": {"type": "mrkdwn", "text": curr_str}})

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"📋 Quản Lý Công Việc — Tất Cả {data.get('total_matched', len(tasks))} Task Active", "emoji": True},
                },
                {"type": "divider"},
            ]
            blocks.extend(task_sections)
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "➕ Tạo Task Mới", "emoji": True},
                            "url": tasks_target_url,
                            "style": "primary",
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📊 Xem Báo Cáo Tiến Độ", "emoji": True},
                            "value": "view_progress",
                            "action_id": "agent_view_progress_action",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"🤖 *Plane Core AI Agent* • Đang hiển thị tất cả {len(tasks)} / {data.get('total_matched', len(tasks))} công việc"}
                    ],
                },
            ])

    # Render Members Workload Card
    elif action == "tool_get_members_workload" and data:
        members = data.get("members", [])
        proj_name = data.get("project_name", "Dự án")

        fields = []
        for m in members:
            fields.append({
                "type": "mrkdwn",
                "text": (
                    f"👤 *{m['display_name']}* ({m['email']})\n"
                    f"🏃 Đang làm: `{m['in_progress']}` | ✅ Đã xong: `{m['completed']}` | 📌 Tổng: `{m['total_assigned']}`"
                ),
            })

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"👥 Tải Công Việc Thành Viên — Dự Án {proj_name}", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Thống kê phân bổ công việc của *{len(members)} thành viên* trong team:"},
            },
            {
                "type": "section",
                "fields": fields[:10],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🤖 *Plane Core AI Agent* • Phân bổ Workload được yêu cầu bởi {user_str}"}
                ],
            },
        ]

    # Render Task Creation Confirmation Card
    elif action == "tool_create_task_with_subtasks" and data:
        subtasks = data.get("subtasks", [])
        sub_lines = [f"• ▫️ *[{s['key']}] {s['title']}*" for s in subtasks]
        sub_str = "\n".join(sub_lines) if sub_lines else "Không có sub-task"

        task_target_url = build_plane_url(
            app_url=eff_app_url,
            workspace_slug=eff_ws_slug,
            project_id=eff_proj_id,
            issue_id=eff_task_id,
        )

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "✨ Khởi Tạo Công Việc Thành Công!", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*📌 Mã Task:*\n`{data.get('task_key')}`"},
                    {"type": "mrkdwn", "text": f"*👤 Người gán:*\n`@{data.get('assignee')}`"},
                    {"type": "mrkdwn", "text": f"*🎯 Tiêu đề:*\n*{data.get('title')}*"},
                    {"type": "mrkdwn", "text": f"*⚡ Ưu tiên:*\n`{data.get('priority', 'medium').upper()}`"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*📂 Danh sách Task Con (Sub-tasks):*\n{sub_str}"},
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔗 Mở Task Trên Web", "emoji": True},
                        "url": task_target_url,
                        "style": "primary",
                    }
                ],
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🤖 *Plane Core AI Agent* • Khởi tạo thành công cho {user_str}"}
                ],
            },
        ]

    if agent_result.get("requires_confirmation"):
        pending = agent_result.get("pending_action", {})
        action_type = pending.get("type", "confirm")
        target_proj_id = pending.get("project_id", "") or eff_proj_id

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ Xác nhận thực hiện", "emoji": True},
                    "style": "primary",
                    "value": f"{action_type}:{target_proj_id}",
                    "action_id": "agent_confirm_action",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "❌ Hủy bỏ", "emoji": True},
                    "style": "danger",
                    "value": f"{action_type}:{target_proj_id}",
                    "action_id": "agent_cancel_action",
                },
            ],
        })

    return {
        "response_type": "in_channel",
        "blocks": blocks,
    }
