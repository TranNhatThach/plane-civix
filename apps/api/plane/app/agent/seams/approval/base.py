# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional


class BaseApprovalProvider(ABC):
    """
    Abstract Service Definition for Human-in-the-Loop (HITL) Approval.
    Governs safety boundaries for critical or destructive tool executions.
    """

    @abstractmethod
    def request_approval(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: Optional[Any] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether a tool execution requires human approval or can proceed.
        Returns Tuple: (is_approved, reason_or_pending_action_id)
        """
        pass
