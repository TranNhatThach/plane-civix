from unittest.mock import patch, MagicMock
import pytest

from plane.bgtasks.slack_publisher import (
    send_slack_webhook,
    format_slack_issue_created,
    format_slack_issue_updated,
    format_slack_comment_added,
    dispatch_slack_event,
)


@pytest.mark.unit
def test_format_slack_issue_created():
    mock_project = MagicMock()
    mock_project.name = "Civix Project"
    mock_project.identifier = "CIVIX"
    mock_project.id = "proj-1"
    mock_project.workspace.slug = "civix"

    mock_assignee = MagicMock()
    mock_assignee.display_name = "John Dev"

    mock_issue = MagicMock()
    mock_issue.sequence_id = 101
    mock_issue.name = "Implement Slack Webhook Bot"
    mock_issue.priority = "high"
    mock_issue.state.name = "In Progress"
    mock_issue.assignees.all.return_value = [mock_assignee]
    mock_issue.created_by.display_name = "Alice"
    mock_issue.description_html = "<p>Slack integration description</p>"
    mock_issue.id = "issue-uuid-101"

    payload = format_slack_issue_created(mock_issue, mock_project, "http://localhost:3000")

    assert "blocks" in payload
    blocks = payload["blocks"]
    assert len(blocks) >= 4
    assert blocks[0]["text"]["text"] == "📌 New Issue Created in Civix Project"
    assert "[CIVIX-101] Implement Slack Webhook Bot" in blocks[1]["text"]["text"]
    assert "John Dev" in str(blocks[2]["fields"])
    assert "In Progress" in str(blocks[2]["fields"])


@pytest.mark.unit
def test_format_slack_issue_updated():
    mock_project = MagicMock()
    mock_project.name = "Civix Project"
    mock_project.identifier = "CIVIX"
    mock_project.id = "proj-1"
    mock_project.workspace.slug = "civix"

    mock_issue = MagicMock()
    mock_issue.sequence_id = 101
    mock_issue.name = "Implement Slack Webhook Bot"
    mock_issue.id = "issue-uuid-101"

    payload = format_slack_issue_updated(
        mock_issue, mock_project, "Backlog", "Done", "Bob", "http://localhost:3000"
    )

    assert "blocks" in payload
    blocks = payload["blocks"]
    assert blocks[0]["text"]["text"] == "🔄 Status Update in Civix Project"
    assert "Backlog" in str(blocks[2]["fields"])
    assert "Done" in str(blocks[2]["fields"])
    assert "Bob" in str(blocks[3]["elements"])


@pytest.mark.unit
def test_format_slack_comment_added():
    mock_project = MagicMock()
    mock_project.name = "Civix Project"
    mock_project.identifier = "CIVIX"
    mock_project.id = "proj-1"
    mock_project.workspace.slug = "civix"

    mock_issue = MagicMock()
    mock_issue.sequence_id = 101
    mock_issue.name = "Implement Slack Webhook Bot"
    mock_issue.id = "issue-uuid-101"

    mock_comment = MagicMock()
    mock_comment.comment_html = "<p>Looks good to me!</p>"

    payload = format_slack_comment_added(
        mock_issue, mock_project, mock_comment, "Charlie", "http://localhost:3000"
    )

    assert "blocks" in payload
    blocks = payload["blocks"]
    assert blocks[0]["text"]["text"] == "💬 New Comment in Civix Project"
    assert "Charlie" in blocks[2]["text"]["text"]
    assert "Looks good to me!" in blocks[2]["text"]["text"]


@pytest.mark.unit
@patch("plane.bgtasks.slack_publisher.requests.post")
def test_send_slack_webhook_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "ok"
    mock_post.return_value = mock_response

    test_payload = {"text": "Hello Slack"}
    success, res = send_slack_webhook("https://hooks.slack.com/services/test/webhook", test_payload)

    assert success is True
    assert res == "ok"
    mock_post.assert_called_once_with(
        "https://hooks.slack.com/services/test/webhook",
        json=test_payload,
        timeout=10,
    )


@pytest.mark.unit
@patch("plane.bgtasks.slack_publisher.requests.post")
def test_send_slack_webhook_error(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "invalid_payload"
    mock_post.return_value = mock_response

    success, res = send_slack_webhook("https://hooks.slack.com/services/test/webhook", {"text": "test"})

    assert success is False
    assert "HTTP 400" in res


@pytest.mark.unit
def test_check_slack_command_permission():
    from plane.bgtasks.slack_bot.permissions import check_slack_command_permission

    mock_automation = MagicMock()
    mock_automation.events = {
        "restrict_commands": True,
        "allowed_users": ["U123456", "@nam_dev", "UADMIN"],
    }

    # 1. Allowed by Slack User ID
    allowed, msg = check_slack_command_permission(mock_automation, "U123456", "someuser")
    assert allowed is True
    assert msg == ""

    # 2. Allowed by username with @
    allowed, msg = check_slack_command_permission(mock_automation, "U999999", "nam_dev")
    assert allowed is True
    assert msg == ""

    # 3. Denied for unknown user
    allowed, msg = check_slack_command_permission(mock_automation, "U_UNKNOWN", "intruder")
    assert allowed is False
    assert "Quyền truy cập bị từ chối" in msg
    assert "U_UNKNOWN" in msg

    # 4. Allowed when restriction is disabled
    mock_automation.events = {"restrict_commands": False}
    allowed, msg = check_slack_command_permission(mock_automation, "U_UNKNOWN", "intruder")
    assert allowed is True


@pytest.mark.unit
def test_render_slack_block_kit_dynamic_url():
    from plane.app.agent.adapters.slack_adapter import render_slack_block_kit

    agent_result = {
        "action_taken": "tool_get_progress",
        "text": "Báo cáo tiến độ",
        "data": {
            "project_name": "Civix Core",
            "completion_percentage": 75,
            "completed_tasks": 3,
            "total_tasks": 4,
            "started_tasks": 1,
            "backlog_tasks": 0,
            "overdue_tasks": 0,
        },
    }

    payload = render_slack_block_kit(
        agent_result,
        user_name="nam",
        app_url="https://plane.civix.vn",
        workspace_slug="civix-ws",
        project_id="proj-123",
    )

    blocks_str = str(payload["blocks"])
    assert "https://plane.civix.vn/civix-ws/projects/proj-123/issues" in blocks_str
    assert "http://localhost/" not in blocks_str

