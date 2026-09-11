#!/usr/bin/env bash
# Request Italy-only CLC 1990 and 2018 vector extracts from the CLMS API.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL="https://land.copernicus.eu/api/en/products/corine-land-cover/clc2018"
REQUEST_URL="https://land.copernicus.eu/api/@datarequest_post"
ENV_FILE="$ROOT/.env"
REQUEST_DIR="$ROOT/data/raw/copernicus/clc/requests"

[[ -f "$ENV_FILE" ]] || { echo "Manca $ENV_FILE" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${CLMS_SERVICE_KEY_FILE:?Definire CLMS_SERVICE_KEY_FILE in .env}"
SERVICE_KEY="$ROOT/$CLMS_SERVICE_KEY_FILE"
[[ -f "$SERVICE_KEY" ]] || { echo "Service key non trovata: $SERVICE_KEY" >&2; exit 1; }
access_token=$("$ROOT/scripts/clms_access_token.py" "$SERVICE_KEY")

mkdir -p "$REQUEST_DIR"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
payload="$REQUEST_DIR/clc_italy_1990_2018_${timestamp}.request.json"
response="$REQUEST_DIR/clc_italy_1990_2018_${timestamp}.response.json"

cat > "$payload" <<'JSON'
{
  "Datasets": [
    {
      "DatasetID": "0407d497d3c44bcd93ce8fd5bf78596a",
      "DatasetDownloadInformationID": "1bda2fbd-3230-42ba-98cf-69c96ac063bc",
      "NUTS": "IT",
      "OutputFormat": "GPKG",
      "OutputGCS": "EPSG:3035"
    },
    {
      "DatasetID": "8b393c8e474642d5acb4ed70fc2dc024",
      "DatasetDownloadInformationID": "fd1c53e8-d710-46a6-8363-2febf699c7be",
      "NUTS": "IT",
      "OutputFormat": "GPKG",
      "OutputGCS": "EPSG:3035"
    }
  ]
}
JSON

curl --fail --location --retry 3 -X POST "$REQUEST_URL" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $access_token" \
  --data-binary "@$payload" \
  --output "$response"
printf 'Richiesta inviata: %s\nRisposta: %s\n' "$payload" "$response"
