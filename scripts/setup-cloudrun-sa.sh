#!/usr/bin/env bash
# One-time: Cloud Run service account + IAM for digest bot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=naming.sh
source "${SCRIPT_DIR}/naming.sh"

PROJECT_ID="${GCP_PROJECT_ID:-athlete-ai-platform}"
SA_NAME="${CLOUD_RUN_SA_NAME}"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Project: ${PROJECT_ID}"
echo "Service account: ${SA_EMAIL}"

gcloud services enable \
  iam.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  texttospeech.googleapis.com \
  run.googleapis.com \
  --project="${PROJECT_ID}"

if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "Service account already exists"
else
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="Cloud Run — Telegram Digest Bot" \
    --project="${PROJECT_ID}"
  echo "Created service account"
fi

# IAM can lag briefly right after SA creation.
for attempt in 1 2 3 4 5; do
  if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
    break
  fi
  echo "Waiting for service account propagation (${attempt}/5)..."
  sleep 2
done

gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null

bind_role() {
  local role="$1"
  if gcloud projects get-iam-policy "${PROJECT_ID}" \
    --flatten="bindings[].members" \
    --filter="bindings.role:${role} AND bindings.members:serviceAccount:${SA_EMAIL}" \
    --format="value(bindings.role)" 2>/dev/null | grep -q .; then
    echo "Already granted ${role}"
    return 0
  fi

  for attempt in 1 2 3 4 5; do
    if gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="${role}" \
      --condition=None \
      --quiet; then
      echo "Granted ${role}"
      return 0
    fi
    echo "Retrying ${role} (${attempt}/5)..."
    sleep 2
  done
}

bind_role roles/aiplatform.user
bind_role roles/secretmanager.secretAccessor

echo ""
echo "Ready: ${SA_EMAIL}"
echo "Next: ./scripts/create-secrets.sh && ./scripts/deploy-cloudrun.sh"
