import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def render_slack_block_kit(agent_result: Dict[str, Any], user_name: str = "") -> Dict[str, Any]:
    """
    Adapts standardized JSON results from Plane Core Agent Engine
    into rich, interactive, high-aesthetic Slack Block Kit Cards.
    """
    action = agent_result.get("action_taken", "")
    text = agent_result.get("text", "")
    data = agent_result.get("data", {})
    user_str = f"@{user_name}" if user_name else "bạn"

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

    # Render Progress Bar Card
    if action == "tool_get_progress" and data:
        pct = data.get("completion_percentage", 0)
        filled = int(pct / 10)
        bar = "▓" * filled + "░" * (10 - filled)
        proj_name = data.get("project_name", "Dự án")

        status_emoji = "🟢" if pct >= 70 else ("🟡" if pct >= 30 else "🔴")

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
                        "url": "http://localhost/",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📋 Xem danh sách Task", "emoji": True},
                        "value": "view_tasks",
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

    # Render Tasks List Card
    elif action == "tool_query_tasks" and data:
        tasks = data.get("tasks", [])
        proj_name = tasks[0]["key"].split("-")[0] if tasks else "Plane"

        if not tasks:
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "📋 Danh Sách Công Việc", "emoji": True},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🎉 *Hiện tại không có công việc nào thỏa mãn điều kiện tìm kiếm!*"},
                },
            ]
        else:
            fields = []
            for t in tasks[:8]:
                p_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(t.get("priority", "").lower(), "⚪")
                assignee = f" ➔ @{t['assignees'][0]}" if t.get("assignees") else ""
                due = f" | 🗓️ {t['target_date']}" if t.get("target_date") else ""

                fields.append({
                    "type": "mrkdwn",
                    "text": f"{p_emoji} *[{t['key']}] {t['name']}*\nTrạng thái: `{t['status']}`{assignee}{due}",
                })

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"📋 Quản Lý Công Việc — {data.get('total_matched', len(tasks))} Task Active", "emoji": True},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "fields": fields[:10],
                },
                {"type": "divider"},
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "➕ Tạo Task Mới", "emoji": True},
                            "url": "http://localhost/",
                            "style": "primary",
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📊 Xem Báo Cáo Tiến Độ", "emoji": True},
                            "value": "view_progress",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"🤖 *Plane Core AI Agent* • Đang hiển thị {len(tasks)} / {data.get('total_matched', len(tasks))} công việc"}
                    ],
                },
            ]

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
                        "url": "http://localhost/",
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

    return {
        "response_type": "in_channel",
        "blocks": blocks,
    }
