from unittest.mock import MagicMock, patch
import pytest
from plane.app.agent.core.context_resolver import ContextResolver
from plane.app.agent.core.scope_guard import AgentContext


@pytest.mark.unit
def test_resolve_identity_returns_none_when_no_match():
    """Verify that resolve_identity NEVER falls back to user #1 blindly."""
    with patch("plane.app.agent.core.context_resolver.SlackUserIntegration") as mock_integ, \
         patch("plane.app.agent.core.context_resolver.User") as mock_user:
        
        mock_integ.objects.filter.return_value.select_related.return_value.first.return_value = None
        mock_user.objects.filter.return_value.first.return_value = None

        # Unknown Slack user with unlinked email
        res = ContextResolver.resolve_identity(
            slack_user_id="U_UNKNOWN_BOSS",
            slack_team_id="T_CORP",
            slack_email="boss.unknown@example.com",
        )

        assert res is None


@pytest.mark.unit
def test_resolve_identity_matches_by_email_and_autolinks():
    """Verify that resolve_identity correctly matches user by email and creates SlackUserIntegration."""
    with patch("plane.app.agent.core.context_resolver.SlackUserIntegration") as mock_integ, \
         patch("plane.app.agent.core.context_resolver.User") as mock_user:

        mock_integ.objects.filter.return_value.select_related.return_value.first.return_value = None
        
        boss_user = MagicMock()
        boss_user.id = "boss-uuid-123"
        boss_user.email = "boss@civix.com"
        boss_user.is_active = True
        mock_user.objects.filter.return_value.first.return_value = boss_user

        res = ContextResolver.resolve_identity(
            slack_user_id="U_BOSS_456",
            slack_team_id="T_CIVIX",
            slack_email="boss@civix.com",
        )

        assert res is not None
        assert res.id == "boss-uuid-123"
        assert res.email == "boss@civix.com"
        mock_integ.objects.get_or_create.assert_called_once()


@pytest.mark.unit
def test_resolve_context_raises_error_if_user_not_authenticated():
    """Verify that resolve_context raises ValueError if user is unknown."""
    with patch.object(ContextResolver, "resolve_identity", return_value=None):
        with pytest.raises(ValueError) as exc_info:
            ContextResolver.resolve_context(
                slack_user_id="U_STRANGER",
                slack_email="stranger@example.com",
            )
        assert "Không tìm thấy tài khoản Plane tương ứng" in str(exc_info.value)


@pytest.mark.unit
def test_resolve_context_prioritizes_slack_company_workspace_over_personal():
    """Verify that resolve_context routes strictly to company workspace connected to Slack."""
    boss_user = MagicMock()
    boss_user.id = "boss-uuid-123"
    boss_user.email = "boss@civix.com"
    boss_user.is_superuser = False

    company_ws = MagicMock()
    company_ws.id = "company-ws-uuid"
    company_ws.slug = "civix-company"
    company_ws.name = "Civix Corp"
    company_ws.owner_id = "dev-uuid-999"  # Owned by dev, boss is member

    company_proj = MagicMock()
    company_proj.id = "company-proj-uuid"
    company_proj.name = "Civix Main Project"
    company_proj.identifier = "CIVIX"
    company_proj.workspace = company_ws

    with patch.object(ContextResolver, "resolve_identity", return_value=boss_user), \
         patch("plane.app.agent.core.context_resolver.Workspace") as mock_ws, \
         patch("plane.app.agent.core.context_resolver.WorkspaceMember") as mock_wm, \
         patch("plane.app.agent.core.context_resolver.Project") as mock_proj:

        mock_ws.objects.filter.return_value.first.return_value = company_ws
        mock_wm.objects.filter.return_value.exists.return_value = True
        mock_proj.objects.filter.return_value.filter.return_value.distinct.return_value.values_list.return_value = [
            "company-proj-uuid"
        ]
        mock_proj.objects.filter.return_value.first.return_value = company_proj

        ctx = ContextResolver.resolve_context(
            slack_user_id="U_BOSS_456",
            slack_email="boss@civix.com",
            fallback_workspace_id="company-ws-uuid",
            fallback_project_id="company-proj-uuid",
        )

        assert ctx.workspace_id == "company-ws-uuid"
        assert ctx.workspace_slug == "civix-company"
        assert ctx.user_email == "boss@civix.com"
        assert ctx.project_id == "company-proj-uuid"


@pytest.mark.unit
def test_tool_get_changelog():
    """Verify tool_get_changelog returns structured version details."""
    from plane.app.agent.tools.changelog_tools import tool_get_changelog

    res = tool_get_changelog(version="v1.4.1")
    assert res["success"] is True
    assert res["version"] == "v1.4.1"
    assert len(res["fixes"]) > 0
    assert "Sửa lỗi Slack Agent" in str(res["fixes"])


@pytest.mark.unit
def test_agent_engine_changelog_fast_path():
    """Verify PlaneAgentEngine handles natural language changelog requests."""
    from plane.app.agent.core.engine import PlaneAgentEngine

    mock_proj = MagicMock()
    mock_proj.id = "proj-uuid"
    mock_proj.name = "Civix Main"
    mock_proj.workspace.slug = "civix"

    mock_user = MagicMock()
    mock_user.id = "user-uuid"

    ctx = AgentContext(
        slack_user_id="U_BOSS",
        plane_user_id="user-uuid",
        workspace_id="ws-uuid",
        workspace_slug="civix",
        project_id="proj-uuid",
    )

    with patch("plane.app.agent.core.engine.get_configuration_value", return_value=("1",)):
        engine = PlaneAgentEngine(project=mock_proj, user=mock_user, context=ctx)
        res = engine.process_request("Xem changelog và các bug đã fix bản mới nhất")

        assert res["action_taken"] == "tool_get_changelog"
        assert "Nhật Ký Phiên Bản Civix" in res["text"]
        assert "v1.4.1" in res["text"]
