import os
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

from plane.app.views.base import BaseAPIView
from plane.authentication.session import BaseSessionAuthentication
from plane.api.middleware.api_authentication import APIKeyAuthentication
from plane.app.permissions import ROLE, allow_permission
from plane.db.models import Project, SlackAutomation
from plane.api.serializers import SlackAutomationSerializer
from plane.bgtasks.slack_publisher import send_slack_webhook


class SlackAutomationEndpoint(BaseAPIView):
    """
    API View for managing Slack Webhook Notification configurations per Project or Workspace.
    """

    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER])
    def get(self, request, slug, project_id):
        if str(project_id).lower() == "global":
            automations = SlackAutomation.objects.filter(project__workspace__slug=slug)
        else:
            automations = SlackAutomation.objects.filter(project_id=project_id)
        serializer = SlackAutomationSerializer(automations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN])
    def post(self, request, slug, project_id):
        webhook_url = request.data.get("webhook_url")
        channel_name = request.data.get("channel_name", "")
        events = request.data.get("events", {"issue_created": True, "issue_updated": True, "comment_created": True})
        is_active = request.data.get("is_active", True)

        if not webhook_url:
            return Response(
                {"error": "webhook_url is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(project_id).lower() == "global":
            projects = Project.objects.filter(workspace__slug=slug)
            created_list = []
            for proj in projects:
                automation, _ = SlackAutomation.objects.update_or_create(
                    project=proj,
                    defaults={
                        "webhook_url": webhook_url,
                        "channel_name": channel_name,
                        "events": events,
                        "is_active": is_active,
                    },
                )
                created_list.append(automation)
            serializer = SlackAutomationSerializer(created_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        project = Project.objects.filter(pk=project_id, workspace__slug=slug).first()
        if not project:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        automation, _ = SlackAutomation.objects.update_or_create(
            project=project,
            defaults={
                "webhook_url": webhook_url,
                "channel_name": channel_name,
                "events": events,
                "is_active": is_active,
            },
        )

        serializer = SlackAutomationSerializer(automation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN])
    def delete(self, request, slug, project_id):
        automation_id = request.data.get("id")
        if automation_id:
            SlackAutomation.objects.filter(id=automation_id).delete()
        elif str(project_id).lower() == "global":
            SlackAutomation.objects.filter(project__workspace__slug=slug).delete()
        else:
            SlackAutomation.objects.filter(project_id=project_id).delete()
        return Response({"message": "Slack automation configuration deleted."}, status=status.HTTP_204_NO_CONTENT)


class SlackTestWebhookEndpoint(BaseAPIView):
    """
    Endpoint to test sending a sample Block Kit message to a Slack Webhook URL.
    """

    authentication_classes = [BaseSessionAuthentication, APIKeyAuthentication]

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER])
    def post(self, request, slug, project_id):
        webhook_url = request.data.get("webhook_url")
        if not webhook_url:
            env_url = os.getenv("SLACK_WEBHOOK_URL") or getattr(settings, "SLACK_WEBHOOK_URL", "")
            if project_id and str(project_id).lower() != "global":
                auto = SlackAutomation.objects.filter(project_id=project_id, is_active=True).first()
                if auto:
                    webhook_url = auto.webhook_url
            if not webhook_url:
                webhook_url = env_url

        if not webhook_url:
            return Response({"error": "Webhook URL is missing."}, status=status.HTTP_400_BAD_REQUEST)

        test_payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎉 Slack Integration Successfully Connected!",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Hello from *Plane-Civix*! Your Slack Webhook notification service is working perfectly.",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "Plane-Civix Notifications Bot"},
                    ],
                },
            ]
        }

        success, message = send_slack_webhook(webhook_url, test_payload)
        if success:
            return Response({"success": True, "message": "Test Slack message sent successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": f"Failed to send Slack message: {message}"}, status=status.HTTP_400_BAD_REQUEST)


class SlackCommandsEndpoint(BaseAPIView):
    """
    Single Entrypoint Endpoint for handling Slack AI Agent Command (/agent).
    Supports Slash Command /agent <natural language request> from Slack Platform.
    """

    permission_classes = [AllowAny]

    def post(self, request, slug, project_id):
        # Read parameters from form-data or JSON
        command = request.data.get("command", "") or request.POST.get("command", "")
        text = (request.data.get("text", "") or request.POST.get("text", "")).strip()
        user_name = request.data.get("user_name", "") or request.POST.get("user_name", "")

        # Clean command string (e.g. /agent -> agent)
        command_name = command.lstrip("/").strip().lower()

        if str(project_id).lower() == "global":
            project = Project.objects.filter(workspace__slug=slug).first()
        else:
            project = Project.objects.filter(pk=project_id, workspace__slug=slug).first()

        if not project:
            return Response(
                {"text": "❌ Error: Project not found or workspace invalid."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from plane.app.agent.engine import PlaneAgentEngine
        from plane.bgtasks.slack_bot.slack_adapter import render_slack_block_kit

        # Single /agent entrypoint routing logic
        if command_name in ["agent", "plane", "bot"]:
            if not text:
                return Response(
                    {
                        "response_type": "ephemeral",
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": (
                                        "🤖 *Plane Core AI Agent*\n"
                                        "Hãy nhập câu lệnh tự nhiên bằng Tiếng Việt hoặc Tiếng Anh sau lệnh `/agent`:\n\n"
                                        "• `/agent Báo cáo tiến độ Civix` ➔ Xem % tiến độ & thanh progress bar\n"
                                        "• `/agent Danh sách task của tôi` ➔ Xem các công việc đang được gán\n"
                                        "• `/agent Thành viên dự án` ➔ Xem danh sách member & khối lượng công việc\n"
                                        "• `/agent Có công việc nào quá hạn không?` ➔ Lọc các task trễ hạn\n"
                                        "• `/agent Tạo task fix bug API gán cho @Nam hạn thứ 6` ➔ AI tự phân tích & tạo task"
                                    ),
                                },
                            }
                        ],
                    },
                    status=status.HTTP_200_OK,
                )

            # Invoke Decoupled Core Agent Engine
            user_obj = request.user if request.user and request.user.is_authenticated else None
            agent_engine = PlaneAgentEngine(project=project, user=user_obj)
            agent_result = agent_engine.process_request(text)

            # Adapt Core Result ➔ Slack Block Kit Card
            payload = render_slack_block_kit(agent_result, user_name=user_name)
        # Backward compatibility for direct commands
        elif command_name == "progress":
            from plane.bgtasks.slack_bot.fast_commands import handle_slack_progress_command
            payload = handle_slack_progress_command(project, slug)
        elif command_name == "tasks":
            from plane.bgtasks.slack_bot.fast_commands import handle_slack_tasks_command
            payload = handle_slack_tasks_command(project)
        elif command_name == "members":
            from plane.bgtasks.slack_bot.fast_commands import handle_slack_members_command
            payload = handle_slack_members_command(project)
        else:
            payload = {
                "response_type": "ephemeral",
                "text": f"❓ Unknown command `/{command_name}`. Please use `/agent <yêu cầu>`.",
            }

        return Response(payload, status=status.HTTP_200_OK)



