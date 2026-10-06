# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import uuid
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.utils import timezone
from django.core.exceptions import ValidationError

from plane.db.models import (
    Workspace,
    WorkspaceMember,
    WorkspaceMemberInvite,
    Project,
    Issue,
    State,
    User,
    Profile,
)
from plane.authentication.adapter.base import CredentialAdapter
from plane.authentication.adapter.error import AuthenticationException
from plane.bgtasks.deletion_task import restore_workspace_objects
from plane.civix.workspace_backup import (
    export_workspace,
    restore_workspace,
    list_workspace_backups,
    prune_workspace_backups,
)


@pytest.mark.django_db
class TestInviteOnlySignupPolicy:
    """Tests that signup is invite-only for any domain (not just @civix.com.vn)."""

    def test_signup_blocked_without_invite_when_signup_disabled(self):
        class DummyAdapter(CredentialAdapter):
            provider = "email"
            def authenticate(self):
                return None

        adapter = DummyAdapter(request=MagicMock(), provider="email")

        # Non-invited gmail account should be rejected
        with patch("plane.authentication.adapter.base.get_configuration_value", return_value=("0",)):
            with pytest.raises(AuthenticationException) as exc_info:
                adapter._CredentialAdapter__check_signup("external.client@gmail.com")
            assert exc_info.value.error_code == 5015

    def test_signup_allowed_with_invite(self):
        class DummyAdapter(CredentialAdapter):
            provider = "email"
            def authenticate(self):
                return None

        adapter = DummyAdapter(request=MagicMock(), provider="email")

        ws = Workspace.objects.create(name="TID TECH", slug="tid-tech-test")
        invite_email = "tidtech.engineer@gmail.com"
        WorkspaceMemberInvite.objects.create(
            workspace=ws,
            email=invite_email,
            token="token123",
            role=15,
        )

        with patch("plane.authentication.adapter.base.get_configuration_value", return_value=("0",)):
            # Should not raise exception
            assert adapter._CredentialAdapter__check_signup(invite_email) is True


@pytest.mark.django_db
class TestTemporaryPasswordHandoverPolicy:
    """Tests temporary password expiry and password change requirement."""

    def test_expired_temporary_password_raises_exception(self):
        from plane.authentication.provider.credentials.email import EmailProvider

        user = User.objects.create(
            email="expired.client@tidtech.vn",
            username="expired_client",
            is_active=True,
        )
        user.set_password("OldTempPass123!")
        user.save()

        # Set expired temporary password
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.must_change_password = True
        profile.temp_password_expires_at = timezone.now() - timedelta(days=1)
        profile.save()

        req = MagicMock()
        provider = EmailProvider(request=req, key=user.email, code="OldTempPass123!", is_signup=False)

        with patch("plane.authentication.provider.credentials.email.get_configuration_value", return_value=("1",)):
            with pytest.raises(AuthenticationException) as exc_info:
                provider.set_user_data({"email": user.email})
            assert exc_info.value.error_code == 5195  # TEMP_PASSWORD_EXPIRED

    def test_valid_temp_password_allowed(self):
        from plane.authentication.provider.credentials.email import EmailProvider

        user = User.objects.create(
            email="valid.client@tidtech.vn",
            username="valid_client",
            is_active=True,
        )
        user.set_password("ValidTempPass123!")
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.must_change_password = True
        profile.temp_password_expires_at = timezone.now() + timedelta(days=5)
        profile.save()

        req = MagicMock()
        provider = EmailProvider(request=req, key=user.email, code="ValidTempPass123!", is_signup=False)

        with patch("plane.authentication.provider.credentials.email.get_configuration_value", return_value=("1",)):
            provider.set_user_data({"email": user.email})
            assert provider.user_data["email"] == user.email


@pytest.mark.django_db
class TestWorkspaceTrashAndRestoration:
    """Tests 15-day workspace trash retention and restore capability."""

    def test_workspace_restore_un_deletes_records(self):
        ws = Workspace.objects.create(name="Trash Corp", slug="trash-corp")
        proj = Project.objects.create(name="Proj 1", workspace=ws)

        delete_time = timezone.now()
        ws.deleted_at = delete_time
        ws.save()
        proj.deleted_at = delete_time
        proj.save()

        assert Workspace.objects.filter(slug="trash-corp").count() == 0

        # Restore
        success = restore_workspace_objects(str(ws.id))
        assert success is True

        # Verify both workspace and project restored
        ws.refresh_from_db()
        proj.refresh_from_db()
        assert ws.deleted_at is None
        assert proj.deleted_at is None


@pytest.mark.django_db
class TestWorkspaceBackupEngine:
    """Tests isolated export and restore for single workspace."""

    def test_export_and_restore_isolated_workspace(self, tmp_path):
        with patch("plane.civix.workspace_backup.exporter.get_workspace_backup_root_dir", return_value=tmp_path):
            # Create two separate workspaces
            civix_ws = Workspace.objects.create(name="CIVIX Workspace", slug="civix-core")
            civix_proj = Project.objects.create(name="Core Dev", workspace=civix_ws)

            tid_ws = Workspace.objects.create(name="TID TECH", slug="tid-tech-corp")
            tid_proj = Project.objects.create(name="TID App", workspace=tid_ws)

            # Export TID TECH workspace
            manifest = export_workspace(str(tid_ws.id), backup_type="manual")
            assert manifest["workspace_slug"] == "tid-tech-corp"
            assert manifest["total_records"] > 0

            # List backups
            backups = list_workspace_backups(str(tid_ws.id))
            assert len(backups) == 1

            # Restore TID TECH from backup
            res = restore_workspace(str(tid_ws.id), manifest["backup_id"])
            assert res["status"] == "success"

            # Check that CIVIX workspace was untouched!
            civix_ws.refresh_from_db()
            civix_proj.refresh_from_db()
            assert civix_ws.name == "CIVIX Workspace"
            assert civix_proj.name == "Core Dev"
