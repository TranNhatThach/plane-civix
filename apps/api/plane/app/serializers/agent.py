# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import serializers
from plane.db.models import AgentSession, AgentMessage


class AgentMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMessage
        fields = ("id", "session", "role", "content", "metadata", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class AgentSessionSerializer(serializers.ModelSerializer):
    messages = AgentMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AgentSession
        fields = ("id", "workspace", "user", "title", "messages", "created_at", "updated_at")
        read_only_fields = ("id", "workspace", "user", "created_at", "updated_at")
