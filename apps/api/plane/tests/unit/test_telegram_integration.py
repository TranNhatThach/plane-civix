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
    issue_data = {
        "id": "123-uuid",
        "project": "proj-uuid",
        "project_identifier": "CIVIX",
        "sequence_id": 42,
        "name": "Add Telegram Notification Bot",
        "priority": "high",
        "state_detail": {"name": "In Progress"},
        "assignee_details": [{"display_name": "John Dev"}],
    }

    message = format_issue_created_message(issue_data, "Civix Project", "http://localhost:3000")

    assert "📌 <b>New Issue in Civix Project</b>" in message
    assert "[CIVIX-42] Add Telegram Notification Bot" in message
    assert "High" in message
    assert "In Progress" in message
    assert "John Dev" in message


@pytest.mark.unit
def test_format_issue_updated_message():
    issue_data = {
        "project_identifier": "CIVIX",
        "sequence_id": 42,
        "name": "Add Telegram Notification Bot",
    }

    message = format_issue_updated_message(issue_data, "Backlog", "Done", "Civix Project")

    assert "🔄 <b>Status Update in Civix Project</b>" in message
    assert "CIVIX-42" in message
    assert "Backlog" in message
    assert "Done" in message


@pytest.mark.unit
@patch("plane.bgtasks.telegram_publisher.requests.post")
def test_send_telegram_message_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 100}}
    mock_post.return_value = mock_response

    success = send_telegram_message("123456:bot_token", "-100123456", "<b>Test Message</b>")

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
