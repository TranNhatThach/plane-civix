import pytest
from plane.app.agent.engine import PlaneAgentEngine
from plane.app.agent.tools import (
    execute_query_tasks,
    execute_get_progress,
    execute_get_members_workload,
    execute_create_task_with_subtasks,
    execute_update_task_status,
)
from plane.db.models import Issue, State, IssueAssignee, Project, Workspace, User, ProjectMember


@pytest.mark.unit
@pytest.mark.django_db
def test_agent_tools_query_and_progress(db):
    user = User.objects.create(email="agentuser@example.com", first_name="Agent", display_name="Agent User")
    workspace = Workspace.objects.create(name="Test Agent WS", slug="test-agent-ws", owner=user)
    project = Project.objects.create(name="Test Agent Project", identifier="TAP", workspace=workspace)

    ProjectMember.objects.create(project=project, workspace=workspace, member=user, role=20)

    state_todo = State.objects.create(name="To Do", group="unstarted", project=project, workspace=workspace)
    state_done = State.objects.create(name="Done", group="completed", project=project, workspace=workspace)

    issue1 = Issue.objects.create(name="Fix login bug", project=project, workspace=workspace, state=state_todo, created_by=user)
    issue2 = Issue.objects.create(name="Implement API", project=project, workspace=workspace, state=state_done, created_by=user)

    IssueAssignee.objects.create(issue=issue1, assignee=user, project=project, workspace=workspace)

    # Test tool_get_progress
    progress = execute_get_progress(project)
    assert progress["total_tasks"] == 2
    assert progress["completed_tasks"] == 1
    assert progress["completion_percentage"] == 50

    # Test tool_query_tasks
    query_res = execute_query_tasks(project, assignee_name="Agent")
    assert query_res["count"] == 1
    assert query_res["tasks"][0]["key"] == f"TAP-{issue1.sequence_id}"

    # Test tool_get_members_workload
    members_res = execute_get_members_workload(project)
    assert members_res["total_members"] == 1
    assert members_res["members"][0]["display_name"] == "Agent User"


@pytest.mark.unit
@pytest.mark.django_db
def test_agent_create_and_update_task(db):
    user = User.objects.create(email="creator@example.com", first_name="Creator")
    workspace = Workspace.objects.create(name="Test Agent WS 2", slug="test-agent-ws-2", owner=user)
    project = Project.objects.create(name="Test Agent Project 2", identifier="TAP2", workspace=workspace)

    State.objects.create(name="Backlog", group="backlog", project=project, workspace=workspace)

    # Test tool_create_task_with_subtasks
    create_res = execute_create_task_with_subtasks(
        project=project,
        created_by_user=user,
        title="Refactor Agent Core",
        description="Split Slack and Core Engine",
        priority="high",
        subtasks=["Task 1: Tools", "Task 2: Engine"],
    )

    assert create_res["success"] is True
    assert create_res["task_key"] == f"TAP2-1"
    assert len(create_res["subtasks"]) == 2

    # Test tool_update_task_status
    state_done = State.objects.create(name="Done", group="completed", project=project, workspace=workspace)
    update_res = execute_update_task_status(project, sequence_id=1, new_status="done")

    assert update_res["success"] is True
    assert update_res["new_status"] == state_done.name


@pytest.mark.unit
@pytest.mark.django_db
def test_plane_agent_engine_rule_router(db):
    user = User.objects.create(email="router@example.com", first_name="Router")
    workspace = Workspace.objects.create(name="Test Router WS", slug="test-router-ws", owner=user)
    project = Project.objects.create(name="Test Router Project", identifier="TRP", workspace=workspace)

    engine = PlaneAgentEngine(project=project)

    # Test progress prompt
    res_progress = engine.process_request("Xem tiến độ dự án TRP")
    assert res_progress["action_taken"] == "tool_get_progress"
    assert "Báo cáo tiến độ dự án" in res_progress["text"]

    # Test members prompt
    res_members = engine.process_request("Danh sách thành viên dự án")
    assert res_members["action_taken"] == "tool_get_members_workload"
