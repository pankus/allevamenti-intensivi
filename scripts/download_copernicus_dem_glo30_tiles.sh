#!/usr/bin/env bash
# Download Copernicus DEM GLO-30 tiles that contain the valid megafarm points.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL="https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N45_00_E010_00_DEM/Copernicus_DSM_COG_10_N45_00_E010_00_DEM.tif"
OUT="$ROOT/data/raw/copernicus/dem/glo30/tiles"
LIST="$OUT/tile_urls.txt"

mkdir -p "$OUT"
python3 - <<'PY' > "$LIST"
from osgeo import ogr, osr
src = ogr.Open('data/processed/allevamenti.gpkg')
points = src.GetLayerByName('megafarms_italy_points_valid')
src_srs = points.GetSpatialRef()
src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
wgs = osr.SpatialReference(); wgs.ImportFromEPSG(4326)
wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
ct = osr.CoordinateTransformation(src_srs, wgs)
tiles = set()
for feature in points:
    geom = feature.GetGeometryRef().Clone(); geom.Transform(ct)
    tiles.add((int(geom.GetY() // 1), int(geom.GetX() // 1)))
for lat, lon in sorted(tiles):
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    name = f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
    print(f"https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif")
PY

while read -r tile_url; do
  name=$(basename "$tile_url")
  if [[ ! -s "$OUT/$name" ]]; then
    curl --fail --location --retry 3 --continue-at - --output "$OUT/$name" "$tile_url"
  fi
done < "$LIST"

(cd "$OUT" && sha256sum *.tif > SHA256SUMS)
cat > "$OUT/README.txt" <<EOF
Fonte: Copernicus DEM GLO-30, Cloud Optimized GeoTIFF public bucket.
URL indice usato dal controllo: $URL
Tile URL: vedi tile_urls.txt
Download UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Licenza/condizioni: Copernicus DEM, uso libero con attribuzione secondo documentazione Copernicus/ESA.
Criterio: scaricati solo i tile 1°x1° che contengono almeno un punto megafarms_italy_points_valid.
EOF
printf 'Tile GLO-30 scaricati/verificati in %s\n' "$OUT"
