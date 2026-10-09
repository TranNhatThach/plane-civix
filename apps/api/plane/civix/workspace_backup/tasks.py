# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import logging
from celery import shared_task
from django.utils import timezone

from .exporter import export_workspace
from .restorer import restore_workspace

logger = logging.getLogger("plane.civix.backup")


@shared_task
def daily_auto_backup_all_workspaces():
    """
    Recurring Celery task scheduled daily at 02:00 Vietnam Time (UTC 19:00).
    Iterates through all active workspaces and generates an automated snapshot.
    """
    from plane.db.models import Workspace

    logger.info("Executing daily automated backup for all active workspaces...")
    active_workspaces = Workspace.objects.filter(deleted_at__isnull=True)
    count = 0
    errors = 0

    for ws in active_workspaces:
        try:
            logger.info("Auto-backing up workspace: %s (%s)", ws.slug, ws.id)
            export_workspace(str(ws.id), backup_type="auto")
            count += 1
        except Exception as e:
            errors += 1
            logger.error("Error auto-backing up workspace %s: %s", ws.slug, str(e))

    logger.info(
        "Daily automated workspace backups finished. Success: %d, Errors: %d", count, errors
    )
    return {"success": count, "errors": errors}


@shared_task
def async_create_workspace_backup(workspace_id: str, backup_type: str = "manual"):
    """Celery task to run workspace backup in the background."""
    return export_workspace(workspace_id, backup_type=backup_type)


@shared_task
def async_restore_workspace_backup(workspace_id: str, backup_id: str):
    """Celery task to run workspace restore in the background."""
    return restore_workspace(workspace_id, backup_id=backup_id)
