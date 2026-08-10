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

# Setup Django before importing any Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.production")
django.setup()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from plane.app.agent.engine import PlaneAgentEngine
from plane.bgtasks.slack_bot.slack_adapter import render_slack_block_kit
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

        # Find the first project in any workspace (auto-detect)
        project = Project.objects.filter(deleted_at__isnull=True).first()

        if not project:
            respond(text="❌ Không tìm thấy project nào trong hệ thống Plane.")
            return

        try:
            # Invoke Decoupled Core Agent Engine
            agent_engine = PlaneAgentEngine(project=project)
            agent_result = agent_engine.process_request(text)

            # Adapt Core Result ➔ Slack Block Kit Card
            payload = render_slack_block_kit(agent_result, user_name=user_name)

            respond(**payload)
        except Exception as e:
            logger.exception(f"Agent error processing request: {text}")
            respond(text=f"❌ Lỗi xử lý: {str(e)}")

    return bolt_app


def main():
    bot_token, app_token = get_tokens()

    if not bot_token:
        print("❌ ERROR: Slack Bot Token chưa được cấu hình.")
        print("   Cách 1: Vào Plane Web UI → Settings → Integrations → Slack → Điền Bot Token")
        print("   Cách 2: Set biến môi trường SLACK_BOT_TOKEN=xoxb-...")
        sys.exit(1)

    if not app_token:
        print("❌ ERROR: Slack App Token chưa được cấu hình.")
        print("   Cách 1: Vào Plane Web UI → Settings → Integrations → Slack → Điền App Token")
        print("   Cách 2: Set biến môi trường SLACK_APP_TOKEN=xapp-...")
        sys.exit(1)

    print("=" * 60)
    print("🤖 Plane Core AI Agent — Slack Socket Mode")
    print("=" * 60)
    print(f"   Bot Token: {bot_token[:15]}...***")
    print(f"   App Token: {app_token[:15]}...***")
    print("   Listening for /agent commands...")
    print("   (Không cần ngrok / domain public)")
    print("=" * 60)

    bolt_app = create_app(bot_token)
    handler = SocketModeHandler(bolt_app, app_token)
    handler.start()


if __name__ == "__main__":
    main()
