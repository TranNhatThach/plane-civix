# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db import models
from plane.db.models.base import BaseModel


class AgentSession(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace", on_delete=models.CASCADE, related_name="agent_sessions"
    )
    user = models.ForeignKey(
        "db.User", on_delete=models.CASCADE, related_name="agent_sessions"
    )
    title = models.CharField(max_length=255, default="New Chat Session")

    class Meta:
        verbose_name = "Agent Session"
        verbose_name_plural = "Agent Sessions"
        db_table = "agent_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.id})"


class AgentMessage(BaseModel):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    )

    session = models.ForeignKey(
        AgentSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Agent Message"
        verbose_name_plural = "Agent Messages"
        db_table = "agent_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"


class AgentPageVector(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace", on_delete=models.CASCADE, related_name="agent_page_vectors"
    )
    page = models.ForeignKey(
        "db.Page", on_delete=models.CASCADE, related_name="vectors", null=True, blank=True
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Agent Page Vector"
        verbose_name_plural = "Agent Page Vectors"
        db_table = "agent_page_vectors"

    def __str__(self):
        return self.title
