# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from html import escape
from plane.db.models import TelegramAutomation


def check_command_permission(automation: TelegramAutomation, message: dict, command: str) -> tuple[bool, str]:
    """
    Checks if the Telegram user sending the message has permission to execute the requested command.
    Configured via `events` JSON field on TelegramAutomation model:
      - allowed_creators: list of Telegram User IDs or @usernames allowed to run /create
      - restrict_create: boolean flag to restrict /create to allowed_creators list
    """
    sender = message.get("from", {})
    sender_id = str(sender.get("id", ""))
    sender_username = (sender.get("username") or "").lower().lstrip("@")
    sender_name = sender.get("first_name") or sender_username or sender_id

    events_config = automation.events or {}

    # Check permission for /create or /newtask command
    if command in ["/create", "/newtask"]:
        allowed_users = events_config.get("allowed_creators") or events_config.get("allowed_users")
        restrict_create = events_config.get("restrict_create", False)

        # If restriction is enabled or an allowed list is explicitly provided
        if restrict_create or allowed_users is not None:
            if not allowed_users:
                allowed_users = []

            allowed_set = {str(u).lower().lstrip("@") for u in allowed_users}
            if sender_id not in allowed_set and sender_username not in allowed_set:
                return False, (
                    f"⛔ <b>Quyền truy cập bị từ chối!</b>\n\n"
                    f"Xin chào <b>{escape(sender_name)}</b> (ID: <code>{sender_id}</code>), bạn chưa được phân quyền tạo Task qua Telegram cho dự án này.\n\n"
                    f"💡 <i>Vui lòng liên hệ Admin để thêm Telegram ID: <code>{sender_id}</code> hoặc Username của bạn vào danh sách được phép.</i>"
                )

    return True, ""
