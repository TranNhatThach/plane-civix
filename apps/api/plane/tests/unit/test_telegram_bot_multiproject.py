from unittest.mock import patch, MagicMock
import pytest

from plane.bgtasks.telegram_bot.task_handlers import (
    handle_tasks_list,
    handle_search_query,
    handle_task_query,
    handle_create_task,
)
from plane.bgtasks.telegram_bot.ai_handlers import handle_ai_ask
from plane.bgtasks.telegram_bot.summary_handlers import handle_workspace_summary


from plane.db.models import Workspace, Project


@pytest.mark.unit
def test_handle_tasks_list_workspace():
    mock_workspace = MagicMock(spec=Workspace)
    mock_workspace.name = "Civix Workspace"
    mock_workspace.slug = "civix"

    mock_project = MagicMock(spec=Project)
    mock_project.name = "Civix Core"
    mock_project.identifier = "CIVIX"
    mock_project.workspace = mock_workspace
    mock_project.id = "proj-1"

    mock_issue = MagicMock()
    mock_issue.sequence_id = 101
    mock_issue.name = "Fix login crash"
    mock_issue.state.name = "In Progress"
    mock_issue.project = mock_project
    mock_issue.id = "issue-1"

    with patch("plane.bgtasks.telegram_bot.task_handlers.Issue.objects") as mock_issue_objs, \
         patch("plane.bgtasks.telegram_bot.task_handlers.Project.objects") as mock_proj_objs:

        mock_proj_objs.filter.return_value.order_by.return_value = [mock_project]
        mock_qs = MagicMock()
        mock_qs.exclude.return_value.select_related.return_value.order_by.return_value = [mock_issue]
        mock_qs.exists.return_value = True
        mock_issue_objs.filter.return_value = mock_qs

        res = handle_tasks_list(mock_workspace, "http://localhost:3000")
        assert "Danh sách Task đang mở" in res
        assert "CIVIX-101" in res
        assert "Fix login crash" in res


@pytest.mark.unit
def test_handle_workspace_summary():
    mock_workspace = MagicMock(spec=Workspace)
    mock_workspace.name = "Civix Workspace"

    mock_project = MagicMock(spec=Project)
    mock_project.name = "Civix Core"
    mock_project.identifier = "CIVIX"

    with patch("plane.bgtasks.telegram_bot.summary_handlers.Issue.objects") as mock_issue_objs, \
         patch("plane.bgtasks.telegram_bot.summary_handlers.Project.objects") as mock_proj_objs:

        mock_issue_objs.filter.return_value.count.return_value = 10
        mock_proj_objs.filter.return_value = [mock_project]

        res = handle_workspace_summary(mock_workspace)
        assert "Báo cáo Tiến độ Workspace: Civix Workspace" in res
        assert "Civix Core" in res
        assert "CIVIX" in res


@pytest.mark.unit
def test_handle_ai_ask_multi_project():
    mock_workspace = MagicMock()
    mock_workspace.name = "Civix Workspace"

    mock_project = MagicMock()
    mock_project.name = "Civix Core"
    mock_project.identifier = "CIVIX"

    mock_issue = MagicMock()
    mock_issue.sequence_id = 1
    mock_issue.name = "Feature Telegram Bot"
    mock_issue.state.name = "In Progress"
    mock_issue.project = mock_project
    mock_issue.assignees.all.return_value = []

    with patch("plane.bgtasks.telegram_bot.ai_handlers.Project.objects") as mock_proj_objs, \
         patch("plane.bgtasks.telegram_bot.ai_handlers.Issue.objects") as mock_issue_objs, \
         patch("plane.bgtasks.telegram_bot.ai_handlers.get_llm_config") as mock_llm_cfg, \
         patch("plane.bgtasks.telegram_bot.ai_handlers.get_llm_response") as mock_llm_resp:

        mock_proj_objs.filter.return_value = [mock_project]
        mock_qs = MagicMock()
        mock_qs.select_related.return_value.prefetch_related.return_value.order_by.return_value = [mock_issue]
        mock_issue_objs.filter.return_value = mock_qs

        mock_llm_cfg.return_value = ("fake_key", "gpt-4o", "openai", None)
        mock_llm_resp.return_value = ("Dự án hiện có 1 task đang thực hiện.", None)

        res = handle_ai_ask(mock_workspace, "Tiến độ thế nào?")
        assert "Plane AI Assistant (gpt-4o)" in res
        assert "Dự án hiện có 1 task đang thực hiện." in res


from plane.bgtasks.telegram_bot.permissions import check_command_permission


@pytest.mark.unit
def test_permission_allowed_by_id():
    automation = MagicMock()
    automation.events = {"restrict_create": True, "allowed_creators": ["10001"]}
    msg = {"from": {"id": 10001, "username": "valid_user", "first_name": "Valid"}}
    allowed, err = check_command_permission(automation, msg, "/create")
    assert allowed is True
    assert err == ""


@pytest.mark.unit
def test_permission_denied_unauthorized_id():
    automation = MagicMock()
    automation.events = {"restrict_create": True, "allowed_creators": ["10001"]}
    msg = {"from": {"id": 99999, "username": "unauthorized_user", "first_name": "Attacker"}}
    allowed, err = check_command_permission(automation, msg, "/create")
    assert allowed is False
    assert "Quyền truy cập bị từ chối" in err
    assert "99999" in err


@pytest.mark.unit
def test_permission_allowed_by_username():
    automation = MagicMock()
    automation.events = {"restrict_create": True, "allowed_creators": ["@admin_user"]}
    msg = {"from": {"id": 88888, "username": "admin_user", "first_name": "Admin"}}
    allowed, err = check_command_permission(automation, msg, "/newtask")
    assert allowed is True
    assert err == ""


@pytest.mark.unit
def test_permission_denied_unauthorized_username():
    automation = MagicMock()
    automation.events = {"restrict_create": True, "allowed_creators": ["@admin_user"]}
    msg = {"from": {"id": 88888, "username": "random_user", "first_name": "Random"}}
    allowed, err = check_command_permission(automation, msg, "/create")
    assert allowed is False
    assert "Quyền truy cập bị từ chối" in err


@pytest.mark.unit
def test_permission_unrestricted_default():
    automation = MagicMock()
    automation.events = {}
    msg = {"from": {"id": 12345, "username": "any_user", "first_name": "Anyone"}}
    allowed, err = check_command_permission(automation, msg, "/create")
    assert allowed is True
    assert err == ""

