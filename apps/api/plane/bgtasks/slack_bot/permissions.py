# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from typing import Tuple, Dict, Any, Optional
from plane.db.models.integration.slack import SlackAutomation


def check_slack_command_permission(
    automation: Optional[SlackAutomation],
    user_id: str,
    user_name: str = "",
    command_text: str = "",
) -> Tuple[bool, str]:
    """
    Checks if the Slack user sending the command has permission to execute.
    Configured via `events` JSON field on SlackAutomation model:
      - allowed_users: list of Slack User IDs (e.g. U123456) or usernames (e.g. @nam)
      - restrict_commands: boolean flag to restrict commands to allowed_users list
    """
    if not automation:
        return True, ""

    events_config = automation.events or {}
    restrict_commands = events_config.get("restrict_commands", False)
    allowed_users = events_config.get("allowed_users") or events_config.get("allowed_creators")

    # If restriction is enabled or an allowed list is explicitly provided
    if restrict_commands or (allowed_users is not None and isinstance(allowed_users, list)):
        if not allowed_users:
            allowed_users = []

        allowed_set = {str(u).lower().lstrip("@").strip() for u in allowed_users if u}
        clean_user_id = str(user_id).lower().strip()
        clean_user_name = str(user_name).lower().lstrip("@").strip()

        if clean_user_id not in allowed_set and clean_user_name not in allowed_set:
            display_name = f"@{user_name}" if user_name else f"ID: {user_id}"
            return False, (
                f"⛔ *Quyền truy cập bị từ chối!*\n\n"
                f"Xin chào *{display_name}* (Slack User ID: `{user_id}`), bạn chưa được phân quyền sử dụng Plane AI Agent cho dự án này.\n\n"
                f"💡 *Vui lòng gửi Slack User ID: `{user_id}` cho Quản trị viên để được thêm vào danh sách cấp quyền trên Plane Web.*"
            )

    return True, ""
