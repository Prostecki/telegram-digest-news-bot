#!/usr/bin/env bash
# One-time: grant the WIF deploy SA permission to build + deploy to Cloud Run.
# The SA github-digest-bot is already WIF-bound to the GitHub repo.
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-athlete-ai-platform}"
DEPLOY_SA="github-digest-bot@${PROJECT_ID}.iam.gserviceaccount.com"
RUNTIME_SA="digest-bot@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Deploy SA:  ${DEPLOY_SA}"
echo "Runtime SA: ${RUNTIME_SA}"

for ROLE in \
  roles/run.admin \
  roles/cloudbuild.builds.editor \
  roles/artifactregistry.writer; do
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

echo ""
echo "CI/CD ready. Push to main → .github/workflows/deploy.yml builds + deploys."
