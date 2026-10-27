# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
from typing import Dict, Any, List, Optional

from plane.app.agent.seams.storage.base import BaseStorageProvider
from plane.app.agent.tools.issue_tools import tool_query_tasks, tool_create_task_with_subtasks
from plane.app.agent.tools.project_tools import tool_get_progress
from plane.app.agent.tools.member_tools import tool_get_members_workload
from plane.app.agent.tools.changelog_tools import tool_get_changelog

logger = logging.getLogger(__name__)


class PlaneORMStorageProvider(BaseStorageProvider):
    """
    Storage Provider implementation bound to Plane's Django ORM backend.
    Enforces security isolation via authoritative workspace_id context.
    """

    def query_tasks(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        is_overdue: Optional[bool] = None,
        state_group: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        return tool_query_tasks(
            workspace_id=workspace_id,
            project_id=project_id,
            assignee_id=assignee_id,
            is_overdue=bool(is_overdue),
            status_group=state_group,
        )

    def create_task_with_subtasks(
        self,
        workspace_id: str,
        project_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        assignee_id: Optional[str] = None,
        subtasks: Optional[List[str]] = None,
        created_by_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return tool_create_task_with_subtasks(
            workspace_id=workspace_id,
            project_id=project_id,
            title=title,
            description=description,
            priority=priority,
            assignee_id=assignee_id,
            subtasks=subtasks or [],
            created_by_user_id=created_by_user_id,
        )

    def get_progress(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return tool_get_progress(
            workspace_id=workspace_id,
            project_id=project_id,
        )

    def get_members_workload(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return tool_get_members_workload(
            workspace_id=workspace_id,
            project_id=project_id,
        )

    def get_changelog(
        self,
        version: Optional[str] = None,
        only_fixes: bool = False,
    ) -> Dict[str, Any]:
        return tool_get_changelog(
            version=version,
            only_fixes=only_fixes,
        )
