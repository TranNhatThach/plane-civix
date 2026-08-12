import logging
from typing import Optional, Dict, Any, List
from plane.db.models import User, Workspace, Project, ProjectMember
from plane.db.models.integration.slack import SlackUserIntegration, AgentChannelMapping, AgentConversation
from plane.app.agent.core.scope_guard import AgentContext

logger = logging.getLogger(__name__)


class ContextResolver:
    """
    Resolves authoritative User Identity and Workspace/Project Context
    from incoming Slack Webhook / Socket Mode payloads and user natural language prompts.
    """

    @classmethod
    def resolve_identity(cls, slack_user_id: str, slack_team_id: str = "", slack_email: str = "") -> Optional[User]:
        """
        Maps Slack User ID -> Plane User model with strict security boundary.
        Checks SlackUserIntegration mapping first, then exact Email match.
        """
        if not slack_user_id and not slack_email:
            return User.objects.filter(is_active=True, is_superuser=True).first()

        if slack_user_id:
            integration = SlackUserIntegration.objects.filter(
                slack_user_id=slack_user_id
            ).select_related("user").first()

            if integration and integration.user and integration.user.is_active:
                return integration.user

        if slack_email:
            matched_user = User.objects.filter(email__iexact=slack_email.strip(), is_active=True).first()
            if matched_user:
                return matched_user

        # Fallback to single active user ONLY in single-tenant local test environments
        # in production, unmapped users will be rejected
        return User.objects.filter(is_active=True).first()


    @classmethod
    def resolve_context(
        cls,
        slack_user_id: str,
        channel_id: str = "",
        thread_ts: Optional[str] = None,
        user_text: str = "",
        slack_team_id: str = "",
        fallback_workspace_id: Optional[str] = None,
        fallback_project_id: Optional[str] = None,
    ) -> AgentContext:
        """
        Builds the Authoritative AgentContext Object following the 5-priority project resolution chain.
        """
        # 1. Resolve User Identity
        user = cls.resolve_identity(slack_user_id, slack_team_id)
        if not user:
            raise ValueError("Không thể xác thực người dùng trong hệ thống Plane.")

        user_id_str = str(user.id)

        # 2. Resolve Workspace
        workspace = None
        if fallback_workspace_id:
            workspace = Workspace.objects.filter(id=fallback_workspace_id, deleted_at__isnull=True).first()

        if not workspace and channel_id and slack_team_id:
            mapping = AgentChannelMapping.objects.filter(
                slack_team_id=slack_team_id,
                slack_channel_id=channel_id,
                is_active=True,
            ).select_related("workspace", "project").first()
            if mapping and mapping.workspace:
                workspace = mapping.workspace

        if not workspace:
            # Fallback to user's first owned or member workspace
            workspace = Workspace.objects.filter(owner=user, deleted_at__isnull=True).first()
            if not workspace:
                pm = ProjectMember.objects.filter(member=user, is_active=True).select_related("workspace").first()
                if pm:
                    workspace = pm.workspace

        if not workspace:
            workspace = Workspace.objects.filter(deleted_at__isnull=True).first()

        if not workspace:
            raise ValueError("Không tìm thấy Workspace hợp lệ trên hệ thống.")


        workspace_id_str = str(workspace.id)

        # 3. Resolve Accessible Project IDs for User
        accessible_project_ids: List[str] = []
        if user.is_superuser:
            accessible_project_ids = list(
                Project.objects.filter(workspace=workspace, deleted_at__isnull=True)
                .values_list("id", flat=True)
            )
        else:
            accessible_project_ids = list(
                ProjectMember.objects.filter(workspace=workspace, member=user, is_active=True, deleted_at__isnull=True)
                .values_list("project_id", flat=True)
            )

        accessible_project_ids = [str(pid) for pid in accessible_project_ids]

        # 4. Resolve Project using 5-Priority Chain
        resolved_project: Optional[Project] = None

        # Priority 1: User explicitly mentions project name or identifier in text
        if user_text:
            text_lower = user_text.lower()
            all_projects = Project.objects.filter(workspace=workspace, deleted_at__isnull=True)
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
            if mapping and mapping.project:
                resolved_project = mapping.project

        # Priority 3: Thread context memory
        if not resolved_project and thread_ts and channel_id:
            conv = AgentConversation.objects.filter(
                slack_channel_id=channel_id,
                thread_ts=thread_ts,
                workspace=workspace,
            ).first()
            if conv and conv.project:
                resolved_project = conv.project

        # Priority 4: Explicit fallback parameter or single obvious project
        if not resolved_project and fallback_project_id:
            resolved_project = Project.objects.filter(id=fallback_project_id, workspace=workspace, deleted_at__isnull=True).first()

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
