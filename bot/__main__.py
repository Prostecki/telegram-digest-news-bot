import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import BotCommand
from telegram.ext import Application, CommandHandler

from bot.config import (
    ALLOWED_CHAT_ID,
    IS_CLOUD_RUN,
    PORT,
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_SECRET,
    WEBHOOK_URL,
)
from bot.handlers import getnews_command, start_command

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def run_health_server(port: int) -> None:
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/health"):
                body = b"ok"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, *args):
            return

    logger.info("Health server on port %s (waiting for WEBHOOK_URL)", port)
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


async def setup_bot_commands(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("getnews", "Сгенерировать дайджест новостей"),
        BotCommand("start", "Информация о боте"),
    ])


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN must be set")
    if not ALLOWED_CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID must be set")
    if WEBHOOK_URL and not WEBHOOK_SECRET:
        raise ValueError("WEBHOOK_SECRET must be set when WEBHOOK_URL is configured")

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(setup_bot_commands)
        .build()
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("getnews", getnews_command))

    if WEBHOOK_URL:
        logger.info("Starting webhook mode on port %s", PORT)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook",
            secret_token=WEBHOOK_SECRET,
        )
        return

    if IS_CLOUD_RUN:
        run_health_server(PORT)
        return

    logger.info("WEBHOOK_URL not set — starting polling mode (local dev)")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
