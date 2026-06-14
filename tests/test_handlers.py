import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import bot.handlers as handlers


def _reset_state() -> None:
    handlers._last_digest_at = None
    handlers._digest_running = False


def test_try_start_digest_blocks_when_running():
    _reset_state()
    handlers._digest_running = True

    err = asyncio.run(handlers._try_start_digest())

    assert err == "⏳ Digest is already running. Please wait."


def test_try_start_digest_blocks_during_cooldown():
    _reset_state()
    handlers._last_digest_at = datetime.now()

    err = asyncio.run(handlers._try_start_digest())

    assert err is not None
    assert "Next digest available" in err


def test_try_start_digest_allows_when_idle():
    _reset_state()

    err = asyncio.run(handlers._try_start_digest())

    assert err is None
    assert handlers._digest_running is True


def test_run_digest_job_sets_cooldown_only_on_success(monkeypatch):
    _reset_state()
    handlers._digest_running = True

    async def fail_deliver(bot, chat_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(handlers, "deliver_digest", fail_deliver)

    application = MagicMock()
    application.bot = AsyncMock()

    asyncio.run(handlers._run_digest_job(application, 123))

    assert handlers._last_digest_at is None
    assert handlers._digest_running is False
    application.bot.send_message.assert_awaited_once()


def test_run_digest_job_sets_cooldown_after_success(monkeypatch):
    _reset_state()
    handlers._digest_running = True

    async def fake_deliver(bot, chat_id):
        return None

    monkeypatch.setattr(handlers, "deliver_digest", fake_deliver)

    application = MagicMock()
    application.bot = AsyncMock()

    before = datetime.now()
    asyncio.run(handlers._run_digest_job(application, 123))
    after = datetime.now()

    assert handlers._last_digest_at is not None
    assert before <= handlers._last_digest_at <= after
    assert handlers._digest_running is False


def test_double_start_only_one_slot():
    _reset_state()

    async def scenario():
        first = await handlers._try_start_digest()
        second = await handlers._try_start_digest()
        handlers._digest_running = False
        return first, second

    first, second = asyncio.run(scenario())

    assert first is None
    assert second == "⏳ Digest is already running. Please wait."


def test_run_digest_job_reports_delivery_error(monkeypatch):
    _reset_state()
    handlers._digest_running = True

    async def fail_deliver(bot, chat_id):
        raise handlers.TelegramDeliveryError("Message part 2 is too long")

    monkeypatch.setattr(handlers, "deliver_digest", fail_deliver)

    application = MagicMock()
    application.bot = AsyncMock()

    asyncio.run(handlers._run_digest_job(application, 123))

    assert handlers._last_digest_at is None
    application.bot.send_message.assert_awaited_once_with(
        chat_id=123,
        text="❌ Failed to prepare digest: Message part 2 is too long",
    )


def test_run_digest_job_reports_rss_error(monkeypatch):
    _reset_state()
    handlers._digest_running = True

    async def fail_deliver(bot, chat_id):
        raise RuntimeError("No articles fetched from any RSS source")

    monkeypatch.setattr(handlers, "deliver_digest", fail_deliver)

    application = MagicMock()
    application.bot = AsyncMock()

    asyncio.run(handlers._run_digest_job(application, 123))

    application.bot.send_message.assert_awaited_once_with(
        chat_id=123,
        text="❌ No news articles fetched from RSS. Try again later.",
    )


def test_cooldown_allows_retry_after_expiry():
    _reset_state()
    handlers._last_digest_at = datetime.now() - timedelta(hours=handlers.COOLDOWN_HOURS, seconds=1)

    err = asyncio.run(handlers._try_start_digest())

    assert err is None
