#!/usr/bin/env bash
# Download the official MASE Natura 2000 cartography transmitted in December 2025.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL="https://download.mase.gov.it/Natura2000/Trasmissione%20CE_dicembre2025/sic_zps_ita_32_daticartografici.zip"
RAW_DIR="$ROOT/data/raw/mase/natura2000/2025-12"
ARCHIVE="$RAW_DIR/sic_zps_ita_32_daticartografici.zip"
EXTRACTED="$RAW_DIR/extracted"
GPKG="$ROOT/data/processed/allevamenti.gpkg"

mkdir -p "$RAW_DIR"
[[ -s "$ARCHIVE" ]] || curl --fail --location --retry 3 --output "$ARCHIVE" "$URL"
mkdir -p "$EXTRACTED"
unzip -oq "$ARCHIVE" -d "$EXTRACTED"
printf '%s  %s\n' "$(sha256sum "$ARCHIVE" | cut -d' ' -f1)" "$(basename "$ARCHIVE")" > "$RAW_DIR/SHA256SUMS"
printf '%s\n' "$URL" > "$RAW_DIR/SOURCE_URL.txt"

mapfile -t shapes < <(find "$EXTRACTED" -type f -iname '*.shp' | sort)
[[ ${#shapes[@]} -eq 1 ]] || { echo "Atteso un solo shapefile, trovati ${#shapes[@]}" >&2; exit 1; }
ogr2ogr -f GPKG -update -overwrite "$GPKG" "${shapes[0]}" \
  -nln mase_natura2000_2025 -nlt PROMOTE_TO_MULTI -t_srs EPSG:3035
ogrinfo -ro -so "$GPKG" mase_natura2000_2025 | grep -q 'Feature Count:'
echo "Importata Rete Natura 2000 MASE 2025 in $GPKG"
