#!/usr/bin/env bash
# Provision Resource Group + Azure ML Workspace + Compute Cluster bằng Bicep.
set -euo pipefail

cd "$(dirname "$0")/.."

LOCATION="${LOCATION:-southeastasia}"

echo ">> az login (nếu chưa đăng nhập)"
az account show > /dev/null 2>&1 || az login

echo ">> Deploy infra (subscription-scope)"
az deployment sub create \
  --name taxi-mlops-infra \
  --location "$LOCATION" \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json

echo ">> Xong. Lấy thông tin workspace vừa tạo:"
az deployment sub show --name taxi-mlops-infra --query properties.outputs -o json
