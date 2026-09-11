#!/usr/bin/env bash
# Request the Italy-only EU-Hydro v1.3 vector extract from the CLMS API.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL="https://land.copernicus.eu/api/en/products/eu-hydro/eu-hydro-river-network-database"
REQUEST_URL="https://land.copernicus.eu/api/@datarequest_post"
ENV_FILE="$ROOT/.env"
REQUEST_DIR="$ROOT/data/raw/copernicus/eu_hydro/requests"

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
payload="$REQUEST_DIR/eu_hydro_italy_${timestamp}.request.json"
response="$REQUEST_DIR/eu_hydro_italy_${timestamp}.response.json"

cat > "$payload" <<'JSON'
{
  "Datasets": [{
    "DatasetID": "99585ce3333d49d8adf24b13b1337704",
    "DatasetDownloadInformationID": "e665c694-4d40-4041-8517-1f91e4050126",
    "NUTS": "IT",
    "OutputFormat": "GDB",
    "OutputGCS": "EPSG:3035"
  }]
}
JSON

curl --fail --location --retry 3 -X POST "$REQUEST_URL" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $access_token" \
  --data-binary "@$payload" \
  --output "$response"
printf 'Richiesta inviata: %s\nRisposta: %s\n' "$payload" "$response"
