#!/usr/bin/env bash
# Set az cli defaults (resource group + workspace) và đăng ký môi trường training.
set -euo pipefail

cd "$(dirname "$0")/.."

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-taxi-mlops}"

if [ -z "${WORKSPACE_NAME:-}" ]; then
  echo ">> Không có WORKSPACE_NAME, tự dò trong resource group $RESOURCE_GROUP ..."
  WORKSPACE_NAME=$(az ml workspace list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
fi

echo ">> Resource group: $RESOURCE_GROUP"
echo ">> Workspace: $WORKSPACE_NAME"

az configure --defaults group="$RESOURCE_GROUP" workspace="$WORKSPACE_NAME"

echo ">> Đăng ký environment taxi-fare-train-env"
az ml environment create --file environment/train-env.yml

echo ">> Danh sách compute hiện có:"
az ml compute list -o table
