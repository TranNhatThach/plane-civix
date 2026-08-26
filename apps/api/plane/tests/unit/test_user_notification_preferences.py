# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from unittest.mock import MagicMock, patch
import pytest

from plane.db.models import User, UserNotificationPreference, Issue, Project, Workspace, State
from plane.bgtasks.email_notification_task import (
    send_instant_mention_email,
    send_instant_assigned_email,
)


@pytest.mark.unit
class TestUserNotificationPreferences:
    """Unit tests for user notification preferences and instant email triggers."""

    def test_default_user_notification_preference_fields(self, db):
        """Verify default values of all new preference fields."""
        user = User.objects.create(
            email="testuser@civix.com.vn",
            username="testuser",
            first_name="Test",
            last_name="User",
        )
        pref, created = UserNotificationPreference.objects.get_or_create(user=user)

        assert pref.email_instant_mention is True
        assert pref.email_instant_assigned is True
        assert pref.email_assigned is True
        assert pref.email_due_date is True
        assert pref.email_digest is False
        assert pref.notify_self_actions is False
        assert pref.mention is True
        assert pref.comment is True
        assert pref.state_change is True
        assert pref.property_change is True

    @patch("plane.bgtasks.email_notification_task.get_email_configuration")
    @patch("plane.bgtasks.email_notification_task.get_connection")
    @patch("plane.bgtasks.email_notification_task.EmailMultiAlternatives")
    def test_send_instant_mention_email_success(
        self, mock_email_class, mock_get_conn, mock_get_config, db
    ):
        """Test sending instant mention email to another user."""
        mock_get_config.return_value = (
            "smtp.gmail.com",
            587,
            "bot@civix.com.vn",
            "password",
            "1",
            "0",
            "Civix Bot <bot@civix.com.vn>",
            "http://localhost:3000",
        )
        mock_msg = MagicMock()
        mock_email_class.return_value = mock_msg

        actor = User.objects.create(
            email="sender@civix.com.vn",
            username="sender",
            first_name="Sender",
            last_name="Dev",
        )
        receiver = User.objects.create(
            email="receiver@civix.com.vn",
            username="receiver",
            first_name="Receiver",
            last_name="Lead",
        )
        workspace = Workspace.objects.create(name="Civix WS", slug="civix-ws", owner=actor)
        project = Project.objects.create(
            name="Civix Core", identifier="CIV", workspace=workspace, created_by=actor
        )
        state = State.objects.create(
            name="In Progress", color="#3b82f6", group="started", project=project, workspace=workspace
        )
        issue = Issue.objects.create(
            name="Fix critical bug",
            project=project,
            workspace=workspace,
            state=state,
            sequence_id=101,
            created_by=actor,
        )

        send_instant_mention_email(
            issue_id=str(issue.id),
            actor_id=str(actor.id),
            receiver_id=str(receiver.id),
            comment_text="<p>@receiver hãy kiểm tra giúp mình task này nhé!</p>",
        )

        mock_email_class.assert_called_once()
        call_kwargs = mock_email_class.call_args[1]
        assert call_kwargs["to"] == [receiver.email]
        assert "CIV-101" in call_kwargs["subject"]
        assert "Sender Dev đã nhắc tên bạn" in call_kwargs["subject"]
        mock_msg.send.assert_called_once()

    @patch("plane.bgtasks.email_notification_task.get_email_configuration")
    @patch("plane.bgtasks.email_notification_task.EmailMultiAlternatives")
    def test_send_instant_mention_email_anti_self_spam(
        self, mock_email_class, mock_get_config, db
    ):
        """Test that instant mention email does not send if actor == receiver."""
        mock_get_config.return_value = (
            "smtp.gmail.com",
            587,
            "bot@civix.com.vn",
            "password",
            "1",
            "0",
            "Civix Bot <bot@civix.com.vn>",
            "http://localhost:3000",
        )

        user = User.objects.create(
            email="self@civix.com.vn",
            username="selfuser",
            first_name="Self",
            last_name="User",
        )
        workspace = Workspace.objects.create(name="Civix WS", slug="civix-ws-2", owner=user)
        project = Project.objects.create(
            name="Civix Core", identifier="CIV", workspace=workspace, created_by=user
        )
        issue = Issue.objects.create(
            name="Self tagged issue",
            project=project,
            workspace=workspace,
            sequence_id=102,
            created_by=user,
        )

        # Actor and receiver are the same person
        send_instant_mention_email(
            issue_id=str(issue.id),
            actor_id=str(user.id),
            receiver_id=str(user.id),
            comment_text="@selfuser self mention",
        )

        # Must not call EmailMultiAlternatives
        mock_email_class.assert_not_called()

    @patch("plane.bgtasks.email_notification_task.get_email_configuration")
    @patch("plane.bgtasks.email_notification_task.get_connection")
    @patch("plane.bgtasks.email_notification_task.EmailMultiAlternatives")
    def test_send_instant_assigned_email_success(
        self, mock_email_class, mock_get_conn, mock_get_config, db
    ):
        """Test sending instant assign email when a user is assigned to an issue."""
        mock_get_config.return_value = (
            "smtp.gmail.com",
            587,
            "bot@civix.com.vn",
            "password",
            "1",
            "0",
            "Civix Bot <bot@civix.com.vn>",
            "http://localhost:3000",
        )
        mock_msg = MagicMock()
        mock_email_class.return_value = mock_msg

        actor = User.objects.create(
            email="manager@civix.com.vn",
            username="manager",
            first_name="Manager",
            last_name="Boss",
        )
        assignee = User.objects.create(
            email="dev@civix.com.vn",
            username="devmember",
            first_name="Dev",
            last_name="Staff",
        )
        workspace = Workspace.objects.create(name="Civix WS", slug="civix-ws-3", owner=actor)
        project = Project.objects.create(
            name="Civix Core", identifier="CIV", workspace=workspace, created_by=actor
        )
        state = State.objects.create(
            name="Todo", color="#e2e8f0", group="unstarted", project=project, workspace=workspace
        )
        issue = Issue.objects.create(
            name="Design API architecture",
            project=project,
            workspace=workspace,
            state=state,
            priority="high",
            sequence_id=103,
            created_by=actor,
        )

        send_instant_assigned_email(
            issue_id=str(issue.id),
            actor_id=str(actor.id),
            receiver_id=str(assignee.id),
        )

        mock_email_class.assert_called_once()
        call_kwargs = mock_email_class.call_args[1]
        assert call_kwargs["to"] == [assignee.email]
        assert "CIV-103" in call_kwargs["subject"]
        assert "Bạn được giao việc mới" in call_kwargs["subject"]
        mock_msg.send.assert_called_once()
