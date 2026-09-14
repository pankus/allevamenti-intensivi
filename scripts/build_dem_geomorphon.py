#!/usr/bin/env python3
"""Sample Copernicus DEM GLO-30 elevation and GRASS geomorphons at megafarm points."""
import csv
import statistics
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from osgeo import gdal, ogr, osr

ogr.UseExceptions()
gdal.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/allevamenti.gpkg"
RAW = ROOT / "data/raw/copernicus/dem/glo30/tiles"
RASTERS = ROOT / "data/derived/rasters"
VECTORS = ROOT / "data/derived/vectors"
RAW_VRT = RASTERS / "copernicus_dem_glo30_point_tiles.vrt"
DEM_3035 = RASTERS / "copernicus_dem_glo30_100m.tif"
GEOMORPHON_3035 = RASTERS / "copernicus_dem_glo30_geomorphon_100m.tif"
OUTPUT = VECTORS / "megafarms_dem_geomorphon.gpkg"
CSV_POINTS = VECTORS / "megafarms_dem_geomorphon_points.csv"
CSV_SUMMARY = VECTORS / "megafarms_dem_geomorphon_summary.csv"
POINT_LAYER = "megafarms_points_dem_geomorphon"
SUMMARY_LAYER = "megafarms_dem_geomorphon_summary"

