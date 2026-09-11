#!/usr/bin/env bash
# Import the manually collected CLMS CLC Italy extracts (already EPSG:3035).
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TARGET="$ROOT/data/processed/allevamenti.gpkg"
for year in 1990 2018; do
  source=$(find "$ROOT/data/raw/copernicus/clc/$year" -maxdepth 1 -type f -name '*.gpkg' -print -quit)
  [[ -n "$source" ]] || { echo "Manca il GeoPackage CLC $year" >&2; exit 1; }
  layer=$(ogrinfo -ro "$source" 2>/dev/null | awk -F': ' '/^[0-9]+: / {sub(/ \(.*/, "", $2); print $2; exit}')
  ogr2ogr -f GPKG -update -overwrite "$TARGET" "$source" "$layer" -nln "copernicus_clc_$year"
  ogrinfo -ro -so "$TARGET" "copernicus_clc_$year" >/dev/null
done
