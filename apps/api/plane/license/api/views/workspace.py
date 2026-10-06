# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import uuid
import secrets
import string
import logging

# Third party imports
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError, transaction
from django.db.models import OuterRef, Func, F
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import FileResponse

# Module imports
from plane.app.views.base import BaseAPIView
from plane.license.api.permissions import InstanceAdminPermission
from plane.db.models import Workspace, WorkspaceMember, Project, User, Profile
from plane.license.api.serializers import WorkspaceSerializer
from plane.utils.constants import RESTRICTED_WORKSPACE_SLUGS
from plane.bgtasks.workspace_seed_task import workspace_seed
from plane.bgtasks.workspace_handover_task import send_workspace_handover_email
from plane.bgtasks.deletion_task import restore_workspace_objects
from plane.civix.workspace_backup import (
    export_workspace,
    restore_workspace,
    list_workspace_backups,
    get_backup_manifest,
    get_backup_archive_path,
    delete_workspace_backup,
)

logger = logging.getLogger("plane.license")


def generate_secure_temporary_password(length: int = 16) -> str:
    """Generates a secure temporary password complying with complexity rules."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    chars += [secrets.choice(alphabet) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


class InstanceWorkSpaceAvailabilityCheckEndpoint(BaseAPIView):
    permission_classes = [InstanceAdminPermission]

    def get(self, request):
        slug = request.GET.get("slug", False)

        if not slug or slug == "":
            return Response(
                {"error": "Workspace Slug is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workspace = Workspace.objects.filter(slug__iexact=slug).exists() or slug in RESTRICTED_WORKSPACE_SLUGS
        return Response({"status": not workspace}, status=status.HTTP_200_OK)


class InstanceWorkSpaceEndpoint(BaseAPIView):
    model = Workspace
    serializer_class = WorkspaceSerializer
    permission_classes = [InstanceAdminPermission]

    def get(self, request):
        project_count = (
            Project.objects.filter(workspace_id=OuterRef("id"))
            .order_by()
            .annotate(count=Func(F("id"), function="Count"))
            .values("count")
        )

        member_count = (
            WorkspaceMember.objects.filter(workspace=OuterRef("id"), member__is_bot=False, is_active=True)
            .select_related("owner")
            .order_by()
            .annotate(count=Func(F("id"), function="Count"))
            .values("count")
        )

        workspaces = Workspace.objects.annotate(total_projects=project_count, total_members=member_count)

        # Add search functionality
        search = request.query_params.get("search", None)
        if search:
            workspaces = workspaces.filter(name__icontains=search)

        return self.paginate(
            request=request,
            queryset=workspaces,
            on_results=lambda results: WorkspaceSerializer(results, many=True).data,
            max_per_page=10,
            default_per_page=10,
        )

    def post(self, request):
        try:
            serializer = WorkspaceSerializer(data=request.data)

            slug = request.data.get("slug", False)
            name = request.data.get("name", False)
            admin_email = request.data.get("admin_email") or request.data.get("email", False)
            admin_name = request.data.get("admin_name", "").strip()

            if not name or not slug:
                return Response(
                    {"error": "Both name and slug are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not admin_email:
                return Response(
                    {"error": "Customer admin email (admin_email) is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            admin_email = str(admin_email).strip().lower()
            try:
                validate_email(admin_email)
            except ValidationError:
                return Response(
                    {"error": "Invalid email address format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(name) > 80 or len(slug) > 48:
                return Response(
                    {"error": "The maximum length for name is 80 and for slug is 48"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not serializer.is_valid():
                return Response(
                    [serializer.errors[error][0] for error in serializer.errors],
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                customer_user = User.objects.filter(email=admin_email).first()
                temp_password = None
                is_new_user = False

                if not customer_user:
                    is_new_user = True
                    temp_password = generate_secure_temporary_password(16)
                    customer_user = User.objects.create(
                        email=admin_email,
                        username=uuid.uuid4().hex,
                        first_name=admin_name or "",
                        is_email_verified=True,
                    )
                    customer_user.set_password(temp_password)
                    customer_user.save()
                    Profile.objects.create(
                        user=customer_user,
                        must_change_password=True,
                        temp_password_expires_at=timezone.now() + timezone.timedelta(days=7),
                    )
                else:
                    # User exists, update first name if provided and not set
                    if admin_name and not customer_user.first_name:
                        customer_user.first_name = admin_name
                        customer_user.save()

                # Assign customer admin as workspace owner
                workspace = serializer.save(owner=customer_user)

                # Add customer admin as Workspace Member with role 20 (Admin)
                _ = WorkspaceMember.objects.create(
                    workspace_id=workspace.id,
                    member=customer_user,
                    role=20,
                    company_role=request.data.get("company_role", "Admin"),
                )

            # Trigger workspace initialization tasks
            workspace_seed.delay(workspace.id)

            # Enqueue onboarding handover email
            base_url = request.build_absolute_uri("/").rstrip("/")
            send_workspace_handover_email.delay(
                email=admin_email,
                workspace_name=name,
                workspace_slug=slug,
                admin_name=admin_name,
                temp_password=temp_password,
                base_url=base_url,
            )

            response_data = dict(serializer.data)
            response_data["admin_email"] = admin_email
            response_data["is_new_user"] = is_new_user
            response_data["handover_email_queued"] = True

            return Response(response_data, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            if "already exists" in str(e):
                return Response(
                    {"slug": "The workspace with the slug already exists"},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Error creating workspace from instance admin: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstanceWorkSpaceHandoverResendEndpoint(BaseAPIView):
    permission_classes = [InstanceAdminPermission]

    def post(self, request, workspace_id):
        workspace = Workspace.objects.filter(pk=workspace_id).first()
        if not workspace:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        owner = workspace.owner
        if not owner:
            return Response({"error": "Workspace does not have an owner"}, status=status.HTTP_400_BAD_REQUEST)

        # Regenerate temporary password and reset expiration
        temp_password = generate_secure_temporary_password(16)
        owner.set_password(temp_password)
        owner.save()

        profile, _ = Profile.objects.get_or_create(user=owner)
        profile.must_change_password = True
        profile.temp_password_expires_at = timezone.now() + timezone.timedelta(days=7)
        profile.save()

        base_url = request.build_absolute_uri("/").rstrip("/")
        send_workspace_handover_email.delay(
            email=owner.email,
            workspace_name=workspace.name,
            workspace_slug=workspace.slug,
            admin_name=owner.first_name,
            temp_password=temp_password,
            base_url=base_url,
        )

        return Response({
            "message": f"Handover email with new temporary password resent to {owner.email}",
            "admin_email": owner.email,
        }, status=status.HTTP_200_OK)


class InstanceWorkSpaceTrashEndpoint(BaseAPIView):
    """Endpoints for managing the 15-day workspace trash retention."""
    permission_classes = [InstanceAdminPermission]

    def get(self, request):
        trashed_workspaces = Workspace.all_objects.filter(deleted_at__isnull=False).order_by("-deleted_at")
        results = []
        now = timezone.now()

        for ws in trashed_workspaces:
            elapsed_days = (now - ws.deleted_at).days
            days_remaining = max(0, 15 - elapsed_days)
            results.append({
                "id": str(ws.id),
                "name": ws.name,
                "slug": ws.slug,
                "deleted_at": ws.deleted_at.isoformat(),
                "days_remaining": days_remaining,
                "owner_email": ws.owner.email if ws.owner else None,
            })

        return Response(results, status=status.HTTP_200_OK)


class InstanceWorkSpaceRestoreEndpoint(BaseAPIView):
    """Restores a workspace from the trash within 15 days."""
    permission_classes = [InstanceAdminPermission]

    def post(self, request, workspace_id):
        success = restore_workspace_objects(workspace_id)
        if not success:
            return Response(
                {"error": "Workspace could not be restored or was not in trash"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Workspace restored successfully"}, status=status.HTTP_200_OK)


class InstanceWorkSpacePurgeEndpoint(BaseAPIView):
    """Permanently purges a workspace from trash."""
    permission_classes = [InstanceAdminPermission]

    def delete(self, request, workspace_id):
        ws = Workspace.all_objects.filter(pk=workspace_id, deleted_at__isnull=False).first()
        if not ws:
            return Response({"error": "Workspace not found in trash"}, status=status.HTTP_404_NOT_FOUND)

        ws.delete(soft=False)
        return Response({"message": f"Workspace {ws.slug} permanently purged"}, status=status.HTTP_200_OK)


class InstanceWorkSpaceBackupEndpoint(BaseAPIView):
    """Lists or triggers backup for a given workspace."""
    permission_classes = [InstanceAdminPermission]

    def get(self, request, workspace_id):
        ws = Workspace.all_objects.filter(pk=workspace_id).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        backups = list_workspace_backups(workspace_id)
        return Response(backups, status=status.HTTP_200_OK)

    def post(self, request, workspace_id):
        ws = Workspace.all_objects.filter(pk=workspace_id).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            manifest = export_workspace(workspace_id, backup_type="manual")
            return Response(manifest, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Failed to export workspace backup: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstanceWorkSpaceBackupDetailEndpoint(BaseAPIView):
    """Download, restore or delete a specific workspace backup."""
    permission_classes = [InstanceAdminPermission]

    def get(self, request, workspace_id, backup_id):
        # Download archive
        archive_path = get_backup_archive_path(workspace_id, backup_id)
        if not archive_path or not archive_path.exists():
            return Response({"error": "Backup file not found"}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(open(archive_path, "rb"), as_attachment=True, filename=archive_path.name)
        response["Content-Type"] = "application/gzip"
        return response

    def post(self, request, workspace_id, backup_id):
        # Restore backup
        manifest = get_backup_manifest(workspace_id, backup_id)
        if not manifest:
            return Response({"error": "Backup not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = restore_workspace(workspace_id, backup_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error restoring workspace %s: %s", workspace_id, str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, workspace_id, backup_id):
        # Delete backup
        deleted = delete_workspace_backup(workspace_id, backup_id)
        if not deleted:
            return Response({"error": "Backup not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"Backup {backup_id} deleted successfully"}, status=status.HTTP_200_OK)
