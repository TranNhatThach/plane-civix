# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports

# Django imports
from django.db import models

# Module imports
from plane.db.models.base import BaseModel
from plane.db.models.project import ProjectBaseModel


class SlackProjectSync(ProjectBaseModel):
    access_token = models.CharField(max_length=300)
    scopes = models.TextField()
    bot_user_id = models.CharField(max_length=50)
    webhook_url = models.URLField(max_length=1000)
    data = models.JSONField(default=dict)
    team_id = models.CharField(max_length=30)
    team_name = models.CharField(max_length=300)
    workspace_integration = models.ForeignKey(
        "db.WorkspaceIntegration", related_name="slack_syncs", on_delete=models.CASCADE
    )

    def __str__(self):
        """Return the repo name"""
        return f"{self.project.name}"

    class Meta:
        unique_together = ["team_id", "project"]
        verbose_name = "Slack Project Sync"
        verbose_name_plural = "Slack Project Syncs"
        db_table = "slack_project_syncs"
        ordering = ("-created_at",)


class SlackAutomation(ProjectBaseModel):
    """
    Model storing Slack Webhook notification settings and
    Socket Mode Bot/App tokens for a Project.
    """
    webhook_url = models.URLField(max_length=1000)
    channel_name = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Socket Mode tokens for /agent slash command
    bot_token = models.CharField(
        max_length=500, blank=True, null=True,
        help_text="Slack Bot User OAuth Token (xoxb-...). Get from OAuth & Permissions page."
    )
    app_token = models.CharField(
        max_length=500, blank=True, null=True,
        help_text="Slack App-Level Token (xapp-...). Get from Basic Information > App-Level Tokens."
    )

    # Event subscription flags: issue_created, issue_updated, comment_added, etc.
    events = models.JSONField(
        default=dict,
        blank=True,
        help_text="Event subscriptions config, e.g. {'issue_created': True, 'issue_updated': True, 'comment_added': True}"
    )

    workspace_integration = models.ForeignKey(
        "db.WorkspaceIntegration",
        related_name="slack_automations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Slack Automation for Project <{self.project.name}> ({self.webhook_url})"

    class Meta:
        verbose_name = "Slack Automation"
        verbose_name_plural = "Slack Automations"
        db_table = "slack_automations"
        ordering = ("-created_at",)


class SlackUserIntegration(BaseModel):
    """
    Maps a Slack User ID to a Plane User ID for Identity Resolution.
    """
    slack_user_id = models.CharField(max_length=64, unique=True, db_index=True)
    slack_team_id = models.CharField(max_length=64, blank=True, null=True)
    user = models.ForeignKey(
        "db.User",
        related_name="slack_user_integrations",
        on_delete=models.CASCADE
    )
    workspace = models.ForeignKey(
        "db.Workspace",
        related_name="slack_user_integrations",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "db.Project",
        related_name="slack_user_integrations",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Slack User Integration"
        verbose_name_plural = "Slack User Integrations"
        db_table = "slack_user_integrations"



class AgentChannelMapping(BaseModel):
    """
    Maps a Slack Channel to a Plane Workspace and optional Project.
    """
    slack_team_id = models.CharField(max_length=64, db_index=True)
    slack_channel_id = models.CharField(max_length=64, db_index=True)
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE)
    project = models.ForeignKey("db.Project", on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["slack_team_id", "slack_channel_id"]
        verbose_name = "Agent Channel Mapping"
        verbose_name_plural = "Agent Channel Mappings"
        db_table = "agent_channel_mappings"


class AgentConversation(BaseModel):
    """
    Stores short-term thread memory and context state for Agent conversations.
    """
    slack_channel_id = models.CharField(max_length=64, db_index=True)
    thread_ts = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    user = models.ForeignKey("db.User", on_delete=models.CASCADE)
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE)
    project = models.ForeignKey("db.Project", on_delete=models.SET_NULL, null=True, blank=True)
    last_intent = models.CharField(max_length=64, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Agent Conversation"
        verbose_name_plural = "Agent Conversations"
        db_table = "agent_conversations"
        ordering = ("-created_at",)



