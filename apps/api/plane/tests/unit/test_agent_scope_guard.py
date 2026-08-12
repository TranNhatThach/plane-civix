import pytest
from django.core.exceptions import PermissionDenied
from plane.db.models import Issue, State, Project, Workspace, User, ProjectMember
from plane.db.models.integration.slack import SlackUserIntegration, AgentChannelMapping
from plane.app.agent.core.scope_guard import AgentContext, scope_guard, ScopeViolationError
from plane.app.agent.core.context_resolver import ContextResolver
from plane.app.agent.core.engine import PlaneAgentEngine


@pytest.mark.unit
@pytest.mark.django_db
def test_identity_and_context_resolver(db):
    user = User.objects.create(username="slackuser", email="slackuser@example.com", first_name="Slack", last_name="Tester", display_name="Slack User")
    workspace = Workspace.objects.create(name="Slack WS", slug="slack-ws", owner=user)
    project = Project.objects.create(name="AI Assistant", identifier="AI", workspace=workspace)
    ProjectMember.objects.create(project=project, workspace=workspace, member=user, role=20)

    # 1. Test Slack Identity Resolution
    SlackUserIntegration.objects.create(slack_user_id="U123456", user=user, slack_team_id="T0001", project=project, workspace=workspace)
    resolved_user = ContextResolver.resolve_identity("U123456")
    assert resolved_user.id == user.id


    # 2. Test Channel Mapping Resolution (Priority 2)
    AgentChannelMapping.objects.create(
        slack_team_id="T0001",
        slack_channel_id="C999",
        workspace=workspace,
        project=project,
    )

    ctx = ContextResolver.resolve_context(
        slack_user_id="U123456",
        channel_id="C999",
        slack_team_id="T0001"
    )

    assert ctx.workspace_id == str(workspace.id)
    assert ctx.project_id == str(project.id)
    assert ctx.project_identifier == "AI"


@pytest.mark.unit
@pytest.mark.django_db
def test_scope_guard_workspace_isolation(db):
    user = User.objects.create(username="user_a", email="user_a@example.com", first_name="UserA")
    ws_a = Workspace.objects.create(name="WS A", slug="ws-a", owner=user)
    ws_b = Workspace.objects.create(name="WS B", slug="ws-b", owner=user)
    
    proj_a = Project.objects.create(name="Project A", identifier="PA", workspace=ws_a)
    proj_b = Project.objects.create(name="Project B", identifier="PB", workspace=ws_b)

    ProjectMember.objects.create(project=proj_a, workspace=ws_a, member=user, role=20)
    ProjectMember.objects.create(project=proj_b, workspace=ws_b, member=user, role=20)

    ctx_a = AgentContext(
        slack_user_id="U_A",
        plane_user_id=str(user.id),
        workspace_id=str(ws_a.id),
        project_id=str(proj_a.id),
    )


    @scope_guard(requires_project=True)
    def dummy_tool(workspace_id: str, project_id: str, _context: AgentContext = None):
        return {"success": True, "workspace_id": workspace_id, "project_id": project_id}

    # Valid execution within WS_A
    res = dummy_tool(workspace_id=str(ws_a.id), project_id=str(proj_a.id), _context=ctx_a)
    assert res["success"] is True

    # Cross-Workspace Attempt (Attempting to query WS_B while in WS_A Context) -> ScopeViolationError
    with pytest.raises(ScopeViolationError):
        dummy_tool(workspace_id=str(ws_b.id), project_id=str(proj_b.id), _context=ctx_a)


@pytest.mark.unit
@pytest.mark.django_db
def test_scope_guard_permission_role_enforcement(db):
    owner = User.objects.create(username="owner", email="owner@example.com", first_name="Owner")
    guest = User.objects.create(username="guest", email="guest_user@example.com", first_name="Guest")
    
    workspace = Workspace.objects.create(name="Security WS", slug="sec-ws", owner=owner)
    project = Project.objects.create(name="Restricted Project", identifier="RES", workspace=workspace)

    # Guest has low role (5 = Guest)
    ProjectMember.objects.create(project=project, workspace=workspace, member=guest, role=5)

    guest_ctx = AgentContext(
        slack_user_id="U_GUEST",
        plane_user_id=str(guest.id),
        workspace_id=str(workspace.id),
        project_id=str(project.id),
    )

    @scope_guard(requires_project=True, min_role=15)
    def restricted_tool(workspace_id: str, project_id: str, _context: AgentContext = None):
        return {"success": True}

    # Expect PermissionDenied due to min_role=15 required
    with pytest.raises(PermissionDenied):
        restricted_tool(workspace_id=str(workspace.id), project_id=str(project.id), _context=guest_ctx)


@pytest.mark.unit
@pytest.mark.django_db
def test_fast_path_deterministic_rendering_policy(db, monkeypatch):
    from plane.app.agent.core.llm_client import SystemLLMClient

    user = User.objects.create(username="fastpath", email="fastpath@example.com", first_name="FastPath")
    workspace = Workspace.objects.create(name="FastPath WS", slug="fastpath-ws", owner=user)
    project = Project.objects.create(name="FastPath Project", identifier="FP", workspace=workspace)
    ProjectMember.objects.create(project=project, workspace=workspace, member=user, role=20)


    state_todo = State.objects.create(name="To Do", group="unstarted", project=project, workspace=workspace)
    Issue.objects.create(name="FastPath Task 1", project=project, workspace=workspace, state=state_todo, created_by=user)

    def mock_generate_completion(self, user_prompt, context_prompt):
        return None, {"name": "tool_get_progress", "args": {}}

    monkeypatch.setattr(SystemLLMClient, "generate_completion", mock_generate_completion)

    ctx = AgentContext(
        slack_user_id="U_FP",
        plane_user_id=str(user.id),
        workspace_id=str(workspace.id),
        project_id=str(project.id),
    )

    engine = PlaneAgentEngine(project=project, user=user, context=ctx)
    res = engine.process_request("Xem tiến độ dự án FastPath Project")

    # Verify Fast Path Execution (Direct Deterministic Result)
    assert res["action_taken"] == "tool_get_progress"
    assert "báo cáo tiến độ" in res["text"].lower()
    assert res["data"]["total_tasks"] == 1

