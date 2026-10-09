# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import gzip
import json
import logging
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.db import models
from django.utils import timezone

logger = logging.getLogger("plane.civix.backup")

# Ordered model list for dependency-safe export and restore
WORKSPACE_EXPORT_MODELS = [
    # 1. Root Workspace
    ("db", "Workspace"),
    # 2. Workspace settings & memberships
    ("db", "WorkspaceMember"),
    ("db", "WorkspaceMemberInvite"),
    ("db", "WorkspaceTheme"),
    ("db", "WorkspaceUserProperties"),
    ("db", "WorkspaceHomePreference"),
    ("db", "WorkspaceUserPreference"),
    # 3. Projects & Project Members
    ("db", "Project"),
    ("db", "ProjectIdentifier"),
    ("db", "ProjectMember"),
    ("db", "ProjectMemberInvite"),
    ("db", "ProjectUserProperty"),
    # 4. Work item categories & attributes
    ("db", "State"),
    ("db", "Label"),
    ("db", "IssueType"),
    ("db", "Estimate"),
    ("db", "EstimatePoint"),
    # 5. Iterations, Modules & Pages
    ("db", "Cycle"),
    ("db", "Module"),
    ("db", "Page"),
    ("db", "ProjectPage"),
    ("db", "PageLabel"),
    ("db", "PageVersion"),
    ("db", "PageLog"),
    # 6. Issues & Work items
    ("db", "Issue"),
    ("db", "IssueSequence"),
    ("db", "DraftIssue"),
    # 7. Issue associations
    ("db", "IssueAssignee"),
    ("db", "IssueLabel"),
    ("db", "IssueSubscriber"),
    ("db", "CycleIssue"),
    ("db", "ModuleIssue"),
    ("db", "ModuleMember"),
    ("db", "ModuleLink"),
    # 8. Activity, Discussions & Attachments
    ("db", "IssueComment"),
    ("db", "IssueActivity"),
    ("db", "IssueLink"),
    ("db", "IssueAttachment"),
    ("db", "IssueReaction"),
    ("db", "CommentReaction"),
    ("db", "IssueBlocker"),
    ("db", "IssueRelation"),
    ("db", "IssueVote"),
    ("db", "IssueVersion"),
    ("db", "IssueDescriptionVersion"),
    # 9. Assets, Webhooks & Misc
    ("db", "FileAsset"),
    ("db", "Webhook"),
    ("db", "WebhookLog"),
    ("db", "AnalyticView"),
    ("db", "UserFavorite"),
]


def get_workspace_backup_root_dir() -> Path:
    """Returns the base directory where workspace backups are stored."""
    env_dir = os.environ.get("WORKSPACE_BACKUP_DIR")
    if env_dir:
        base_path = Path(env_dir)
    else:
        # Default fallback to $HOME/plane-backups/workspaces
        base_path = Path.home() / "plane-backups" / "workspaces"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def get_workspace_backup_dir(workspace_id: str) -> Path:
    """Returns the dedicated directory for a specific workspace."""
    root = get_workspace_backup_root_dir()
    ws_dir = root / str(workspace_id)
    ws_dir.mkdir(parents=True, exist_ok=True)
    return ws_dir


