# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseStorageProvider(ABC):
    """
    Abstract Service Definition for Workspace Storage and Entity Operations.
    Allows tools to run against local Django ORM, Mock Sandbox, or Remote APIs.
    """

    @abstractmethod
    def query_tasks(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        is_overdue: Optional[bool] = None,
        state_group: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_progress(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_members_workload(
        self,
        workspace_id: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_changelog(
        self,
        version: Optional[str] = None,
        only_fixes: bool = False,
    ) -> Dict[str, Any]:
        pass
