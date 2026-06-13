# Telegram Digest Bot

Daily tech digest: RSS → Gemini (Vertex AI) → Telegram (text + audio + markdown file).

Trigger on demand with `/getnews` in Telegram.

## Architecture

```
Telegram /getnews
    ↓
Cloud Run (Docker, webhook + secret token)
    ↓
Secret Manager → digest-telegram-bot-token, digest-telegram-chat-id, digest-webhook-secret
Vertex AI (Gemini) + Cloud TTS
    ↓
Telegram (audio + messages + .md)
```

## Security

- Secrets only in Secret Manager (never in the image)
- Dedicated service account `digest-bot@...` (Vertex AI + Secret Manager read)
- `/getnews` only from `TELEGRAM_CHAT_ID`
- Webhook protected with `WEBHOOK_SECRET`
- Rate limit: 1 digest per `DIGEST_COOLDOWN_HOURS` (default 4h)

## Local development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
gcloud auth application-default login
python -m bot          # polling mode (no WEBHOOK_URL)
```

In Telegram, send `/getnews` to your bot.

Test digest generation without Telegram:

```bash
python -m digest
```

Run tests:

```bash
pytest
```

## GCP setup (one time)

### 1. Service account

```bash
chmod +x scripts/*.sh
./scripts/setup-cloudrun-sa.sh
```

Creates `digest-bot@athlete-ai-platform.iam.gserviceaccount.com` with least-privilege IAM.

### 2. Store secrets in Secret Manager

```bash
./scripts/create-secrets.sh
```

| GCP Secret Manager | Env var |
|---|---|
| `digest-telegram-bot-token` | `TELEGRAM_BOT_TOKEN` |
| `digest-telegram-chat-id` | `TELEGRAM_CHAT_ID` |
| `digest-webhook-secret` | `WEBHOOK_SECRET` (auto-created on deploy) |

### 3. Deploy to Cloud Run

```bash
./scripts/deploy-cloudrun.sh
```

The script builds the image, creates `digest-webhook-secret` if missing, deploys, and sets `WEBHOOK_URL`.

Optional: change cooldown before deploy:

```bash
DIGEST_COOLDOWN_HOURS=6 ./scripts/deploy-cloudrun.sh
```

## Project structure

```
digest/          # RSS fetch, Gemini, enrich, audio — returns typed Digest
  models.py      # Article, TopStory, Category, Question, Digest
bot/             # Telegram bot
  config.py      # env config
  formatters.py  # Telegram + Markdown rendering (pure)
  handlers.py    # /start, /getnews, cooldown, delivery
  __main__.py    # entrypoint (webhook / polling / health)
tts.py           # Google Cloud Text-to-Speech
tests/           # pytest unit tests
Dockerfile       # Cloud Run image (python -m bot)
scripts/         # GCP bootstrap + deploy
```
