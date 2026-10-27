# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import uuid
import logging
from typing import Dict, Any, Tuple, Optional, Set
from plane.app.agent.seams.approval.base import BaseApprovalProvider

logger = logging.getLogger(__name__)


class ApprovalPolicy:
    AUTO_APPROVE = "auto_approve"
    PROMPT_ON_DESTRUCTIVE = "prompt_on_destructive"
    READ_ONLY = "read_only"


DESTRUCTIVE_TOOLS: Set[str] = {
    "tool_rebalance_workload",
    "tool_batch_update_tasks",
    "tool_delete_task",
}


class StandardApprovalProvider(BaseApprovalProvider):
    """
    Standard Human-in-the-Loop Approval Provider.
    Enforces policies on destructive or high-impact actions.
    """

    def __init__(self, policy: str = ApprovalPolicy.PROMPT_ON_DESTRUCTIVE):
        self.policy = policy
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}

    def request_approval(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: Optional[Any] = None,
    ) -> Tuple[bool, Optional[str]]:
        if self.policy == ApprovalPolicy.AUTO_APPROVE:
            return True, None

        if self.policy == ApprovalPolicy.READ_ONLY:
            if tool_name in DESTRUCTIVE_TOOLS or tool_name.startswith("tool_create_") or tool_name.startswith("tool_update_"):
                return False, "Chính sách hệ thống đang ở chế độ Chỉ đọc (Read-Only), không cho phép sửa đổi dữ liệu."

        if self.policy == ApprovalPolicy.PROMPT_ON_DESTRUCTIVE:
            if tool_name in DESTRUCTIVE_TOOLS:
                # Check dry_run flag if present
                if args.get("dry_run", True) is False:
                    action_id = f"act_{uuid.uuid4().hex[:10]}"
                    self._pending_approvals[action_id] = {
                        "tool_name": tool_name,
                        "args": args,
                        "context": context,
                    }
                    return False, f"Hành động này có tính chất thay đổi diện rộng, cần người dùng xác nhận (ID: {action_id})."

        return True, None

    def approve_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Approve and pop a pending action for execution."""
        return self._pending_approvals.pop(action_id, None)

    def reject_action(self, action_id: str) -> bool:
        """Reject and discard a pending action."""
        return self._pending_approvals.pop(action_id, None) is not None
