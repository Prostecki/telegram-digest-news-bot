import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip().rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip() or None
COOLDOWN_HOURS = float(os.getenv("DIGEST_COOLDOWN_HOURS", "4"))
TTS_LANGUAGE = "en-US"

PORT = int(os.getenv("PORT", "8080"))
IS_CLOUD_RUN = bool(os.getenv("K_SERVICE"))

SAVE_DIGEST_FILE = _flag("SAVE_DIGEST_FILE")
DIGESTS_DIR = Path(os.getenv("DIGESTS_DIR", "digests"))

MAX_MESSAGE_LENGTH = 4096
OPTION_LABELS = "ABCD"

CATEGORY_EMOJI = {
    "AI & Agents": "🤖",
    "Fullstack": "⚛️",
    "Backend & APIs": "🐍",
    "GCP & DevOps": "☁️",
    "Databases": "🗄️",
    "Worth Reading": "📚",
}
