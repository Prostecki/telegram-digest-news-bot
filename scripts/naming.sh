# Naming for telegram-digest-bot — avoids clashes with other project secrets.
# Sourced by scripts/*.sh

SECRET_PREFIX="digest"

SM_TELEGRAM_BOT_TOKEN="${SECRET_PREFIX}-telegram-bot-token"
SM_TELEGRAM_CHAT_ID="${SECRET_PREFIX}-telegram-chat-id"

# GitHub Actions repository variables (Settings → Variables)
GH_VAR_PROJECT_ID="DIGEST_GCP_PROJECT_ID"
GH_VAR_LOCATION="DIGEST_GCP_LOCATION"
GH_VAR_SERVICE_ACCOUNT="DIGEST_GCP_SERVICE_ACCOUNT"
GH_VAR_WIF_PROVIDER="DIGEST_GCP_WIF_PROVIDER"
