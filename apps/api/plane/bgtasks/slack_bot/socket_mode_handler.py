"""
Slack Socket Mode Handler for Plane Core AI Agent.
Reads Bot Token & App Token from the SlackAutomation DB model
(configured via Plane Web UI Settings).

Run as a standalone process alongside the Django API server:
    python plane/bgtasks/slack_bot/socket_mode_handler.py

Or via Docker service (recommended for production).
"""

import os
import sys
import logging
import django

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure project root directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.production")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "postgresql://plane:plane@localhost:5432/plane")
os.environ.setdefault("SECRET_KEY", "django-insecure-plane-agent-dev-key")

django.setup()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from plane.app.agent.engine import PlaneAgentEngine
from plane.bgtasks.slack_bot.slack_adapter import render_slack_block_kit
from plane.bgtasks.slack_bot.permissions import check_slack_command_permission
from plane.db.models import Project
from plane.db.models.integration.slack import SlackAutomation

logger = logging.getLogger(__name__)


def get_tokens():
    """
    Read Bot Token & App Token from the first active SlackAutomation record in DB.
    These are configured by the user from the Plane Web UI Settings page.
    Falls back to environment variables if DB tokens are empty.
    """
    try:
        automation = SlackAutomation.objects.filter(
            is_active=True,
            bot_token__isnull=False,
            app_token__isnull=False,
        ).exclude(bot_token="").exclude(app_token="").first()

        if automation:
            return automation.bot_token, automation.app_token
    except Exception as e:
        logger.warning(f"Could not read tokens from DB: {e}")

    # Fallback to environment variables
    return (
        os.environ.get("SLACK_BOT_TOKEN", ""),
        os.environ.get("SLACK_APP_TOKEN", ""),
    )


