#!/usr/bin/env bash
# Import every vector layer in the geometry-preserving EU-Hydro GDB extract.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
EXTRACTED="$ROOT/data/raw/copernicus/eu_hydro/v1.3_2006-2012/extracted"
SOURCE=$(find "$EXTRACTED" -type d -name '*.gdb' -print -quit)
TARGET="$ROOT/data/processed/allevamenti.gpkg"

[[ -n "$SOURCE" ]] || { echo "Manca il geodatabase EU-Hydro in $EXTRACTED" >&2; exit 1; }
python3 - "$SOURCE" <<'PY'
import sys
from osgeo import ogr
ogr.UseExceptions()
dataset = ogr.Open(sys.argv[1], 0)
river = next((layer for layer in dataset if layer.GetName().lower().endswith("river_net_l")), None)
if river is None:
    raise SystemExit("Manca il layer River_Net_l")
feature = next((feature for feature in river if feature.GetGeometryRef() is not None), None)
if feature is None:
    raise SystemExit("River_Net_l non contiene geometrie")
if ogr.GT_Flatten(feature.GetGeometryRef().GetGeometryType()) not in (ogr.wkbLineString, ogr.wkbMultiLineString):
    raise SystemExit("River_Net_l non contiene geometrie lineari")
PY
while IFS= read -r layer; do
  name="euhydro_${layer,,}"
  name=${name//\//_}
  name=${name//-/_}
  ogr2ogr -f GPKG -update -overwrite "$TARGET" "$SOURCE" "$layer" -nln "$name"
  ogrinfo -ro -so "$TARGET" "$name" >/dev/null
done < <(ogrinfo -ro "$SOURCE" 2>/dev/null | awk -F': ' '/^[0-9]+: / {sub(/ \(.*/, "", $2); print $2}')
echo "Importati tutti i layer EU-Hydro in $TARGET"
