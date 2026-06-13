#!/usr/bin/env bash
# Store Telegram credentials in GCP Secret Manager.
# Reads from .env if present, otherwise pass as env vars.
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-athlete-ai-platform}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${TELEGRAM_BOT_TOKEN:?Set TELEGRAM_BOT_TOKEN or add to .env}"
: "${TELEGRAM_CHAT_ID:?Set TELEGRAM_CHAT_ID or add to .env}"

create_or_update() {
  local name="$1"
  local value="$2"
  if gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
    echo -n "$value" | gcloud secrets versions add "$name" --data-file=- --project="$PROJECT_ID"
    echo "Updated secret: $name"
  else
    echo -n "$value" | gcloud secrets create "$name" --data-file=- --project="$PROJECT_ID"
    echo "Created secret: $name"
  fi
}

create_or_update "telegram-bot-token" "$TELEGRAM_BOT_TOKEN"
create_or_update "telegram-chat-id" "$TELEGRAM_CHAT_ID"

echo "Done. Secrets stored in project ${PROJECT_ID}."
