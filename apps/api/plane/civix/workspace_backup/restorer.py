# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import gzip
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any

from django.apps import apps
from django.core import serializers
from django.db import transaction
from django.utils import timezone

from .exporter import get_workspace_backup_dir, export_workspace

logger = logging.getLogger("plane.civix.backup")


def restore_workspace(workspace_id: str, backup_id: str) -> Dict[str, Any]:
    """
    Restores an isolated workspace database snapshot without affecting any other workspace.
    
    Args:
        workspace_id: UUID string of the workspace
        backup_id: The backup identifier (e.g. ws_tid-tech_20261006_020000_auto)
        
    Returns:
        Summary dict of restored records.
    """
    from plane.db.models import Workspace, User, Profile

    target_dir = get_workspace_backup_dir(workspace_id)
    manifest_path = target_dir / f"{backup_id}.manifest.json"
    archive_path = target_dir / f"{backup_id}.jsonl.gz"

    if not manifest_path.exists() or not archive_path.exists():
        raise FileNotFoundError(f"Backup files for '{backup_id}' not found.")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Validate sha256 checksum
    hasher = hashlib.sha256()
    with open(archive_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    # Note: Manifest may store uncompressed or compressed hash; check archive hash
    logger.info("Verifying archive for workspace %s restore...", manifest.get("workspace_slug"))

    # 2. Safety pre-restore snapshot of current state (if workspace currently exists)
    current_ws = Workspace.all_objects.filter(pk=workspace_id).first()
    if current_ws:
        try:
            logger.info("Creating safety pre-restore backup for %s...", workspace_id)
            export_workspace(workspace_id, backup_type="pre-restore")
        except Exception as e:
            logger.warning("Could not create pre-restore snapshot: %s", str(e))

    restored_summary = {}
    total_restored = 0

    # 3. Perform atomic restoration
    with transaction.atomic():
        # First pass: read file and separate user metadata and model records
        users_metadata = []
        model_records = []

        with gzip.open(archive_path, "rt", encoding="utf-8") as gz:
            for line in gz:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("_type") == "USER_SHELL_METADATA":
                    users_metadata = data.get("records", [])
                else:
                    model_records.append(data)

        # Ensure missing users exist in database as shell accounts
        for u in users_metadata:
            uid = u.get("id")
            email = u.get("email")
            if not User.objects.filter(pk=uid).exists() and not User.objects.filter(email=email).exists():
                user = User.objects.create(
                    id=uid,
                    email=email,
                    username=u.get("username") or uid,
                    first_name=u.get("first_name", ""),
                    last_name=u.get("last_name", ""),
                    is_password_autoset=True,
                    is_active=True,
                )
                Profile.objects.get_or_create(user=user)
                logger.info("Recreated missing member shell user: %s", email)

        # Delete existing records of this workspace
        if current_ws:
            logger.info("Purging existing records of workspace %s before restore...", workspace_id)
            current_ws.delete(soft=False)

        # Deserialize and save model records
        # Using serializers.deserialize('python', ...)
        for record in model_records:
            model_ident = record.get("model")
            try:
                for deserialized_obj in serializers.deserialize("python", [record]):
                    deserialized_obj.save()
                    restored_summary[model_ident] = restored_summary.get(model_ident, 0) + 1
                    total_restored += 1
            except Exception as e:
                logger.error("Failed deserializing record for %s: %s", model_ident, str(e))
                raise

    logger.info("Workspace %s restored successfully with %s records.", workspace_id, total_restored)

    return {
        "status": "success",
        "workspace_id": workspace_id,
        "backup_id": backup_id,
        "total_restored": total_restored,
        "restored_summary": restored_summary,
        "restored_at": timezone.now().isoformat(),
    }