def create_app(bot_token):
    """Create and configure the Slack Bolt App."""
    bolt_app = App(token=bot_token)

    @bolt_app.command("/agent")
    def handle_agent_command(ack, respond, command):
        """
        Handle /agent <natural language request> slash command via Socket Mode.
        """
        # Must acknowledge within 3 seconds
        ack()

        text = (command.get("text", "") or "").strip()
        user_name = command.get("user_name", "user")
        user_id = command.get("user_id", "")
        channel_id = command.get("channel_id", "")
        team_id = command.get("team_id", "")

        # Fast Command: Check My ID (/agent myid or /agent id)
        if text.lower() in ["myid", "id", "whoami", "/myid", "/id"]:
            respond(
                response_type="ephemeral",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"🆔 *Thông tin tài khoản Slack của bạn:*\n\n"
                                f"• *Slack User ID:* `{user_id}`\n"
                                f"• *Username:* `@{user_name}`\n\n"
                                f"💡 _Hãy gửi mã User ID này cho Quản trị viên để được thêm vào danh sách phân quyền trên Plane Web (Settings → Integrations → Slack)._"
                            ),
                        },
                    }
                ],
            )
            return

        if not text:
            respond(
                response_type="ephemeral",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                "🤖 *Plane Core AI Agent*\n"
                                "Hãy nhập câu lệnh tự nhiên bằng Tiếng Việt hoặc Tiếng Anh sau lệnh `/agent`:\n\n"
                                "• `/agent myid` ➔ Xem Slack User ID của bạn để cấu hình phân quyền\n"
                                "• `/agent Báo cáo tiến độ Civix` ➔ Xem % tiến độ & thanh progress bar\n"
                                "• `/agent Danh sách task của tôi` ➔ Xem các công việc đang được gán\n"
                                "• `/agent Thành viên dự án` ➔ Xem danh sách member & khối lượng công việc\n"
                                "• `/agent Có công việc nào quá hạn không?` ➔ Lọc các task trễ hạn\n"
                                "• `/agent Tạo task fix bug API gán cho @Nam hạn thứ 6` ➔ AI tự phân tích & tạo task"
                            ),
                        },
                    }
                ],
            )
            return

        # Check Permission Configured on Plane Web
        # Find active automation that owns the bot tokens or active project integration
        automation = (
            SlackAutomation.objects.filter(
                is_active=True,
                bot_token__isnull=False,
                app_token__isnull=False,
            ).exclude(bot_token="").exclude(app_token="").select_related("project__workspace").first()
            or SlackAutomation.objects.filter(is_active=True).select_related("project__workspace").first()
        )
        is_allowed, deny_message = check_slack_command_permission(
            automation=automation,
            user_id=user_id,
            user_name=user_name,
            command_text=text,
        )
        if not is_allowed:
            respond(
                response_type="ephemeral",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": deny_message,
                        },
                    }
                ],
            )
            return

        # Resolve Slack User Email & Workspace context
        slack_email = ""
        try:
            user_info = bolt_app.client.users_info(user=user_id)
            if user_info and user_info.get("user"):
                slack_email = user_info["user"].get("profile", {}).get("email", "")
        except Exception as e:
            logger.warning(f"Could not retrieve Slack email for {user_id}: {e}")

        from plane.app.agent.core.context_resolver import ContextResolver

        fb_workspace_id = None
        fb_project_id = None
        if automation and automation.project:
            fb_workspace_id = str(automation.project.workspace_id)
            fb_project_id = str(automation.project.id)

        try:
            context = ContextResolver.resolve_context(
                slack_user_id=user_id,
                channel_id=channel_id,
                user_text=text,
                slack_team_id=team_id,
                slack_email=slack_email,
                fallback_workspace_id=fb_workspace_id,
                fallback_project_id=fb_project_id,
            )
            user = ContextResolver.resolve_identity(user_id, team_id, slack_email)
        except ValueError as val_err:
            respond(
                response_type="ephemeral",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"⚠️ *Không thể truy cập hệ thống Plane:*\n\n"
                                f"{str(val_err)}\n\n"
                                f"• *Slack User ID:* `{user_id}`\n"
                                f"• *Email phát hiện từ Slack:* `{slack_email or 'Không lấy được email (vui lòng cấp quyền users:read.email)'}`\n\n"
                                f"💡 _Hãy đảm bảo tài khoản Plane của bạn có cùng email với Slack hoặc liên hệ Quản trị viên để được thêm vào Workspace công ty._"
                            ),
                        },
                    }
                ],
            )
            return

        project = None
        if context and context.project_id:
            project = Project.objects.filter(id=context.project_id, deleted_at__isnull=True).first()

        try:
            # Invoke Decoupled Core Agent Engine with Authoritative Context
            agent_engine = PlaneAgentEngine(project=project, user=user, context=context)
            agent_result = agent_engine.process_request(text)

            # Adapt Core Result ➔ Slack Block Kit Card
            ws_slug = context.workspace_slug if context else (project.workspace.slug if project and project.workspace else "")
            proj_id = context.project_id if context else (str(project.id) if project else "")

            payload = render_slack_block_kit(
                agent_result,
                user_name=user_name,
                workspace_slug=ws_slug,
                project_id=proj_id,
            )

            respond(**payload)
        except Exception as e:
            logger.exception(f"Agent error processing request: {text}")
            respond(text=f"❌ Lỗi xử lý: {str(e)}")


    @bolt_app.action("agent_confirm_action")
    def handle_confirm_action(ack, respond, body):
        """
        Handle HITL [Approve] button click from Slack Block Kit Card.
        """
        ack()
        user_info = body.get("user", {})
        slack_username = user_info.get("username", "user")
        action = body.get("actions", [{}])[0]
        value = action.get("value", "")

        parts = value.split(":", 1)
        action_type = parts[0]
        project_id = parts[1] if len(parts) > 1 else ""

        from plane.app.agent.tools import tool_rebalance_workload

        if action_type == "rebalance_workload":
            res = tool_rebalance_workload(project_id=project_id, dry_run=False)
            if res.get("success"):
                respond(
                    text=(
                        f"✅ *ĐÃ THỰC THI THÀNH CÔNG bởi @{slack_username}!*\n\n"
                        f"Đã tái phân bổ *{res.get('reassigned_count')} task* từ *{res.get('most_busy')}* "
                        f"sang cho *{res.get('least_busy')}*."
                    )
                )
            else:
                respond(text=f"❌ Không thể phân bổ lại: {res.get('error', 'Lỗi không xác định')}")
        else:
            respond(text=f"✅ *Đã xác nhận thao tác bởi @{slack_username}!*")

    @bolt_app.action("agent_cancel_action")
    def handle_cancel_action(ack, respond, body):
        """
        Handle HITL [Cancel] button click from Slack Block Kit Card.
        """
        ack()
        user_info = body.get("user", {})
        slack_username = user_info.get("username", "user")
        respond(text=f"❌ *Đã hủy thao tác* theo yêu cầu của @{slack_username}.")

    @bolt_app.action("agent_view_tasks_action")
    def handle_view_tasks_action(ack, respond, body):
        """
        Handle [📋 Xem danh sách Task] button click from Slack Block Kit Card.
        """
        ack()
        user_info = body.get("user", {})
        slack_username = user_info.get("username", "user")

        automation = (
            SlackAutomation.objects.filter(
                is_active=True,
                bot_token__isnull=False,
            ).exclude(bot_token="").select_related("project__workspace").first()
            or SlackAutomation.objects.filter(is_active=True).select_related("project__workspace").first()
        )
        project = automation.project if (automation and automation.project) else None

        if project:
            agent_engine = PlaneAgentEngine(project=project)
            agent_result = agent_engine.process_request("Xem danh sách công việc")
            ws_slug = project.workspace.slug if project.workspace else ""
            payload = render_slack_block_kit(
                agent_result,
                user_name=slack_username,
                workspace_slug=ws_slug,
                project_id=str(project.id),
            )
            respond(**payload)
        else:
            respond(text="❌ Không tìm thấy dự án đã kết nối Slack trong hệ thống Plane.")

    @bolt_app.action("agent_view_progress_action")
    def handle_view_progress_action(ack, respond, body):
        """
        Handle [📊 Xem Báo Cáo Tiến Độ] button click from Slack Block Kit Card.
        """
        ack()
        user_info = body.get("user", {})
        slack_username = user_info.get("username", "user")

        automation = (
            SlackAutomation.objects.filter(
                is_active=True,
                bot_token__isnull=False,
            ).exclude(bot_token="").select_related("project__workspace").first()
            or SlackAutomation.objects.filter(is_active=True).select_related("project__workspace").first()
        )
        project = automation.project if (automation and automation.project) else None

        if project:
            agent_engine = PlaneAgentEngine(project=project)
            agent_result = agent_engine.process_request("Báo cáo tiến độ dự án")
            ws_slug = project.workspace.slug if project.workspace else ""
            payload = render_slack_block_kit(
                agent_result,
                user_name=slack_username,
                workspace_slug=ws_slug,
                project_id=str(project.id),
            )
            respond(**payload)
        else:
            respond(text="❌ Không tìm thấy dự án đã kết nối Slack trong hệ thống Plane.")

    return bolt_app


def main():
    import time
    
    print("=" * 60)
    print("🤖 Plane Core AI Agent — Slack Socket Mode Service")
    print("=" * 60)

    while True:
        bot_token, app_token = get_tokens()

        if not bot_token or not app_token:
            logger.info("Slack Bot Token / App Token chưa được cấu hình. Đang đợi cấu hình từ Plane Web Settings...")
            time.sleep(15)
            continue

        print(f"   Bot Token: {bot_token[:15]}...***")
        print(f"   App Token: {app_token[:15]}...***")
        print("   Listening for /agent commands...")
        print("   (Không cần ngrok / domain public)")
        print("=" * 60)

        try:
            bolt_app = create_app(bot_token)
            handler = SocketModeHandler(bolt_app, app_token)
            handler.start()
        except Exception as e:
            logger.error(f"Lỗi khi chạy Slack SocketModeHandler: {e}. Thử kết nối lại sau 15s...")
            time.sleep(15)


if __name__ == "__main__":
    main()
