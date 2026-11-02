#!/usr/bin/env bash
# Deploy the registered model to a Managed Online Endpoint.
set -euo pipefail

cd "$(dirname "$0")/.."

echo ">> Creating online endpoint (no-op if it already exists)"
az ml online-endpoint create --file deployment/endpoint.yml

echo ">> Creating online deployment 'taxi-model-1' (this can take 10-15 minutes)"
az ml online-deployment create --file deployment/deployment.yml --all-traffic

echo ">> Done. Endpoint details:"
az ml online-endpoint show --name taxi-fare-endpoint
