import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.production")
django.setup()
from plane.db.models.integration.slack import SlackAutomation
records = list(SlackAutomation.objects.values("id", "bot_token", "app_token", "is_active", "webhook_url"))
for r in records:
    bt = r["bot_token"]
    at = r["app_token"]
    print(f"ID: {r['id']}")
    print(f"  bot_token: {bt[:20]}...***" if bt else "  bot_token: EMPTY")
    print(f"  app_token: {at[:20]}...***" if at else "  app_token: EMPTY")
    print(f"  is_active: {r['is_active']}")
    print(f"  webhook_url: {r['webhook_url']}")
if not records:
    print("NO SlackAutomation records found in DB!")