def export_workspace(workspace_id: str, backup_type: str = "manual") -> Dict[str, Any]:
    """
    Exports an entire workspace's database records into an isolated .jsonl.gz archive.
    
    Args:
        workspace_id: UUID string of the workspace
        backup_type: 'auto' | 'manual' | 'pre-delete' | 'pre-restore'
        
    Returns:
        Manifest dictionary with backup details.
    """
    from plane.db.models import Workspace, WorkspaceMember, User

    # Fetch workspace using all_objects to allow backup before purge
    workspace = Workspace.all_objects.filter(pk=workspace_id).first()
    if not workspace:
        raise ValueError(f"Workspace with ID {workspace_id} not found.")

    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    backup_id = f"ws_{workspace.slug}_{timestamp}_{backup_type}"
    target_dir = get_workspace_backup_dir(workspace_id)
    archive_path = target_dir / f"{backup_id}.jsonl.gz"
    manifest_path = target_dir / f"{backup_id}.manifest.json"

    logger.info("Starting workspace backup: %s (Type: %s)", backup_id, backup_type)

    # 1. Collect Users associated with this workspace
    member_user_ids = list(
        WorkspaceMember.all_objects.filter(workspace_id=workspace.id).values_list("member_id", flat=True)
    )
    if workspace.owner_id and workspace.owner_id not in member_user_ids:
        member_user_ids.append(workspace.owner_id)

    users_data = []
    for u in User.objects.filter(pk__in=member_user_ids):
        users_data.append({
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "display_name": getattr(u, "display_name", "") or u.email,
            "avatar": getattr(u, "avatar", "") or "",
        })

    tables_summary = {"users_metadata": len(users_data)}
    total_records = len(users_data)

    with gzip.open(archive_path, "wt", encoding="utf-8") as gz_file:
        # Header: write user metadata line
        user_meta_line = json.dumps({"_type": "USER_SHELL_METADATA", "records": users_data}) + "\n"
        gz_file.write(user_meta_line)

        # Iterate over models
        for app_label, model_name in WORKSPACE_EXPORT_MODELS:
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            # Query records for this workspace
            manager = getattr(model, "all_objects", model.objects)
            qs = None

            if model_name == "Workspace":
                qs = manager.filter(pk=workspace.id)
            elif hasattr(model, "workspace") or any(f.name == "workspace" for f in model._meta.fields):
                qs = manager.filter(workspace_id=workspace.id)
            elif hasattr(model, "issue"):
                # Child of issue (IssueBlocker, IssueRelation, IssueReaction, etc.)
                qs = manager.filter(issue__project__workspace_id=workspace.id)
            elif hasattr(model, "comment"):
                qs = manager.filter(comment__project__workspace_id=workspace.id)
            elif hasattr(model, "draft_issue"):
                qs = manager.filter(draft_issue__project__workspace_id=workspace.id)
            else:
                continue

            count = qs.count()
            if count == 0:
                continue

            # Serialize using Django python serializer in batches
            serialized_objects = serializers.serialize("python", qs)
            tables_summary[f"{app_label}.{model_name}"] = len(serialized_objects)
            total_records += len(serialized_objects)

            for record in serialized_objects:
                # Custom JSON encoder for datetime/UUID
                record_line = json.dumps(record, default=str) + "\n"
                gz_file.write(record_line)

    file_size = archive_path.stat().st_size
    hasher = hashlib.sha256()
    with open(archive_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    file_hash = hasher.hexdigest()

    manifest = {
        "backup_id": backup_id,
        "filename": f"{backup_id}.jsonl.gz",
        "workspace_id": str(workspace.id),
        "workspace_slug": workspace.slug,
        "workspace_name": workspace.name,
        "backup_type": backup_type,
        "created_at": timezone.now().isoformat(),
        "total_records": total_records,
        "tables_summary": tables_summary,
        "file_size_bytes": file_size,
        "file_size_human": f"{file_size / (1024 * 1024):.2f} MB" if file_size >= 1024*1024 else f"{file_size / 1024:.1f} KB",
        "sha256": file_hash,
        "app_version": "v1.6.0",
    }

    # Write manifest file
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info("Workspace backup completed successfully: %s (%s records)", backup_id, total_records)

    # Prune old backups to respect retention policy
    try:
        prune_workspace_backups(workspace_id)
    except Exception as e:
        logger.warning("Error during workspace backup pruning: %s", str(e))

    return manifest


def prune_workspace_backups(workspace_id: str, max_keep: int = None) -> int:
    """
    Enforces retention policy for a workspace's backups.
    Default: keep 45 most recent auto/manual backups, deletes older ones.
    """
    if max_keep is None:
        max_keep = int(os.environ.get("WORKSPACE_BACKUP_MAX_KEEP", 45))

    ws_dir = get_workspace_backup_dir(workspace_id)
    manifest_files = list(ws_dir.glob("*.manifest.json"))

    backups = []
    for mf in manifest_files:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
                backups.append((data.get("created_at", ""), data.get("backup_type", "manual"), mf))
        except Exception:
            continue

    # Filter auto and manual backups
    routine_backups = [b for b in backups if b[1] in ("auto", "manual")]
    routine_backups.sort(key=lambda x: x[0], reverse=True)

    pruned_count = 0
    if len(routine_backups) > max_keep:
        to_delete = routine_backups[max_keep:]
        for created_at, b_type, manifest_file in to_delete:
            archive_file = manifest_file.with_name(manifest_file.stem + ".jsonl.gz")
            if manifest_file.exists():
                manifest_file.unlink()
            if archive_file.exists():
                archive_file.unlink()
            pruned_count += 1
            logger.info("Pruned old workspace backup: %s", manifest_file.stem)

    return pruned_count
