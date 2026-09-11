#!/usr/bin/env bash
# Download ISPRA's national 1:250,000 hydrographic network and import its vector layer.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL="https://sdi.isprambiente.it/download_ogc/idro/Idrografia_reticolo_corsi_acqua_.gpkg"
RAW_DIR="$ROOT/data/raw/ispra/reticolo_idrografico/1_250000"
RAW_FILE="$RAW_DIR/Idrografia_reticolo_corsi_acqua.gpkg"
GPKG="$ROOT/data/processed/allevamenti.gpkg"

mkdir -p "$RAW_DIR"
[[ -s "$RAW_FILE" ]] || curl --fail --location --retry 3 --output "$RAW_FILE" "$URL"
printf '%s  %s\n' "$(sha256sum "$RAW_FILE" | cut -d' ' -f1)" "$(basename "$RAW_FILE")" > "$RAW_DIR/SHA256SUMS"
printf '%s\n' "$URL" > "$RAW_DIR/SOURCE_URL.txt"

layer=$(ogrinfo -ro "$RAW_FILE" 2>/dev/null | awk -F': ' '/^[0-9]+: / {sub(/ \(.*/, "", $2); print $2; exit}')
[[ -n "$layer" ]] || { echo "Layer ISPRA non trovato" >&2; exit 1; }
ogr2ogr -f GPKG -update -overwrite "$GPKG" "$RAW_FILE" "$layer" \
  -nln ispra_reticolo_idrografico -t_srs EPSG:3035
ogrinfo -ro -so "$GPKG" ispra_reticolo_idrografico | grep -q 'Feature Count:'
echo "Importato reticolo idrografico ISPRA in $GPKG"
