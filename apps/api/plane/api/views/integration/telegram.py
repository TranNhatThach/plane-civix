import os
import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

from plane.app.views.base import BaseAPIView
from plane.authentication.session import BaseSessionAuthentication
from plane.api.middleware.api_authentication import APIKeyAuthentication
from plane.app.permissions import ROLE, allow_permission
from plane.db.models import Project, TelegramAutomation
from plane.api.serializers import TelegramAutomationSerializer
from plane.bgtasks.telegram_publisher import send_telegram_message
from plane.bgtasks.telegram_bot_service import process_telegram_update


def setup_telegram_webhook(bot_token: str, request=None):
    """Ensures Webhook is cleared so the dedicated Telegram Bot Polling service handles updates exclusively."""
    if not bot_token:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
            timeout=5,
        )
    except Exception:
        pass


class TelegramAutomationEndpoint(BaseAPIView):
    """
    API View for managing Telegram Bot Notification configurations per Project or Workspace.
    """

    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER])
    def get(self, request, slug, project_id):
        if str(project_id).lower() == "global":
            automations = TelegramAutomation.objects.filter(project__workspace__slug=slug)
        else:
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

        setup_telegram_webhook(bot_token, request)

        if str(project_id).lower() == "global":
            projects = Project.objects.filter(workspace__slug=slug)
            if not projects.exists():
                return Response(
                    {"error": "No projects found in this workspace. Please create a project first before configuring Telegram automation."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            last_automation = None
            for proj in projects:
                auto, _ = TelegramAutomation.objects.update_or_create(
                    project=proj,
                    defaults={
                        "workspace": proj.workspace,
                        "bot_token": bot_token,
                        "chat_id": chat_id,
                        "is_active": request.data.get("is_active", True),
                        "events": request.data.get("events", {"issue_created": True, "issue_updated": True, "comment_added": True}),
                    },
                )
                last_automation = auto
            serializer = TelegramAutomationSerializer(last_automation)
            return Response(serializer.data, status=status.HTTP_200_OK)

        try:
            project = Project.objects.get(pk=project_id, workspace__slug=slug)
        except (Project.DoesNotExist, ValueError):
            project = Project.objects.filter(workspace__slug=slug).first()
            if not project:
                return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

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
            automation = TelegramAutomation.objects.get(pk=pk)
            automation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TelegramAutomation.DoesNotExist:
            return Response({"error": "Telegram automation config not found."}, status=status.HTTP_404_NOT_FOUND)


class TelegramTestMessageEndpoint(BaseAPIView):
    """
    Endpoint for testing Telegram Bot Token and Chat ID connection.
    """

    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER])
    def post(self, request, slug, project_id):
        bot_token = request.data.get("bot_token")
        chat_id = request.data.get("chat_id")

        if not bot_token or not chat_id:
            return Response(
                {"error": "bot_token and chat_id are required for testing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        setup_telegram_webhook(bot_token, request)

        test_message = (
            "🎉 <b>Plane Telegram Bot Test Connection Successful!</b>\n\n"
            "Your Plane workspace is now connected to this Telegram chat. You will receive real-time notifications for issue updates!"
        )

        success, err_msg = send_telegram_message(bot_token, chat_id, test_message)

        if success:
            return Response({"message": "Test notification sent successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": f"Telegram Error: {err_msg}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TelegramWebhookEndpoint(BaseAPIView):
    """
    Public Webhook endpoint - delegates exclusively to Polling container to avoid double processing.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

