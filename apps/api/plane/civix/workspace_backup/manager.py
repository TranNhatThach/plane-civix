# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .exporter import get_workspace_backup_dir, export_workspace, prune_workspace_backups
from .restorer import restore_workspace

logger = logging.getLogger("plane.civix.backup")


def list_workspace_backups(workspace_id: str) -> List[Dict[str, Any]]:
    """
    Returns a sorted list of all backups available for a given workspace.
    """
    ws_dir = get_workspace_backup_dir(workspace_id)
    manifest_files = list(ws_dir.glob("*.manifest.json"))

    backups = []
    for mf in manifest_files:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
                backups.append(data)
        except Exception as e:
            logger.warning("Could not read backup manifest %s: %s", mf.name, str(e))

    # Sort newest first
    backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return backups


def get_backup_manifest(workspace_id: str, backup_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the manifest of a specific backup.
    """
    target_dir = get_workspace_backup_dir(workspace_id)
    manifest_path = target_dir / f"{backup_id}.manifest.json"
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_backup_archive_path(workspace_id: str, backup_id: str) -> Optional[Path]:
    """
    Returns the file path of the compressed archive for downloading.
    """
    target_dir = get_workspace_backup_dir(workspace_id)
    archive_path = target_dir / f"{backup_id}.jsonl.gz"
    return archive_path if archive_path.exists() else None


def delete_workspace_backup(workspace_id: str, backup_id: str) -> bool:
    """
    Deletes both the manifest and the archive file for a backup.
    """
    target_dir = get_workspace_backup_dir(workspace_id)
    manifest_path = target_dir / f"{backup_id}.manifest.json"
    archive_path = target_dir / f"{backup_id}.jsonl.gz"

    deleted = False
    if manifest_path.exists():
        manifest_path.unlink()
        deleted = True
    if archive_path.exists():
        archive_path.unlink()
        deleted = True

    return deleted
