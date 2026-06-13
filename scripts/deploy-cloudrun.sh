#!/usr/bin/env bash
# Build and deploy digest bot to Cloud Run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=naming.sh
source "${SCRIPT_DIR}/naming.sh"

PROJECT_ID="${GCP_PROJECT_ID:-athlete-ai-platform}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_SERVICE:-digest-bot}"
SA_EMAIL="${CLOUD_RUN_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REPO="${ARTIFACT_REPO:-digest-bot}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/app:latest"
COOLDOWN_HOURS="${DIGEST_COOLDOWN_HOURS:-4}"

echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"
echo "Service: ${SERVICE}"
echo "Image:   ${IMAGE}"

"${SCRIPT_DIR}/setup-cloudrun-sa.sh"

gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --project="${PROJECT_ID}"

# Telegram webhook secret: A-Za-z0-9_- only, no trailing newline.
WEBHOOK_TOKEN="$(openssl rand -hex 32)"
if gcloud secrets describe "${SM_WEBHOOK_SECRET}" --project="${PROJECT_ID}" &>/dev/null; then
  printf '%s' "${WEBHOOK_TOKEN}" | gcloud secrets versions add "${SM_WEBHOOK_SECRET}" \
    --data-file=- \
    --project="${PROJECT_ID}"
  echo "Updated secret: ${SM_WEBHOOK_SECRET}"
else
  printf '%s' "${WEBHOOK_TOKEN}" | gcloud secrets create "${SM_WEBHOOK_SECRET}" \
    --data-file=- \
    --project="${PROJECT_ID}"
  echo "Created secret: ${SM_WEBHOOK_SECRET}"
fi

gcloud artifacts repositories create "${REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --project="${PROJECT_ID}" 2>/dev/null || true

gcloud builds submit "$(dirname "${SCRIPT_DIR}")" \
  --tag "${IMAGE}" \
  --project="${PROJECT_ID}"

SECRETS="TELEGRAM_BOT_TOKEN=${SM_TELEGRAM_BOT_TOKEN}:latest"
SECRETS+=",TELEGRAM_CHAT_ID=${SM_TELEGRAM_CHAT_ID}:latest"
SECRETS+=",WEBHOOK_SECRET=${SM_WEBHOOK_SECRET}:latest"

DEPLOY_ARGS=(
  --image "${IMAGE}"
  --project "${PROJECT_ID}"
  --region "${REGION}"
  --service-account "${SA_EMAIL}"
  --set-secrets="${SECRETS}"
  --allow-unauthenticated
  --no-cpu-throttling
  --timeout=900
  --memory=1Gi
  --min-instances=0
  --max-instances=1
  --port=8080
)

deploy_service() {
  local env_vars="$1"
  gcloud run deploy "${SERVICE}" \
    "${DEPLOY_ARGS[@]}" \
    --set-env-vars="${env_vars}"
}

BASE_ENV="GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},DIGEST_COOLDOWN_HOURS=${COOLDOWN_HOURS}"
SERVICE_URL="$(gcloud run services describe "${SERVICE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --format='value(status.url)' 2>/dev/null || true)"

if [[ -n "${SERVICE_URL}" ]]; then
  echo "Using service URL: ${SERVICE_URL}"
  deploy_service "${BASE_ENV},WEBHOOK_URL=${SERVICE_URL}"
else
  echo "First deploy: starting health server, then enabling webhook"
  deploy_service "${BASE_ENV}"
  SERVICE_URL="$(gcloud run services describe "${SERVICE}" \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --format='value(status.url)')"
  deploy_service "${BASE_ENV},WEBHOOK_URL=${SERVICE_URL}"
fi

echo ""
echo "Deployed: ${SERVICE_URL}"
echo "Telegram webhook: ${SERVICE_URL}/webhook"
echo "Cooldown: ${COOLDOWN_HOURS}h between /getnews runs"
echo "Send /getnews in your allowed chat to generate a digest."
