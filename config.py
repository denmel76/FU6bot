import os

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://example.com")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
