import logging

logger = logging.getLogger(__name__)


def render_slack_block_kit(agent_result: dict, user_name: str = "") -> dict:
    """
    Adapts standardized JSON result from Plane Core Agent Engine
    into rich interactive Slack Block Kit Card UI.
    """
    action = agent_result.get("action_taken", "")
    text = agent_result.get("text", "")
    data = agent_result.get("data", {})

    # Default fallback Slack Block Card
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🤖 Plane AI Agent", "emoji": True},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        },
    ]

    # Render Progress Bar Card
    if action == "tool_get_progress" and data:
        pct = data.get("completion_percentage", 0)
        filled = int(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📊 Báo Cáo Tiến Độ Dự Án {data.get('project_name', '')}", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Hoàn thành:* `{bar}` *{pct}%*\n\n"
                        f"• ✅ Completed: *{data.get('completed_tasks', 0)}* tasks\n"
                        f"• 🏃 In Progress: *{data.get('started_tasks', 0)}* tasks\n"
                        f"• 📥 Backlog: *{data.get('backlog_tasks', 0)}* tasks\n"
                        f"• 🚨 Overdue: *{data.get('overdue_tasks', 0)}* tasks"
                    ),
                },
            },
        ]

    # Render Tasks List Card
    elif action == "tool_query_tasks" and data:
        tasks = data.get("tasks", [])
        if not tasks:
            blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "📋 *Không tìm thấy công việc phù hợp.*"},
                }
            ]
        else:
            task_lines = []
            for t in tasks:
                p_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(t.get("priority", "").lower(), "⚪")
                assignee = f" ➔ @{t['assignees'][0]}" if t.get("assignees") else ""
                task_lines.append(f"{p_emoji} *[{t['key']}] {t['name']}* ({t['status']}){assignee}")

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"📋 Danh Sách {len(tasks)} Công Việc active", "emoji": True},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(task_lines[:12]),
                    },
                },
            ]

    # Render Members Workload Card
    elif action == "tool_get_members_workload" and data:
        members = data.get("members", [])
        mem_lines = []
        for m in members:
            mem_lines.append(f"• *{m['display_name']}*: *{m['in_progress']}* in progress / *{m['total_assigned']}* total assigned")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"👥 Tải Công Việc Thành Viên ({len(members)} Members)", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(mem_lines),
                },
            },
        ]

    # Render Task Creation Confirmation Card
    elif action == "tool_create_task_with_subtasks" and data:
        subtasks = data.get("subtasks", [])
        sub_lines = [f"  ↳ ▫️ *[{s['key']}] {s['title']}*" for s in subtasks]
        sub_str = "\n" + "\n".join(sub_lines) if sub_lines else ""

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"✅ Khởi Tạo Công Việc Thành Công!", "emoji": True},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"📌 *[{data.get('task_key')}] {data.get('title')}*\n"
                        f"• Người gán: *{data.get('assignee')}*\n"
                        f"• Ưu tiên: *{data.get('priority', 'medium').upper()}*\n"
                        f"{'• Task con:' + sub_str if sub_lines else ''}"
                    ),
                },
            },
        ]

    return {
        "response_type": "in_channel",
        "blocks": blocks,
    }
