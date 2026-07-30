# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import status
from rest_framework.response import Response

from plane.api.views.base import BaseAPIView
from plane.app.permissions import ROLE, allow_permission
from plane.db.models import Project, TelegramAutomation
from plane.api.serializers import TelegramAutomationSerializer
from plane.bgtasks.telegram_publisher import send_telegram_message


class TelegramAutomationEndpoint(BaseAPIView):
    """
    API View for managing Telegram Bot Notification configurations per Project.
    """

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER])
    def get(self, request, slug, project_id):
        automations = TelegramAutomation.objects.filter(project_id=project_id)
        serializer = TelegramAutomationSerializer(automations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN])
    def post(self, request, slug, project_id):
        bot_token = request.data.get("bot_token")
        chat_id = request.data.get("chat_id")

        if not bot_token or not chat_id:
            return Response(
                {"error": "bot_token and chat_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = Project.objects.get(pk=project_id)

        automation, created = TelegramAutomation.objects.update_or_create(
            project=project,
            chat_id=chat_id,
            defaults={
                "bot_token": bot_token,
                "is_active": request.data.get("is_active", True),
                "events": request.data.get("events", {"issue_created": True, "issue_updated": True, "comment_added": True}),
            },
        )

        serializer = TelegramAutomationSerializer(automation)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN])
    def delete(self, request, slug, project_id, pk):
        try:
            automation = TelegramAutomation.objects.get(pk=pk, project_id=project_id)
            automation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TelegramAutomation.DoesNotExist:
            return Response({"error": "Telegram automation config not found."}, status=status.HTTP_404_NOT_FOUND)


class TelegramTestMessageEndpoint(BaseAPIView):
    """
    Endpoint for testing Telegram Bot Token and Chat ID connection.
    """

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER])
    def post(self, request, slug, project_id):
        bot_token = request.data.get("bot_token")
        chat_id = request.data.get("chat_id")

        if not bot_token or not chat_id:
            return Response(
                {"error": "bot_token and chat_id are required for testing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_message = (
            "🎉 <b>Plane Telegram Bot Test Connection Successful!</b>\n\n"
            "Your Plane workspace is now connected to this Telegram chat. You will receive real-time notifications for issue updates!"
        )

        success = send_telegram_message(bot_token, chat_id, test_message)

        if success:
            return Response({"message": "Test notification sent successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to send test message. Please verify your Bot Token and Chat ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
