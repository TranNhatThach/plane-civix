# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import time
import logging
import requests
from django.core.management.base import BaseCommand
from plane.db.models import TelegramAutomation
from plane.bgtasks.telegram_bot_service import process_telegram_update

logger = logging.getLogger("plane.telegram")

class Command(BaseCommand):
    help = "Runs Telegram Bot polling loop for interactive 2-way AI and task queries."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🤖 Starting Telegram Bot Polling Service..."))

        last_offsets = {}

        while True:
            try:
                automations = TelegramAutomation.objects.filter(is_active=True).values("bot_token").distinct()
                tokens = [a["bot_token"] for a in automations if a["bot_token"]]

                if not tokens:
                    time.sleep(5)
                    continue

                for bot_token in tokens:
                    offset = last_offsets.get(bot_token, 0)
                    try:
                        resp = requests.get(
                            f"https://api.telegram.org/bot{bot_token}/getUpdates",
                            params={"offset": offset, "timeout": 5},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("ok"):
                                for update in data.get("result", []):
                                    update_id = update["update_id"]
                                    last_offsets[bot_token] = update_id + 1
                                    self.stdout.write(f"📩 Processing update {update_id}...")
                                    try:
                                        process_telegram_update(update)
                                    except Exception as exc:
                                        self.stdout.write(self.style.ERROR(f"Error processing update: {exc}"))
                        elif resp.status_code == 409:
                            # Conflict: Webhook is set, delete webhook first
                            requests.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"Telegram polling error for token {bot_token[:10]}: {e}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Polling loop error: {e}"))
                time.sleep(3)

            time.sleep(1)
