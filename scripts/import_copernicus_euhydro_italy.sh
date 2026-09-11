#!/usr/bin/env bash
# Import every vector layer in the CLMS Italy-only EU-Hydro package.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/data/raw/copernicus/eu_hydro/v1.3_2006-2012/extracted/Results/EU-Hydro.gpkg"
TARGET="$ROOT/data/processed/allevamenti.gpkg"

[[ -f "$SOURCE" ]] || { echo "Manca $SOURCE" >&2; exit 1; }
while IFS= read -r layer; do
  name="euhydro_${layer,,}"
  name=${name//\//_}
  name=${name//-/_}
  ogr2ogr -f GPKG -update -overwrite "$TARGET" "$SOURCE" "$layer" -nln "$name"
  ogrinfo -ro -so "$TARGET" "$name" >/dev/null
done < <(ogrinfo -ro "$SOURCE" 2>/dev/null | awk -F': ' '/^[0-9]+: / {sub(/ \(.*/, "", $2); print $2}')
echo "Importati tutti i layer EU-Hydro in $TARGET"
