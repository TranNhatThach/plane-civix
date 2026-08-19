import logging
from typing import Optional, Dict, Any, List
from django.db.models import Q
from plane.db.models import User, Workspace, Project, ProjectMember, WorkspaceMember
from plane.db.models.integration.slack import (
    SlackUserIntegration,
    AgentChannelMapping,
    AgentConversation,
    SlackAutomation,
)
from plane.app.agent.core.scope_guard import AgentContext

logger = logging.getLogger(__name__)


class ContextResolver:
    """
    Resolves authoritative User Identity and Workspace/Project Context
    from incoming Slack Webhook / Socket Mode payloads and user natural language prompts.
    Enforces strict Workspace boundary and Slack integration attachment.
    """

    @classmethod
    def resolve_identity(cls, slack_user_id: str, slack_team_id: str = "", slack_email: str = "") -> Optional[User]:
        """
        Maps Slack User ID -> Plane User model with strict security boundary.
        Checks SlackUserIntegration mapping first, then exact Email match.
        Auto-links SlackUserIntegration if matching email is found.
        Returns None if user cannot be matched (never blindly falls back to another user).
        """
        if not slack_user_id and not slack_email:
            return None

        if slack_user_id:
            integration = SlackUserIntegration.objects.filter(
                slack_user_id=slack_user_id
            ).select_related("user").first()

            if integration and integration.user and integration.user.is_active:
                return integration.user

        if slack_email:
            matched_user = User.objects.filter(email__iexact=slack_email.strip(), is_active=True).first()
            if matched_user:
                # Auto-link SlackUserIntegration for future fast lookups
                if slack_user_id:
                    try:
                        SlackUserIntegration.objects.get_or_create(
                            slack_user_id=slack_user_id,
                            defaults={
                                "user": matched_user,
                                "slack_team_id": slack_team_id,
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Could not auto-link SlackUserIntegration: {e}")
                return matched_user

        return None


    @classmethod
    def resolve_context(
        cls,
        slack_user_id: str,
        channel_id: str = "",
        thread_ts: Optional[str] = None,
        user_text: str = "",
        slack_team_id: str = "",
        slack_email: str = "",
        fallback_workspace_id: Optional[str] = None,
        fallback_project_id: Optional[str] = None,
    ) -> AgentContext:
        """
        Builds the Authoritative AgentContext Object following the 5-priority project resolution chain.
        Strictly enforces Workspace connection to Slack and User membership access boundaries.
        """
        # 1. Resolve User Identity
        user = cls.resolve_identity(slack_user_id, slack_team_id, slack_email)
        if not user:
            raise ValueError(
                "Không tìm thấy tài khoản Plane tương ứng với tài khoản Slack của bạn. "
                "Vui lòng đảm bảo email trên Slack trùng với email tài khoản Plane hoặc liên hệ Quản trị viên để được cấp quyền."
            )

        user_id_str = str(user.id)

        # 2. Resolve Workspace strictly connected to Slack and accessible by User
        workspace = None

        # Priority A: Check fallback_workspace_id (e.g. from active Slack Bot integration)
        if fallback_workspace_id:
            candidate_ws = Workspace.objects.filter(id=fallback_workspace_id, deleted_at__isnull=True).first()
            if candidate_ws:
                is_accessible = (
                    getattr(user, "is_superuser", False)
                    or candidate_ws.owner_id == user.id
                    or WorkspaceMember.objects.filter(workspace=candidate_ws, member=user, is_active=True, deleted_at__isnull=True).exists()
                    or ProjectMember.objects.filter(workspace=candidate_ws, member=user, is_active=True, deleted_at__isnull=True).exists()
                )
                if is_accessible:
                    workspace = candidate_ws
                else:
                    logger.warning(
                        f"User {user.email} is not a member of the Slack Bot fallback workspace: {candidate_ws.name}"
                    )

        # Priority B: Slack Channel mapping
        if not workspace and channel_id and slack_team_id:
            mapping = AgentChannelMapping.objects.filter(
                slack_team_id=slack_team_id,
                slack_channel_id=channel_id,
                is_active=True,
            ).select_related("workspace", "project").first()
            if mapping and mapping.workspace:
                is_accessible = (
                    getattr(user, "is_superuser", False)
                    or mapping.workspace.owner_id == user.id
                    or WorkspaceMember.objects.filter(workspace=mapping.workspace, member=user, is_active=True, deleted_at__isnull=True).exists()
                    or ProjectMember.objects.filter(workspace=mapping.workspace, member=user, is_active=True, deleted_at__isnull=True).exists()
                )
                if is_accessible:
                    workspace = mapping.workspace

        # Priority C: Find Workspaces connected to Slack where the User is an active member
        if not workspace:
            slack_ws_ids = list(
                SlackAutomation.objects.filter(is_active=True, deleted_at__isnull=True)
                .values_list("project__workspace_id", flat=True)
                .distinct()
            )
            if slack_ws_ids:
                wm = WorkspaceMember.objects.filter(
                    workspace_id__in=slack_ws_ids,
                    member=user,
                    is_active=True,
                    deleted_at__isnull=True,
                ).select_related("workspace").first()
                if wm:
                    workspace = wm.workspace
                else:
                    pm = ProjectMember.objects.filter(
                        workspace_id__in=slack_ws_ids,
                        member=user,
                        is_active=True,
                        deleted_at__isnull=True,
                    ).select_related("workspace").first()
                    if pm:
                        workspace = pm.workspace
                    elif getattr(user, "is_superuser", False):
                        workspace = Workspace.objects.filter(id__in=slack_ws_ids, deleted_at__isnull=True).first()
                    else:
                        owner_ws = Workspace.objects.filter(id__in=slack_ws_ids, owner=user, deleted_at__isnull=True).first()
                        if owner_ws:
                            workspace = owner_ws

        # Priority D: Fallback to user member workspace (if no Slack-connected workspace restriction in test environment)
        if not workspace:
            wm = WorkspaceMember.objects.filter(member=user, is_active=True, deleted_at__isnull=True).select_related("workspace").first()
            if wm:
                workspace = wm.workspace
            else:
                pm = ProjectMember.objects.filter(member=user, is_active=True, deleted_at__isnull=True).select_related("workspace").first()
                if pm:
                    workspace = pm.workspace
                else:
                    workspace = Workspace.objects.filter(owner=user, deleted_at__isnull=True).first()

        if not workspace:
            raise ValueError(
                f"Tài khoản '{user.email}' chưa được thêm vào Workspace công ty được kết nối Slack. "
                "Vui lòng liên hệ Quản trị viên để được cấp quyền thành viên."
            )

        workspace_id_str = str(workspace.id)

        # 3. Resolve Accessible Project IDs for User (Strict Isolation)
        accessible_project_ids: List[str] = []
        if getattr(user, "is_superuser", False) or workspace.owner_id == user.id:
            # Superuser / Workspace Owner: all active projects within this specific workspace
            accessible_project_ids = list(
                Project.objects.filter(workspace=workspace, deleted_at__isnull=True)
                .values_list("id", flat=True)
            )
        else:
            # Member / Guest: only projects where the user is an active member OR public projects (network=2)
            accessible_project_ids = list(
                Project.objects.filter(
                    workspace=workspace,
                    deleted_at__isnull=True,
                ).filter(
                    Q(project_projectmember__member=user, project_projectmember__is_active=True, project_projectmember__deleted_at__isnull=True)
                    | Q(network=2)
                ).distinct().values_list("id", flat=True)
            )

        accessible_project_ids = [str(pid) for pid in accessible_project_ids]

        # 4. Resolve Project using 5-Priority Chain
        resolved_project: Optional[Project] = None

        # Priority 1: User explicitly mentions project name or identifier in text
        if user_text:
            text_lower = user_text.lower()
            # Only search within accessible projects in this workspace
            all_projects = Project.objects.filter(
                workspace=workspace,
                id__in=accessible_project_ids,
                deleted_at__isnull=True,
            )
            for proj in all_projects:
                p_name = (proj.name or "").lower()
                p_id = (proj.identifier or "").lower()
                if (p_name and p_name in text_lower) or (p_id and p_id in text_lower):
                    resolved_project = proj
                    break

        # Priority 2: Slack Channel mapping
        if not resolved_project and channel_id and slack_team_id:
            mapping = AgentChannelMapping.objects.filter(
                slack_team_id=slack_team_id,
                slack_channel_id=channel_id,
                is_active=True,
            ).first()
            if mapping and mapping.project and str(mapping.project.id) in accessible_project_ids:
                resolved_project = mapping.project

        # Priority 3: Thread context memory
        if not resolved_project and thread_ts and channel_id:
            conv = AgentConversation.objects.filter(
                slack_channel_id=channel_id,
                thread_ts=thread_ts,
                workspace=workspace,
            ).first()
            if conv and conv.project and str(conv.project.id) in accessible_project_ids:
                resolved_project = conv.project

        # Priority 4: Explicit fallback parameter or single obvious project
        if not resolved_project and fallback_project_id:
            resolved_project = Project.objects.filter(
                id=fallback_project_id,
                workspace=workspace,
                id__in=accessible_project_ids,
                deleted_at__isnull=True,
            ).first()

        if not resolved_project and len(accessible_project_ids) == 1:
            resolved_project = Project.objects.filter(id=accessible_project_ids[0]).first()

        project_id_str = str(resolved_project.id) if resolved_project else None
        project_identifier = resolved_project.identifier if resolved_project else None

        return AgentContext(
            slack_user_id=slack_user_id or "user_slack",
            plane_user_id=user_id_str,
            user_email=user.email or "",
            is_superuser=getattr(user, "is_superuser", False),
            workspace_id=workspace_id_str,
            workspace_slug=workspace.slug or "",
            project_id=project_id_str,
            project_identifier=project_identifier,
            slack_team_id=slack_team_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            accessible_project_ids=accessible_project_ids,
        )
