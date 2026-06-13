# Telegram Digest Bot

Daily tech digest: RSS → Gemini (Vertex AI) → Telegram (text + audio + markdown file).

## Architecture

```
GitHub Actions (cron / manual)
    ↓ WIF (no JSON keys)
GCP Service Account
    ↓
Secret Manager → digest-telegram-bot-token, digest-telegram-chat-id
Vertex AI (Gemini) + Cloud TTS
    ↓
Telegram
```

## Local development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values
python bot.py
```

## GCP setup (one time)

### 1. Enable APIs + WIF

```bash
chmod +x scripts/*.sh
export GCP_PROJECT_ID=athlete-ai-platform
./scripts/setup-wif.sh YOUR_GITHUB_USER telegram-digest-bot
```

### 2. Store secrets in Secret Manager

```bash
./scripts/create-secrets.sh
```

Never commit `.env` — it is gitignored.

Creates secrets with **digest-** prefix (see `scripts/naming.sh`):

| GCP Secret Manager | App env var (injected in CI) |
|---|---|
| `digest-telegram-bot-token` | `TELEGRAM_BOT_TOKEN` |
| `digest-telegram-chat-id` | `TELEGRAM_CHAT_ID` |

### 3. GitHub repository variables

In **Settings → Secrets and variables → Actions → Variables**, add (**DIGEST_** prefix — no clash with other repos/projects):

| Variable | Example |
|---|---|
| `DIGEST_GCP_PROJECT_ID` | `athlete-ai-platform` |
| `DIGEST_GCP_LOCATION` | `us-central1` |
| `DIGEST_GCP_SERVICE_ACCOUNT` | `github-digest-bot@athlete-ai-platform.iam.gserviceaccount.com` |
| `DIGEST_GCP_WIF_PROVIDER` | `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |

Telegram credentials live only in **GCP Secret Manager** (`digest-*`), not in GitHub Secrets.

### 4. Push and run CI

```bash
git push -u origin main
```

- **Scheduled:** daily at 07:00 UTC (edit cron in `.github/workflows/digest.yml`)
- **Manual:** Actions → Daily Digest → Run workflow

## Project structure

```
digest/          # RSS fetch, Gemini, enrich, audio script
bot.py           # Telegram formatting + send
tts.py           # Google Cloud Text-to-Speech
.github/         # GitHub Actions (WIF)
scripts/         # GCP bootstrap
```
