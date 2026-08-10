# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import serializers
from plane.db.models import TelegramAutomation, SlackAutomation, Project


class TelegramAutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramAutomation
        fields = [
            "id",
            "project",
            "bot_token",
            "chat_id",
            "is_active",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        return TelegramAutomation.objects.create(**validated_data)


class SlackAutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackAutomation
        fields = [
            "id",
            "project",
            "webhook_url",
            "channel_name",
            "is_active",
            "bot_token",
            "app_token",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        return SlackAutomation.objects.create(**validated_data)

