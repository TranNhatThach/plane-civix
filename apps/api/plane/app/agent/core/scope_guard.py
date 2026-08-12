import functools
import inspect
import logging

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class ScopeViolationError(Exception):
    """Raised when an agent tool call attempts cross-workspace or unauthorized data access."""
    pass


@dataclass
class AgentContext:
    """
    Authoritative Context Object passed with every Agent request.
    """
    slack_user_id: str
    plane_user_id: str
    user_email: str = ""
    is_superuser: bool = False
    
    workspace_id: str = ""
    workspace_slug: str = ""
    project_id: Optional[str] = None
    project_identifier: Optional[str] = None
    
    slack_team_id: str = ""
    channel_id: str = ""
    thread_ts: Optional[str] = None
    conversation_id: str = ""
    
    accessible_project_ids: List[str] = field(default_factory=list)
    last_discussed_issue_ids: List[str] = field(default_factory=list)
    active_intent: Optional[str] = None


def scope_guard(
    requires_project: bool = False,
    min_role: int = 15  # 5: Guest, 10: Viewer, 15: Member, 20: Admin
):
    """
    Decorator enforcing Security Boundaries on Agent Tool execution.
    Validates workspace_id, project_id, user_id against DB records.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            context: Optional[AgentContext] = kwargs.get("_context")
            
            # 1. Force Workspace Isolation
            tool_workspace_id = kwargs.get("workspace_id")
            if context and tool_workspace_id and str(tool_workspace_id) != str(context.workspace_id):
                logger.error(
                    f"[SECURITY VIOLATION] User {context.plane_user_id} attempted access "
                    f"to Workspace '{tool_workspace_id}' outside assigned '{context.workspace_id}'"
                )
                raise ScopeViolationError(
                    f"❌ Truy cập bị từ chối: Workspace '{tool_workspace_id}' không hợp lệ hoặc nằm ngoài phạm vi được phép."
                )

            # Auto-inject workspace_id from context if missing or present
            if context and context.workspace_id:
                kwargs["workspace_id"] = str(context.workspace_id)

            # 2. Force Project Scope Validation if required
            raw_proj_id = kwargs.get("project_id") or (context.project_id if context else None)
            target_project_id = None

            if raw_proj_id and str(raw_proj_id).strip() not in ["None", "null", ""]:
                try:
                    import uuid
                    uuid.UUID(str(raw_proj_id))
                    target_project_id = str(raw_proj_id)
                except ValueError:
                    target_project_id = None

            if target_project_id is None:
                kwargs.pop("project_id", None)

            if requires_project and not target_project_id:
                return {
                    "success": False,
                    "error_type": "AMBIGUOUS_PROJECT",
                    "message": "Vui lòng chỉ định rõ dự án bạn muốn thực hiện tác vụ này."
                }

            if target_project_id and context and context.workspace_id:
                from plane.db.models import Project, ProjectMember
                
                # Check project belongs to current workspace
                proj = Project.objects.filter(
                    id=target_project_id,
                    workspace_id=context.workspace_id,
                    deleted_at__isnull=True
                ).first()

                
                if not proj:
                    raise ScopeViolationError(
                        f"❌ Dự án ID '{target_project_id}' không tồn tại trong Workspace hiện tại."
                    )

                # Verify User Permission Role in Project
                if not context.is_superuser:
                    member = ProjectMember.objects.filter(
                        project_id=target_project_id,
                        member_id=context.plane_user_id,
                        is_active=True,
                        deleted_at__isnull=True
                    ).first()
                    
                    if not member or member.role < min_role:
                        raise PermissionDenied(
                            f"❌ Bạn không có quyền truy cập vào dự án '{proj.name}'."
                        )
                
                kwargs["project_id"] = str(target_project_id)

            # 3. Force Issue Scope Validation if sequence_id is passed
            sequence_id = kwargs.get("sequence_id")
            if sequence_id and kwargs.get("project_id") and kwargs.get("workspace_id"):
                from plane.db.models import Issue
                issue = Issue.objects.filter(
                    project_id=kwargs["project_id"],
                    workspace_id=kwargs["workspace_id"],
                    sequence_id=sequence_id,
                    deleted_at__isnull=True
                ).first()
                
                if not issue:
                    return {
                        "success": False,
                        "error_type": "ISSUE_NOT_FOUND",
                        "message": f"Không tìm thấy Task #{sequence_id} trong dự án hiện tại."
                    }
                kwargs["_issue_instance"] = issue

            # Filter kwargs to match target func signature
            sig = inspect.signature(func)
            has_var_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

            filtered_kwargs = {}
            for k, v in kwargs.items():
                if has_var_kwargs or k in sig.parameters:
                    filtered_kwargs[k] = v

            return func(*args, **filtered_kwargs)

        return wrapper
    return decorator

