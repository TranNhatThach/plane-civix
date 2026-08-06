# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import re
from html import escape
from typing import Dict, Any

from django.conf import settings
from plane.bgtasks.telegram_publisher import send_telegram_message, schedule_auto_delete
from plane.bgtasks.telegram_bot.permissions import check_command_permission
from plane.bgtasks.telegram_bot.ai_handlers import handle_ai_ask
from plane.bgtasks.telegram_bot.summary_handlers import handle_project_summary
from plane.bgtasks.telegram_bot.task_handlers import (
    get_project_and_automation,
    handle_task_query,
    handle_tasks_list,
    handle_search_query,
    handle_create_task,
)


def process_telegram_update(update_data: Dict[str, Any]) -> None:
    """Processes incoming Telegram webhook or long-polling update and routes to handlers."""
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

    is_private = chat_type == "private"
    is_reply_to_bot = message.get("reply_to_message", {}).get("from", {}).get("is_bot", False)
    is_mentioned = False

    # Clean text if bot username mentioned e.g. /task@CivixBot
    if "@" in text:
        parts = text.split("@")
        if len(parts) > 1:
            bot_name = parts[1].split()[0]
            is_mentioned = True
            text = text.replace(f"@{bot_name}", "").strip()

    is_command = text.startswith("/")

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

    # Permission check for specific commands
    has_perm, deny_reason = check_command_permission(automation, message, cmd_part)
    if not has_perm:
        send_telegram_message(automation.bot_token, chat_id, deny_reason)
        return

    if cmd_part in ["/myid", "/id", "/whoami"]:
        sender = message.get("from", {})
        sender_id = str(sender.get("id", ""))
        sender_username = sender.get("username", "không có username")
        sender_name = sender.get("first_name", "User")
        reply_text = (
            f"👤 <b>Thông tin Tài khoản Telegram của bạn:</b>\n\n"
            f"• <b>Họ tên:</b> {escape(sender_name)}\n"
            f"• <b>Username:</b> @{escape(sender_username)}\n"
            f"• <b>Telegram User ID:</b> <code>{sender_id}</code>\n\n"
            f"📋 <i>Sao chép ID <code>{sender_id}</code> này để dán vào cài đặt Phân quyền Workspace trong Plane!</i>"
            "\n\n"
            "<b>TIN NHẮN SẼ TỰ HỦY SAU 15 GIÂY</b>"
        )
    elif cmd_part in ["/start", "/help"]:
        reply_text = (
            "🤖 <b>Plane Telegram Assistant</b>\n\n"
            "Tôi có thể giúp bạn tra cứu thông tin dự án & hỏi đáp AI:\n\n"
            "• <code>/myid</code>: Xem Telegram User ID của bạn (để dán vào cài đặt phân quyền)\n"
            "• <code>/task &lt;MÃ_TASK&gt;</code>: Xem chi tiết task (vd: <code>/task CIVIX-12</code>)\n"
            "• <code>/tasks</code>: Xem danh sách các task đang mở\n"
            "• <code>/create &lt;nội dung / danh sách task&gt;</code>: AI tự tạo task tự động vào Plane\n"
            "• <code>/search &lt;từ khóa&gt;</code>: Tìm kiếm task theo từ khóa\n"
            "• <code>/summary</code> hoặc <code>/status</code>: Báo cáo tổng quan tiến độ dự án\n"
            "• <code>/ask &lt;câu hỏi&gt;</code>: Hỏi đáp AI bằng ngôn ngữ tự nhiên\n"
            "\n"
            "<b>TIN NHẮN SẼ TỰ HỦY SAU 15 GIÂY</b>"
        )
    elif cmd_part == "/task":
        reply_text = handle_task_query(automation, project, arg_part, app_url)
    elif cmd_part == "/tasks":
        reply_text = handle_tasks_list(project, app_url)
    elif cmd_part in ["/create", "/newtask"]:
        reply_text = handle_create_task(project, arg_part, app_url)
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

    user_msg_id = message.get("message_id")
    success, resp_data = send_telegram_message(automation.bot_token, chat_id, reply_text)

    # Auto-delete helper/info commands & replies after 15 seconds to keep chat clean
    auto_delete_commands = ["/start", "/help", "/myid", "/id", "/whoami"]
    if cmd_part in auto_delete_commands and success and isinstance(resp_data, dict):
        bot_msg_id = resp_data.get("result", {}).get("message_id")
        to_delete = [m for m in [user_msg_id, bot_msg_id] if m]
        schedule_auto_delete(automation.bot_token, chat_id, to_delete, delay_seconds=15.0)
