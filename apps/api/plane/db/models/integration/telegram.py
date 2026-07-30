# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Django imports
from django.db import models

# Module imports
from plane.db.models.project import ProjectBaseModel


class TelegramAutomation(ProjectBaseModel):
    """
    Model storing Telegram Bot notification and automation settings for a Project.
    """
    bot_token = models.CharField(max_length=300)
    chat_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    # Event subscription flags: issue_created, issue_updated, comment_added, etc.
    events = models.JSONField(
        default=dict,
        blank=True,
        help_text="Event subscriptions config, e.g. {'issue_created': True, 'issue_updated': True, 'comment_added': True}"
    )

    workspace_integration = models.ForeignKey(
        "db.WorkspaceIntegration",
        related_name="telegram_automations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Telegram Bot for Project <{self.project.name}> ({self.chat_id})"

    class Meta:
        verbose_name = "Telegram Automation"
        verbose_name_plural = "Telegram Automations"
        db_table = "telegram_automations"
        ordering = ("-created_at",)
