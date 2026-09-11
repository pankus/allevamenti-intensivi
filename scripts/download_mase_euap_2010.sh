#!/usr/bin/env bash
# Download the official VI EUAP protected-areas layer exposed by the MASE WFS.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL="https://wms.pcn.minambiente.it/ogc?map=/ms_ogc/wfs/EUAP.map&service=wfs&request=getCapabilities"
SOURCE_LAYER="SP.SITIPROTETTI.EUAP"
RAW_DIR="$ROOT/data/raw/mase/euap/2010"
RAW_FILE="$RAW_DIR/euap_2010.gpkg"
GPKG="$ROOT/data/processed/allevamenti.gpkg"

mkdir -p "$RAW_DIR"
if [[ ! -s "$RAW_FILE" ]]; then
  ogr2ogr -f GPKG "$RAW_FILE" "WFS:$URL" "$SOURCE_LAYER"
fi
printf '%s  %s\n' "$(sha256sum "$RAW_FILE" | cut -d' ' -f1)" "$(basename "$RAW_FILE")" > "$RAW_DIR/SHA256SUMS"
printf '%s\n' "$URL" > "$RAW_DIR/SOURCE_URL.txt"
# The WFS exposes latitude,longitude coordinates while declaring conventional EPSG:4326 axes.
ogr2ogr -f GPKG -update -overwrite "$GPKG" "$RAW_FILE" \
  -nln mase_euap_2010 -nlt PROMOTE_TO_MULTI -t_srs EPSG:3035 \
  -ct '+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +step +proj=axisswap +order=2,1'
ogrinfo -ro -so "$GPKG" mase_euap_2010 >/dev/null
echo "Importato EUAP 2010 in $GPKG"
