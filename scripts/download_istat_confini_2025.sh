#!/usr/bin/env bash
# Download and import the fixed 2025 ISTAT administrative-boundary release.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL="https://www.istat.it/storage/cartografia/confini_amministrativi/non_generalizzati/2025/Limiti01012025.zip"
RAW_DIR="$ROOT/data/raw/istat/confini_amministrativi/2025"
ARCHIVE="$RAW_DIR/Limiti01012025.zip"
EXTRACTED="$RAW_DIR/extracted"
GPKG="$ROOT/data/processed/allevamenti.gpkg"

mkdir -p "$RAW_DIR"
if [[ ! -s "$ARCHIVE" ]]; then
  curl --fail --location --retry 3 --output "$ARCHIVE" "$URL"
fi

mkdir -p "$EXTRACTED"
unzip -oq "$ARCHIVE" -d "$EXTRACTED"
printf '%s  %s\n' "$(sha256sum "$ARCHIVE" | cut -d' ' -f1)" "$(basename "$ARCHIVE")" > "$RAW_DIR/SHA256SUMS"
printf '%s\n' "$URL" > "$RAW_DIR/SOURCE_URL.txt"

import_layer() {
  local prefix=$1 layer=$2 source
  source=$(find "$EXTRACTED" -type f -name "${prefix}*.shp" -print -quit)
  [[ -n "$source" ]] || { echo "Shapefile ${prefix}*.shp non trovato" >&2; exit 1; }
  local mode=()
  [[ -f "$GPKG" ]] && mode=(-update -overwrite)
  ogr2ogr -f GPKG "${mode[@]}" "$GPKG" "$source" -nln "$layer" -nlt PROMOTE_TO_MULTI -t_srs EPSG:3035
  ogrinfo -ro -so "$GPKG" "$layer" | grep -q 'Feature Count:'
}

import_layer 'Com' 'istat_comuni_2025'
import_layer 'Prov' 'istat_province_2025'
import_layer 'Reg' 'istat_regioni_2025'
echo "Importati confini ISTAT 2025 in $GPKG"
