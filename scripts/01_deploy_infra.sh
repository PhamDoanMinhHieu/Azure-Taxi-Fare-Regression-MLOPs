#!/usr/bin/env bash
# Provision Resource Group + Azure ML Workspace + Compute Cluster using Bicep.
set -euo pipefail

cd "$(dirname "$0")/.."

LOCATION="${LOCATION:-southeastasia}"

echo ">> az login (if not already logged in)"
az account show > /dev/null 2>&1 || az login

echo ">> Deploy infra (subscription-scope)"
az deployment sub create \
  --name taxi-mlops-infra \
  --location "$LOCATION" \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json

echo ">> Done. Fetching details of the newly created workspace:"
az deployment sub show --name taxi-mlops-infra --query properties.outputs -o json
