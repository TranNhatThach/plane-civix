# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
from django.core.management.base import BaseCommand, CommandError
from plane.db.models import Workspace
from plane.civix.workspace_backup import (
    export_workspace,
    restore_workspace,
    list_workspace_backups,
)


class Command(BaseCommand):
    help = "Civix Workspace-Level Backup & Restore CLI Tool"

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Workspace slug to backup or restore")
        parser.add_argument("--all", action="store_true", help="Backup all active workspaces")
        parser.add_argument("--list", action="store_true", help="List backups for the specified workspace")
        parser.add_argument("--restore", type=str, help="Backup ID to restore from")
        parser.add_argument("--type", type=str, default="manual", help="Backup type: manual, auto, pre-delete, pre-restore")

    def handle(self, *args, **options):
        slug = options.get("slug")
        is_all = options.get("all")
        is_list = options.get("list")
        restore_id = options.get("restore")
        backup_type = options.get("type", "manual")

        if is_all:
            workspaces = Workspace.objects.filter(deleted_at__isnull=True)
            self.stdout.write(self.style.NOTICE(f"Found {workspaces.count()} active workspaces. Starting backup..."))
            success = 0
            for ws in workspaces:
                try:
                    manifest = export_workspace(str(ws.id), backup_type=backup_type)
                    self.stdout.write(self.style.SUCCESS(f"  [OK] {ws.slug} -> {manifest['filename']} ({manifest['file_size_human']})"))
                    success += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  [ERR] {ws.slug} -> {str(e)}"))
            self.stdout.write(self.style.SUCCESS(f"Finished: {success}/{workspaces.count()} workspaces backed up."))
            return

        if not slug:
            raise CommandError("Please specify --slug <workspace_slug> or --all")

        workspace = Workspace.all_objects.filter(slug=slug).first()
        if not workspace:
            raise CommandError(f"Workspace with slug '{slug}' not found.")

        if is_list:
            backups = list_workspace_backups(str(workspace.id))
            self.stdout.write(self.style.NOTICE(f"Backups for workspace '{workspace.name}' ({workspace.slug}):"))
            if not backups:
                self.stdout.write("  No backups found.")
                return
            for idx, b in enumerate(backups, 1):
                self.stdout.write(
                    f"  [{idx}] {b.get('created_at')} | {b.get('backup_type')} | {b.get('file_size_human')} | {b.get('backup_id')}"
                )
            return

        if restore_id:
            self.stdout.write(self.style.WARNING(f"Restoring workspace '{workspace.slug}' from backup '{restore_id}'..."))
            try:
                res = restore_workspace(str(workspace.id), restore_id)
                self.stdout.write(self.style.SUCCESS(f"Successfully restored {res['total_restored']} records!"))
            except Exception as e:
                raise CommandError(f"Restore failed: {str(e)}")
            return

        # Default action: Create backup
        self.stdout.write(self.style.NOTICE(f"Creating backup for '{workspace.slug}'..."))
        try:
            manifest = export_workspace(str(workspace.id), backup_type=backup_type)
            self.stdout.write(self.style.SUCCESS(f"Backup created: {manifest['filename']}"))
            self.stdout.write(self.style.SUCCESS(f"Size: {manifest['file_size_human']} | Total records: {manifest['total_records']}"))
        except Exception as e:
            raise CommandError(f"Backup failed: {str(e)}")
