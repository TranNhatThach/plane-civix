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


@pytest.mark.unit
@pytest.mark.django_db
def test_tool_list_projects_workspace_isolation(db):
    from plane.app.agent.tools.project_tools import tool_list_projects

    user_a = User.objects.create(username="usera", email="usera@example.com")
    user_b = User.objects.create(username="userb", email="userb@example.com")

    ws_a = Workspace.objects.create(name="WS A", slug="ws-a", owner=user_a)
    ws_b = Workspace.objects.create(name="WS B", slug="ws-b", owner=user_b)

    proj_a1 = Project.objects.create(name="Project A1", identifier="PA1", workspace=ws_a)
    proj_a2_private = Project.objects.create(name="Project A2 Private", identifier="PA2", workspace=ws_a, network=0)
    proj_b1 = Project.objects.create(name="Project B1", identifier="PB1", workspace=ws_b)

    # user_a is member of proj_a1 only (not proj_a2_private and not proj_b1)
    ProjectMember.objects.create(project=proj_a1, workspace=ws_a, member=user_a, role=15)
    ProjectMember.objects.create(project=proj_a2_private, workspace=ws_a, member=user_b, role=20)
    ProjectMember.objects.create(project=proj_b1, workspace=ws_b, member=user_b, role=20)

    ctx_user_a = ContextResolver.resolve_context(
        slack_user_id="U_USER_A",
        slack_email="usera@example.com",
        fallback_workspace_id=str(ws_a.id),
    )

    res = tool_list_projects(_context=ctx_user_a)
    proj_names = [p["name"] for p in res["projects"]]

    # User A in WS A should ONLY see Project A1 (cannot see WS B projects or User B's private project in WS A)
    assert "Project A1" in proj_names
    assert "Project B1" not in proj_names
    assert "Project A2 Private" not in proj_names


@pytest.mark.unit
@pytest.mark.django_db
def test_tasks_cua_toi_exact_user_id_matching(db):
    from plane.app.agent.tools.issue_tools import tool_query_tasks

    user_a = User.objects.create(username="dev_a", email="dev_a@example.com", first_name="Nam")
    user_b = User.objects.create(username="dev_b", email="dev_b@example.com", first_name="Nam")

    ws = Workspace.objects.create(name="Match WS", slug="match-ws", owner=user_a)
    proj = Project.objects.create(name="Match Proj", identifier="MP", workspace=ws)
    state = State.objects.create(name="In Progress", group="started", project=proj, workspace=ws)

    # Issue assigned to dev_a
    issue_a = Issue.objects.create(name="Task for User A", project=proj, workspace=ws, state=state, created_by=user_a)
    issue_a.assignees.add(user_a)

    # Issue assigned to dev_b (also named Nam)
    issue_b = Issue.objects.create(name="Task for User B", project=proj, workspace=ws, state=state, created_by=user_b)
    issue_b.assignees.add(user_b)

    ctx_a = AgentContext(
        slack_user_id="U_DEV_A",
        plane_user_id=str(user_a.id),
        workspace_id=str(ws.id),
        project_id=str(proj.id),
    )

    engine_a = PlaneAgentEngine(project=proj, user=user_a, context=ctx_a)
    res = engine_a.process_request("Xem task của tôi")

    matched_keys = [t["name"] for t in res["data"]["tasks"]]
    assert "Task for User A" in matched_keys
    assert "Task for User B" not in matched_keys


