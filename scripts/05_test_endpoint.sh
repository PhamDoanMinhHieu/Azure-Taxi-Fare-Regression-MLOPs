#!/usr/bin/env bash
# Invoke the deployed endpoint with a sample request.
set -euo pipefail

cd "$(dirname "$0")/.."

az ml online-endpoint invoke \
  --name taxi-fare-endpoint \
  --request-file deployment/sample-request.json
