from unittest.mock import patch, MagicMock
import pytest

from plane.db.models import TelegramAutomation, Project
from plane.bgtasks.telegram_publisher import (
    send_telegram_message,
    format_issue_created_message,
    format_issue_updated_message,
    format_comment_added_message,
    dispatch_telegram_event,
)


@pytest.mark.unit
def test_format_issue_created_message():
    mock_project = MagicMock()
    mock_project.name = "Civix Project"
    mock_project.identifier = "CIVIX"
    mock_project.id = "proj-1"
    mock_project.workspace.slug = "civix"

    mock_assignee = MagicMock()
    mock_assignee.display_name = "John Dev"

    mock_issue = MagicMock()
    mock_issue.sequence_id = 42
    mock_issue.name = "Add Telegram Notification Bot"
    mock_issue.priority = "high"
    mock_issue.state.name = "In Progress"
    mock_issue.assignees.all.return_value = [mock_assignee]
    mock_issue.created_by.display_name = "Creator"
    mock_issue.description_html = "<p>Desc</p>"
    mock_issue.id = "123-uuid"

    message = format_issue_created_message(mock_issue, mock_project, "http://localhost:3000")

    assert "📌 <b>[CIVIX-42] New Task Created</b>" in message
    assert "Civix Project" in message
    assert "Add Telegram Notification Bot" in message
    assert "High" in message
    assert "In Progress" in message
    assert "John Dev" in message


@pytest.mark.unit
def test_format_issue_updated_message():
    mock_project = MagicMock()
    mock_project.name = "Civix Project"
    mock_project.identifier = "CIVIX"
    mock_project.id = "proj-1"
    mock_project.workspace.slug = "civix"

    mock_issue = MagicMock()
    mock_issue.sequence_id = 42
    mock_issue.name = "Add Telegram Notification Bot"
    mock_issue.id = "123-uuid"

    message = format_issue_updated_message(mock_issue, mock_project, "Backlog", "Done", "Actor", "http://localhost:3000")

    assert "🔄 <b>[CIVIX-42] Status Changed</b>" in message
    assert "Civix Project" in message
    assert "Backlog" in message
    assert "Done" in message


@pytest.mark.unit
@patch("plane.bgtasks.telegram_publisher.requests.post")
def test_send_telegram_message_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 100}}
    mock_post.return_value = mock_response

    success, _ = send_telegram_message("123456:bot_token", "-100123456", "<b>Test Message</b>")

    assert success is True
    mock_post.assert_called_once_with(
        "https://api.telegram.org/bot123456:bot_token/sendMessage",
        json={
            "chat_id": "-100123456",
            "text": "<b>Test Message</b>",
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )
