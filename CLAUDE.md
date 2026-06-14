# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Dev setup
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Auth (required for Vertex AI + Cloud TTS locally)
gcloud auth application-default login

# Run bot (polling mode, no webhook needed locally)
python -m bot

# Run digest pipeline without Telegram
python -m digest

# Tests
pytest
pytest tests/test_fetcher.py          # single file
pytest tests/test_fetcher.py::test_fn # single test
```

## Architecture

Two independent packages: `digest/` does all data work and returns a typed `Digest`; `bot/` wraps it in a Telegram bot.

### Data flow

```
RSS feeds (18 sources, parallel fetch)
  → fetch_news()          digest/fetcher.py   — feedparser, keyword filter, dedup
  → generate_digest()     digest/generator.py — Vertex AI Gemini 2.5 Flash, JSON schema
  → validate_raw_digest() digest/validator.py — structural checks, retry up to 2x
  → enrich_digest()       digest/enricher.py  — maps raw dict → typed Digest dataclass
  → Digest                digest/models.py    — Article, TopStory, Category, Question
```

### Bot flow

`bot/handlers.py:deliver_digest()` orchestrates the Telegram send sequence:
1. `run_digest()` in a thread (blocks ~2-5 min)
2. `synthesize_speech()` via `tts.py` — Cloud TTS, splits >4800 byte chunks, merges with ffmpeg
3. Sends: header message → audio file → HTML messages (chunked ≤4096 chars) → markdown file

Cooldown and in-flight deduplication are in-memory (`_digest_lock`, `_last_digest_at`, `_digest_running`). These reset on process restart.

### Bot startup (`bot/__main__.py`)

- `WEBHOOK_URL` set → webhook mode (production, Cloud Run)
- `K_SERVICE` set but no `WEBHOOK_URL` → health-only server (Cloud Run without webhook)
- Neither → polling mode (local dev)

### Key config

| Var | Default | Notes |
|-----|---------|-------|
| `TELEGRAM_BOT_TOKEN` | — | required |
| `TELEGRAM_CHAT_ID` | — | required; only chat allowed to trigger |
| `WEBHOOK_URL` | — | enables webhook mode |
| `WEBHOOK_SECRET` | — | required if `WEBHOOK_URL` set |
| `DIGEST_COOLDOWN_HOURS` | `4` | rate limit between runs |
| `GCP_PROJECT_ID` | — | Vertex AI project |
| `GCP_LOCATION` | `us-central1` | Vertex AI region |
| `TTS_VOICE` | `en-US-Neural2-J` | override Cloud TTS voice |
| `SAVE_DIGEST_FILE` | `false` | persist digest to `digests/` |

RSS sources and interest-keyword filter live in `digest/config.py`. Gemini prompt and JSON response schema are in `digest/prompts.py`.

## GCP deploy

```bash
./scripts/setup-cloudrun-sa.sh   # create service account (one time)
./scripts/create-secrets.sh      # store secrets in Secret Manager (one time)
./scripts/deploy-cloudrun.sh     # build, push, deploy Cloud Run + set webhook
```

Secrets injected at runtime from Secret Manager (not baked into image):
- `digest-telegram-bot-token` → `TELEGRAM_BOT_TOKEN`
- `digest-telegram-chat-id` → `TELEGRAM_CHAT_ID`
- `digest-webhook-secret` → `WEBHOOK_SECRET`
