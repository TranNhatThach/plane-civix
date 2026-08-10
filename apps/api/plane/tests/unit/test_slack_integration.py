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
