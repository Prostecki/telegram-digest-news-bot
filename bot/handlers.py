import asyncio
import logging
from datetime import datetime, timedelta
from io import BytesIO

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes

from bot.config import (
    ALLOWED_CHAT_ID,
    COOLDOWN_HOURS,
    DIGESTS_DIR,
    SAVE_DIGEST_FILE,
    TTS_LANGUAGE,
)
from bot.formatters import (
    digest_filename,
    format_digest_markdown,
    format_telegram_messages,
)
from digest import Digest, run_digest
from tts import synthesize_speech

logger = logging.getLogger(__name__)

_digest_lock = asyncio.Lock()
_last_digest_at: datetime | None = None


def _is_allowed_chat(chat_id: int) -> bool:
    if not ALLOWED_CHAT_ID:
        return False
    return str(chat_id) == ALLOWED_CHAT_ID


def _cooldown_remaining() -> timedelta | None:
    if _last_digest_at is None:
        return None
    elapsed = datetime.now() - _last_digest_at
    limit = timedelta(hours=COOLDOWN_HOURS)
    if elapsed >= limit:
        return None
    return limit - elapsed


def _format_cooldown(remaining: timedelta) -> str:
    total_minutes = int(remaining.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _save_digest_file(digest: Digest) -> None:
    if not SAVE_DIGEST_FILE:
        return
    DIGESTS_DIR.mkdir(parents=True, exist_ok=True)
    path = DIGESTS_DIR / digest_filename(digest.date)
    path.write_text(format_digest_markdown(digest), encoding="utf-8")
    logger.info("Saved digest to %s", path)


async def deliver_digest(bot, chat_id: int) -> None:
    logger.info("Generating digest for chat %s", chat_id)
    digest = await asyncio.to_thread(run_digest)
    messages = format_telegram_messages(digest)
    markdown = format_digest_markdown(digest)
    filename = digest_filename(digest.date)
    _save_digest_file(digest)

    logger.info("Synthesizing audio")
    audio_text = digest.audio_script or digest.summary
    audio_bytes = await asyncio.to_thread(synthesize_speech, audio_text, TTS_LANGUAGE)

    await bot.send_message(
        chat_id=chat_id,
        text=(
            f"🗞 <b>Digest ready</b>\n"
            f"📅 {digest.date}\n"
            f"🎧 Top stories podcast + 📖 categorized reading\n"
            f"📎 <code>{filename}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )

    await bot.send_audio(
        chat_id=chat_id,
        audio=BytesIO(audio_bytes),
        filename=f"{digest.date}-top-stories-podcast.mp3",
        title=f"Top Tech News — {digest.date}",
        caption=f"🎧 Top {len(digest.top_stories)} stories (~3-4 min)",
    )

    for message in messages:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
        )

    await bot.send_document(
        chat_id=chat_id,
        document=BytesIO(markdown.encode("utf-8")),
        filename=filename,
        caption=f"📄 {filename}",
    )

    logger.info("Digest sent to chat %s", chat_id)


async def _run_digest_job(application: Application, chat_id: int) -> None:
    global _last_digest_at

    async with _digest_lock:
        _last_digest_at = datetime.now()
        try:
            await deliver_digest(application.bot, chat_id)
        except Exception:
            logger.exception("Digest failed for chat %s", chat_id)
            await application.bot.send_message(
                chat_id=chat_id,
                text="❌ Failed to generate digest. Check Cloud Run logs.",
            )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.message:
        return

    if not _is_allowed_chat(update.effective_chat.id):
        await update.message.reply_text("⛔ This bot is private.")
        return

    await update.message.reply_text(
        "👋 Tech Digest Bot\n\n"
        f"Send /getnews to generate today's digest (2–5 min).\n"
        f"Cooldown: {COOLDOWN_HOURS:g}h between runs."
    )


async def getnews_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.message:
        return

    chat_id = update.effective_chat.id
    if not _is_allowed_chat(chat_id):
        await update.message.reply_text("⛔ This bot is private.")
        return

    if _digest_lock.locked():
        await update.message.reply_text("⏳ Digest is already running. Please wait.")
        return

    remaining = _cooldown_remaining()
    if remaining is not None:
        await update.message.reply_text(
            f"⏳ Next digest available in {_format_cooldown(remaining)}."
        )
        return

    await update.message.reply_text("⏳ Generating digest… This takes 2–5 minutes.")
    context.application.create_task(_run_digest_job(context.application, chat_id))
