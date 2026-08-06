# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Backward-compatibility alias wrapper.
All modular Telegram bot logic is organized in `plane.bgtasks.telegram_bot`.
"""

from plane.bgtasks.telegram_bot import (
    process_telegram_update,
    check_command_permission,
    handle_ai_ask,
    handle_project_summary,
    get_project_and_automation,
    handle_task_query,
    handle_tasks_list,
    handle_search_query,
    handle_create_task,
)

__all__ = [
    "process_telegram_update",
    "check_command_permission",
    "handle_ai_ask",
    "handle_project_summary",
    "get_project_and_automation",
    "handle_task_query",
    "handle_tasks_list",
    "handle_search_query",
    "handle_create_task",
]
