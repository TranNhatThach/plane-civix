# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from typing import Optional, Dict, Any, Tuple


class FastPathMatcher:
    """
    Sub-50ms Deterministic Intent Matcher.
    Short-circuits standard read-only queries directly to tools without calling LLMs.
    """

    @classmethod
    def match(
        cls,
        prompt: str,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Evaluates prompt text.
        Returns Tuple: (tool_name, args_dict) or (None, {})
        """
        p_lower = (prompt or "").lower().strip()
        args: Dict[str, Any] = {}

        if any(kw in p_lower for kw in ["báo cáo workspace", "tổng quan workspace", "tất cả task workspace", "tiến độ workspace"]):
            return "tool_get_workspace_summary", args

        if any(kw in p_lower for kw in ["báo cáo tiến độ", "xem tiến độ", "tiến độ dự án"]):
            return "tool_get_progress", args

        if any(kw in p_lower for kw in ["task của tôi", "công việc của tôi", "việc của tôi", "tasks của tôi"]):
            if user_id:
                args["assignee_id"] = str(user_id)
            if user_name:
                args["assignee_name"] = str(user_name)
            return "tool_query_tasks", args

        if any(kw in p_lower for kw in ["quá hạn", "trễ hạn"]) and not any(kw in p_lower for kw in ["phân bổ", "điều chuyển", "rebalance"]):
            args["is_overdue"] = True
            return "tool_query_tasks", args

        if any(kw in p_lower for kw in ["danh sách task", "xem task", "danh sách công việc"]):
            has_specific = any(w in p_lower for w in ["của ", "trạng thái", "in progress", "done", "completed", "lọc", "ưu tiên"])
            if not has_specific:
                return "tool_query_tasks", args

        if any(kw in p_lower for kw in ["thành viên", "khối lượng công việc", "ai làm gì", "phân bổ công việc"]):
            return "tool_get_members_workload", args

        if any(kw in p_lower for kw in ["danh sách dự án", "xem các dự án", "tất cả dự án"]):
            return "tool_list_projects", args

        if any(kw in p_lower for kw in ["changelog", "phiên bản", "cập nhật gì", "bản cập nhật", "có gì mới", "bug nào", "lỗi đã sửa"]):
            if any(w in p_lower for w in ["bug", "lỗi", "fix", "sửa"]):
                args["only_fixes"] = True
            return "tool_get_changelog", args

        return None, {}
