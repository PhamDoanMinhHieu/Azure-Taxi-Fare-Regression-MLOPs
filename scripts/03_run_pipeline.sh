#!/usr/bin/env bash
# Submit the pipeline job (prep -> train -> evaluate -> register) to Azure ML.
set -euo pipefail

cd "$(dirname "$0")/.."

echo ">> Submit pipeline job"
az ml job create --file pipeline.yml --stream
