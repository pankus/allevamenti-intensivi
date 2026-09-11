#!/usr/bin/env bash
# Collect the geometry-preserving GDB extract and import all EU-Hydro vector layers.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TASK_ID=10074359711
RAW_DIR="$ROOT/data/raw/copernicus/eu_hydro/v1.3_2006-2012"
ARCHIVE="$RAW_DIR/eu_hydro_italy_task_${TASK_ID}.zip"

if [[ ! -s "$ARCHIVE" ]]; then
  set -a
  source "$ROOT/.env"
  set +a
  token=$("$ROOT/scripts/clms_access_token.py" "$ROOT/$CLMS_SERVICE_KEY_FILE")
  status=$(mktemp)
  curl --fail --silent --show-error \
    'https://land.copernicus.eu/api/@datarequest_search?status=Finished_ok' \
    -H "Authorization: Bearer $token" -H 'Accept: application/json' > "$status"
  url=$(python3 - "$status" "$TASK_ID" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))[sys.argv[2]]["DownloadURL"])
PY
)
  mkdir -p "$RAW_DIR"
  curl --fail --location --retry 3 --output "$ARCHIVE" "$url"
fi

if ! find "$RAW_DIR/extracted" -type d -name '*.gdb' -print -quit 2>/dev/null | grep -q .; then
  mkdir -p "$RAW_DIR/extracted"
  unzip -oq "$ARCHIVE" -d "$RAW_DIR/extracted"
fi
printf '%s  %s\n' "$(sha256sum "$ARCHIVE" | cut -d' ' -f1)" "$(basename "$ARCHIVE")" > "$RAW_DIR/SHA256SUMS"
printf '%s\n' 'https://land.copernicus.eu/en/products/eu-hydro/eu-hydro-river-network-database' > "$RAW_DIR/SOURCE_URL.txt"
"$ROOT/scripts/import_copernicus_euhydro_italy.sh"
