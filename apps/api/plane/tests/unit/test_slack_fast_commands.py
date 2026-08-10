import pytest
from plane.db.models import Workspace, Project, Issue, State, User, ProjectMember
from plane.bgtasks.slack_bot.fast_commands import (
    handle_slack_progress_command,
    handle_slack_tasks_command,
    handle_slack_members_command,
    render_progress_bar,
)


@pytest.mark.unit
@pytest.mark.django_db
def test_render_progress_bar():
    bar_50 = render_progress_bar(50.0, length=10)
    assert "`█████░░░░░` 50.0%" in bar_50

    bar_100 = render_progress_bar(100.0, length=10)
    assert "`██████████` 100.0%" in bar_100


@pytest.mark.unit
@pytest.mark.django_db
def test_handle_slack_progress_command(db):
    user = User.objects.create(email="owner@civix.com", username="owner_civix")
    workspace = Workspace.objects.create(name="Civix WS", slug="civix-ws", owner=user)
    project = Project.objects.create(name="Civix Project", identifier="CIV", workspace=workspace, project_lead=user)

    state_backlog = State.objects.create(name="Backlog", group="backlog", project=project, workspace=workspace)
    state_done = State.objects.create(name="Done", group="completed", project=project, workspace=workspace)

    Issue.objects.create(name="Task 1", project=project, workspace=workspace, state=state_backlog, priority="high")
    Issue.objects.create(name="Task 2", project=project, workspace=workspace, state=state_done, priority="medium")

    result = handle_slack_progress_command(project, "civix-ws")

    assert result["response_type"] == "in_channel"
    assert len(result["blocks"]) > 0
    header_text = result["blocks"][0]["text"]["text"]
    assert "Civix Project" in header_text


@pytest.mark.unit
@pytest.mark.django_db
def test_handle_slack_tasks_command(db):
    from plane.db.models import IssueAssignee

    user = User.objects.create(email="dev@civix.com", username="dev_civix", first_name="Dev")
    workspace = Workspace.objects.create(name="Civix WS", slug="civix-ws", owner=user)
    project = Project.objects.create(name="Civix Project", identifier="CIV", workspace=workspace, project_lead=user)
    state = State.objects.create(name="In Progress", group="started", project=project, workspace=workspace)

    issue = Issue.objects.create(
        name="Fix Login Bug",
        project=project,
        workspace=workspace,
        state=state,
        priority="urgent",
        sequence_id=1,
    )
    IssueAssignee.objects.create(issue=issue, assignee=user, project=project, workspace=workspace)

    result = handle_slack_tasks_command(project, user=user)

    assert result["response_type"] == "in_channel"
    text_content = str(result["blocks"])
    assert "CIV-1" in text_content
    assert "Fix Login Bug" in text_content


@pytest.mark.unit
@pytest.mark.django_db
def test_handle_slack_members_command(db):
    user = User.objects.create(email="lead@civix.com", username="lead_civix", first_name="Lead")
    workspace = Workspace.objects.create(name="Civix WS", slug="civix-ws", owner=user)
    project = Project.objects.create(name="Civix Project", identifier="CIV", workspace=workspace, project_lead=user)

    ProjectMember.objects.create(project=project, workspace=workspace, member=user, role=20)

    result = handle_slack_members_command(project)

    assert result["response_type"] == "in_channel"
    text_content = str(result["blocks"])
    assert "Lead" in text_content
    assert "Admin" in text_content
