#!/usr/bin/env bash
# Store digest-bot credentials in GCP Secret Manager (digest-* names).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=naming.sh
source "${SCRIPT_DIR}/naming.sh"

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

echo "Project: ${PROJECT_ID}"
echo "Secret names: ${SM_TELEGRAM_BOT_TOKEN}, ${SM_TELEGRAM_CHAT_ID}"
echo ""

create_or_update "$SM_TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN"
create_or_update "$SM_TELEGRAM_CHAT_ID" "$TELEGRAM_CHAT_ID"

echo ""
echo "Done. GitHub Actions reads these via workflow digest.yml."
