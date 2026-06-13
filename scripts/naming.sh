# Naming for telegram-digest-bot — avoids clashes with other project secrets.
# Sourced by scripts/*.sh

SECRET_PREFIX="digest"

SM_TELEGRAM_BOT_TOKEN="${SECRET_PREFIX}-telegram-bot-token"
SM_TELEGRAM_CHAT_ID="${SECRET_PREFIX}-telegram-chat-id"
SM_WEBHOOK_SECRET="${SECRET_PREFIX}-webhook-secret"

CLOUD_RUN_SA_NAME="digest-bot"
