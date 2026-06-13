#!/usr/bin/env bash
# One-time GCP setup: WIF for GitHub Actions + service account IAM.
# Usage: ./scripts/setup-wif.sh <GITHUB_ORG_OR_USER> <REPO_NAME>
set -euo pipefail

GITHUB_REPO_OWNER="${1:?GitHub org or user, e.g. marktaratynov}"
GITHUB_REPO_NAME="${2:?Repo name, e.g. telegram-digest-bot}"
PROJECT_ID="${GCP_PROJECT_ID:-athlete-ai-platform}"
POOL_ID="${WIF_POOL_ID:-github-pool}"
PROVIDER_ID="${WIF_PROVIDER_ID:-github-provider}"
SA_NAME="${GITHUB_ACTIONS_SA:-github-digest-bot}"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

echo "Project: $PROJECT_ID ($PROJECT_NUMBER)"
echo "GitHub repo: $GITHUB_REPO_OWNER/$GITHUB_REPO_NAME"
echo "Service account: $SA_EMAIL"

gcloud services enable \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  texttospeech.googleapis.com \
  --project="$PROJECT_ID"

# Service account for GitHub Actions
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="GitHub Actions — Telegram Digest Bot" \
  --project="$PROJECT_ID" 2>/dev/null || true

for ROLE in \
  roles/aiplatform.user \
  roles/cloudtexttospeech.user \
  roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --condition=None \
    --quiet
done

# Workload Identity Pool
gcloud iam workload-identity-pools create "$POOL_ID" \
  --project="$PROJECT_ID" \
  --location=global \
  --display-name="GitHub Actions Pool" 2>/dev/null || true

gcloud iam workload-identity-pools describe "$POOL_ID" \
  --project="$PROJECT_ID" \
  --location=global \
  --format="value(name)"

# OIDC provider for GitHub
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location=global \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository_owner == '${GITHUB_REPO_OWNER}'" \
  --issuer-uri="https://token.actions.githubusercontent.com" 2>/dev/null || true

# Allow this repo to impersonate the SA
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}"

WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"

echo ""
echo "=== Add these GitHub repository VARIABLES (Settings → Secrets and variables → Actions → Variables) ==="
echo "GCP_PROJECT_ID=${PROJECT_ID}"
echo "GCP_LOCATION=us-central1"
echo "GCP_SERVICE_ACCOUNT=${SA_EMAIL}"
echo "GCP_WIF_PROVIDER=${WIF_PROVIDER}"
echo ""
echo "=== Create secrets in Secret Manager ==="
echo "gcloud secrets create telegram-bot-token --project=${PROJECT_ID}"
echo "echo -n 'YOUR_TOKEN' | gcloud secrets versions add telegram-bot-token --data-file=- --project=${PROJECT_ID}"
echo "gcloud secrets create telegram-chat-id --project=${PROJECT_ID}"
echo "echo -n 'YOUR_CHAT_ID' | gcloud secrets versions add telegram-chat-id --data-file=- --project=${PROJECT_ID}"
