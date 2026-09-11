#!/usr/bin/env python3
"""Create national kernel-density rasters for pigs and poultry."""
from pathlib import Path
from subprocess import DEVNULL, run
from tempfile import TemporaryDirectory

from osgeo import gdal, ogr

ogr.UseExceptions()
gdal.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/allevamenti.gpkg"
OUTPUT_DIR = ROOT / "data/derived/rasters"
RADIUS = 20_000
PIXEL_SIZE = 2_000
SPECIES = {"Pigs": "pigs", "Poultry": "poultry"}


def weighted_points(path: Path, species: str) -> None:
    source = ogr.Open(str(SOURCE), 0)
    input_points = source.GetLayerByName("megafarms_italy_points_valid")
    municipalities = source.GetLayerByName("istat_comuni_2025")
    output = ogr.GetDriverByName("GPKG").CreateDataSource(str(path))
    layer = output.CreateLayer("points", input_points.GetSpatialRef(), ogr.wkbPoint)
    layer.CreateField(ogr.FieldDefn("weight", ogr.OFTReal))

    input_points.SetAttributeFilter(f'"Type of Animal" = \'{species}\'')
    for point in input_points:
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometry(point.GetGeometryRef())
        feature.SetField("weight", 1.0)
        layer.CreateFeature(feature)

    min_x, max_x, min_y, max_y = municipalities.GetExtent()
    for x, y in ((min_x, min_y), (min_x, max_y), (max_x, min_y), (max_x, max_y)):
        feature = ogr.Feature(layer.GetLayerDefn())
        geometry = ogr.Geometry(ogr.wkbPoint)
        geometry.AddPoint_2D(x, y)
        feature.SetGeometry(geometry)
        feature.SetField("weight", 0.0)
        layer.CreateFeature(feature)
    output = None
    source = None


def national_mask(path: Path) -> None:
    source = ogr.Open(str(SOURCE), 0)
    result = source.ExecuteSQL(
        "SELECT ST_Union(geom) AS geom FROM istat_comuni_2025", dialect="SQLITE"
    )
    boundary_feature = result.GetNextFeature()
    boundary = boundary_feature.GetGeometryRef().Clone()
    source.ReleaseResultSet(result)
    if not boundary.IsValid():
        boundary = ogr.ForceToMultiPolygon(boundary.MakeValid())
    output = ogr.GetDriverByName("GPKG").CreateDataSource(str(path))
    layer = output.CreateLayer("italy", source.GetLayerByName("istat_comuni_2025").GetSpatialRef(), ogr.wkbMultiPolygon)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(boundary)
    layer.CreateFeature(feature)
    output = None
    source = None


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as temporary:
        temporary = Path(temporary)
        mask = temporary / "italy.gpkg"
        national_mask(mask)
        for species, key in SPECIES.items():
            points = temporary / f"{key}.gpkg"
            raw = temporary / f"{key}_raw.tif"
            scaled = temporary / f"{key}_scaled.tif"
            output = OUTPUT_DIR / f"megafarms_kde_20km_{key}.tif"
            weighted_points(points, species)
            run([
                "qgis_process", "run", "native:heatmapkerneldensityestimation", "--",
                f"INPUT={points}|layername=points", f"RADIUS={RADIUS}",
                f"PIXEL_SIZE={PIXEL_SIZE}", "WEIGHT_FIELD=weight", "KERNEL=0",
                "OUTPUT_VALUE=1", f"OUTPUT={raw}",
            ], check=True, stdout=DEVNULL)
            run([
                "gdal_calc.py", "-A", str(raw), "--hideNoData",
                "--calc=where(A == -9999, 0, A * 1000000)",
                "--NoDataValue=-9999", "--type=Float32", "--co=COMPRESS=DEFLATE",
                f"--outfile={scaled}", "--overwrite",
            ], check=True, stdout=DEVNULL)
            output.unlink(missing_ok=True)
            run([
                "gdalwarp", "-cutline", str(mask), "-cl", "italy",
                "-crop_to_cutline", "-dstnodata", "-9999", "-co", "COMPRESS=DEFLATE",
                str(scaled), str(output),
            ], check=True, stdout=DEVNULL)
            run([
                "gdal_edit.py", "-mo", "UNIT=points_per_km2",
                "-mo", f"KERNEL=quartic", "-mo", f"BANDWIDTH_M={RADIUS}",
                "-mo", f"PIXEL_SIZE_M={PIXEL_SIZE}", str(output),
            ], check=True)

            dataset = gdal.Open(str(output))
            band = dataset.GetRasterBand(1)
            if band.GetNoDataValue() != -9999 or dataset.RasterCount != 1:
                raise RuntimeError(f"Raster non valido: {output}")
            print(f"Creato {output} ({dataset.RasterXSize} × {dataset.RasterYSize} pixel)")


if __name__ == "__main__":
    main()