GEOMORPHON = {
    1: "flat",
    2: "summit",
    3: "ridge",
    4: "shoulder",
    5: "spur",
    6: "slope",
    7: "hollow",
    8: "footslope",
    9: "valley",
    10: "depression",
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def sample(dataset: gdal.Dataset, x: float, y: float, fallback_cells: int = 0) -> float | None:
    inv = gdal.InvGeoTransform(dataset.GetGeoTransform())
    px, py = gdal.ApplyGeoTransform(inv, x, y)
    ix, iy = int(px), int(py)
    if ix < 0 or iy < 0 or ix >= dataset.RasterXSize or iy >= dataset.RasterYSize:
        return None
    band = dataset.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    value = band.ReadAsArray(ix, iy, 1, 1)[0][0]
    if nodata is None or value != nodata:
        return float(value)
    if not fallback_cells:
        return None
    x0 = max(0, ix - fallback_cells)
    y0 = max(0, iy - fallback_cells)
    array = band.ReadAsArray(
        x0, y0,
        min(dataset.RasterXSize - x0, fallback_cells * 2 + 1),
        min(dataset.RasterYSize - y0, fallback_cells * 2 + 1),
    )
    best = None
    for row in range(array.shape[0]):
        for col in range(array.shape[1]):
            candidate = array[row][col]
            if candidate == nodata:
                continue
            distance = (x0 + col - ix) ** 2 + (y0 + row - iy) ** 2
            if best is None or distance < best[0]:
                best = (distance, candidate)
    return float(best[1]) if best else None


def read_points():
    src = ogr.Open(str(SOURCE), 0)
    layer = src.GetLayerByName("megafarms_italy_points_valid")
    src_srs = layer.GetSpatialRef()
    src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    wgs = osr.SpatialReference(); wgs.ImportFromEPSG(4326)
    wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    to_wgs = osr.CoordinateTransformation(src_srs, wgs)
    rows = []
    for feature in layer:
        geom = feature.GetGeometryRef().Clone()
        lonlat = geom.Clone(); lonlat.Transform(to_wgs)
        rows.append({
            "fid": feature.GetFID(),
            "animal": feature["Type of Animal"],
            "country": feature["CountryName"],
            "x": geom.GetX(),
            "y": geom.GetY(),
            "lon": lonlat.GetX(),
            "lat": lonlat.GetY(),
            "geom": geom.Clone(),
        })
    return rows, layer.GetSpatialRef()


def build_rasters(points):
    tiles = sorted(RAW.glob("Copernicus_DSM_COG_10_*_DEM.tif"))
    if not tiles:
        raise SystemExit("DEM GLO-30 non trovato: esegui scripts/download_copernicus_dem_glo30_tiles.sh")
    run(["gdalbuildvrt", "-q", str(RAW_VRT), *map(str, tiles)])

    xs = [row["x"] for row in points]
    ys = [row["y"] for row in points]
    buffer = 50_000
    extent = [str(min(xs) - buffer), str(min(ys) - buffer), str(max(xs) + buffer), str(max(ys) + buffer)]

    DEM_3035.unlink(missing_ok=True)
    GEOMORPHON_3035.unlink(missing_ok=True)
    run([
        "gdalwarp", "-q", "-t_srs", "EPSG:3035", "-tr", "100", "100", "-tap",
        "-te", *extent, "-r", "bilinear", "-co", "COMPRESS=DEFLATE",
        str(RAW_VRT), str(DEM_3035),
    ])

    with tempfile.TemporaryDirectory(prefix="grass_geomorphon_"):
        script = f"""
set -euo pipefail
r.import input='{DEM_3035}' output=dem --overwrite --quiet
g.region raster=dem --quiet
r.geomorphon elevation=dem forms=forms search=10 skip=0 flat=1 --overwrite --quiet
r.out.gdal input=forms output='{GEOMORPHON_3035}' format=GTiff type=Byte createopt='COMPRESS=DEFLATE' --overwrite --quiet
"""
        run(["grass", "--tmp-project", str(DEM_3035), "--exec", "bash", "-c", script])


def write_outputs(rows, srs):
    OUTPUT.unlink(missing_ok=True)
    ds = ogr.GetDriverByName("GPKG").CreateDataSource(str(OUTPUT))
    points = ds.CreateLayer(POINT_LAYER, srs, ogr.wkbPoint, ["SPATIAL_INDEX=YES"])
    for name, typ in (("source_fid", ogr.OFTInteger64), ("CountryName", ogr.OFTString), ("Type of Animal", ogr.OFTString), ("dem_elev_m", ogr.OFTReal), ("geomorphon", ogr.OFTInteger), ("geomorphon_label", ogr.OFTString)):
        points.CreateField(ogr.FieldDefn(name, typ))
    for row in rows:
        feature = ogr.Feature(points.GetLayerDefn())
        feature.SetGeometry(row["geom"])
        feature.SetField("source_fid", row["fid"])
        feature.SetField("CountryName", row["country"])
        feature.SetField("Type of Animal", row["animal"])
        if row["elev"] is not None:
            feature.SetField("dem_elev_m", row["elev"])
        if row["geomorphon"] is not None:
            feature.SetField("geomorphon", row["geomorphon"])
            feature.SetField("geomorphon_label", GEOMORPHON.get(row["geomorphon"], "unknown"))
        points.CreateFeature(feature)

    table = ds.CreateLayer(SUMMARY_LAYER, geom_type=ogr.wkbNone)
    fields = (("animal", ogr.OFTString), ("geomorphon", ogr.OFTInteger), ("geomorphon_label", ogr.OFTString), ("point_count", ogr.OFTInteger), ("share_percent", ogr.OFTReal), ("elev_median", ogr.OFTReal), ("elev_q1", ogr.OFTReal), ("elev_q3", ogr.OFTReal))
    for name, typ in fields:
        table.CreateField(ogr.FieldDefn(name, typ))

    summary_rows = []
    for animal in ("Pigs", "Poultry", "All"):
        subset = rows if animal == "All" else [r for r in rows if r["animal"] == animal]
        total = len(subset)
        counts = Counter(r["geomorphon"] for r in subset)
        for code in sorted(k for k in counts if k is not None):
            elevs = sorted(r["elev"] for r in subset if r["geomorphon"] == code and r["elev"] is not None)
            q = statistics.quantiles(elevs, n=4, method="inclusive") if len(elevs) > 1 else [elevs[0]] * 3
            row = (animal, code, GEOMORPHON.get(code, "unknown"), counts[code], counts[code] / total * 100, statistics.median(elevs), q[0], q[2])
            summary_rows.append(row)
            feature = ogr.Feature(table.GetLayerDefn())
            for i, value in enumerate(row):
                feature.SetField(i, value)
            table.CreateFeature(feature)
    ds = None

    with CSV_POINTS.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("source_fid", "animal", "dem_elev_m", "geomorphon", "geomorphon_label", "x_3035", "y_3035", "lon", "lat"))
        for row in rows:
            writer.writerow((row["fid"], row["animal"], row["elev"], row["geomorphon"], GEOMORPHON.get(row["geomorphon"], "") if row["geomorphon"] else "", row["x"], row["y"], row["lon"], row["lat"]))
    with CSV_SUMMARY.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("animal", "geomorphon", "geomorphon_label", "point_count", "share_percent", "elev_median", "elev_q1", "elev_q3"))
        writer.writerows(summary_rows)

    for layer in (POINT_LAYER, SUMMARY_LAYER):
        run(["ogr2ogr", "-f", "GPKG", "-update", "-overwrite", str(SOURCE), str(OUTPUT), layer, "-nln", layer])


def main() -> None:
    RASTERS.mkdir(parents=True, exist_ok=True)
    VECTORS.mkdir(parents=True, exist_ok=True)
    points, srs = read_points()
    build_rasters(points)

    dem = gdal.Open(str(DEM_3035))
    forms = gdal.Open(str(GEOMORPHON_3035))
    for row in points:
        row["elev"] = sample(dem, row["x"], row["y"])
        value = sample(forms, row["x"], row["y"], fallback_cells=10)
        row["geomorphon"] = int(value) if value is not None else None
    write_outputs(points, srs)
    print(f"Creati {OUTPUT}, {CSV_POINTS}, {CSV_SUMMARY}")
    print(f"DEM EPSG:3035: {DEM_3035}")
    print(f"Geomorphon EPSG:3035: {GEOMORPHON_3035}")
    print(f"Valori mancanti: quota={sum(row['elev'] is None for row in points)}, geomorphon={sum(row['geomorphon'] is None for row in points)}")


if __name__ == "__main__":
    main()
