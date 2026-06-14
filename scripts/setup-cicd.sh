#!/usr/bin/env bash
# One-time: grant the WIF deploy SA permission to build + deploy to Cloud Run.
# The SA github-digest-bot is already WIF-bound to the GitHub repo.
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-athlete-ai-platform}"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
DEPLOY_SA="github-digest-bot@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_SA="digest-bot@${PROJECT_ID}.iam.gserviceaccount.com"
# Cloud Build runs builds as the default compute service account.
BUILD_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Deploy SA:  ${DEPLOY_SA}"
echo "Runtime SA: ${RUNTIME_SA}"
echo "Build SA:   ${BUILD_SA}"

for ROLE in \
  roles/run.admin \
  roles/cloudbuild.builds.editor \
  roles/artifactregistry.writer \
  roles/serviceusage.serviceUsageConsumer \
  roles/storage.admin; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${DEPLOY_SA}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet
  echo "Granted ${ROLE}"
done

# Deployer must be able to act as the runtime SA to deploy a service that runs as it.
gcloud iam service-accounts add-iam-policy-binding "${RUNTIME_SA}" \
  --member="serviceAccount:${DEPLOY_SA}" \
  --role="roles/iam.serviceAccountUser" \
  --quiet
echo "Granted actAs ${RUNTIME_SA}"

# Deployer must be able to act as the build SA that Cloud Build uses to run builds.
gcloud iam service-accounts add-iam-policy-binding "${BUILD_SA}" \
  --member="serviceAccount:${DEPLOY_SA}" \
  --role="roles/iam.serviceAccountUser" \
  --quiet
echo "Granted actAs ${BUILD_SA}"

echo ""
echo "CI/CD ready. Push to main → .github/workflows/deploy.yml builds + deploys."
