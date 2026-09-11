#!/usr/bin/env python3
"""Measure point intersections and distances to Natura 2000 and EUAP separately."""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median
from subprocess import run

from osgeo import ogr

ogr.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/allevamenti.gpkg"
OUTPUT = ROOT / "data/derived/vectors/megafarms_protected_areas.gpkg"
CSV = ROOT / "data/derived/vectors/megafarms_protected_areas_summary.csv"
POINT_LAYER = "megafarms_points_protected_areas"
TABLE_LAYER = "megafarms_protected_areas_summary"
SEARCH_RADII = (1_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000)
DATASETS = {
    "natura2000": ("mase_natura2000_2025", "site_code"),
    "euap": ("mase_euap_2010", "codice_are"),
}


def valid_geometry(feature: ogr.Feature) -> ogr.Geometry:
    geometry = feature.GetGeometryRef()
    return geometry if geometry.IsValid() else geometry.MakeValid()


def proximity(layer: ogr.Layer, point: ogr.Geometry, id_field: str) -> tuple[int, float, str]:
    layer.SetSpatialFilter(point)
    intersections = []
    for feature in layer:
        geometry = valid_geometry(feature)
        if geometry.Intersects(point):
            intersections.append((str(feature[id_field]), geometry))
    layer.SetSpatialFilter(None)
    if intersections:
        return len(intersections), 0.0, min(site_id for site_id, _ in intersections)

    for radius in SEARCH_RADII:
        layer.SetSpatialFilter(point.Buffer(radius))
        candidates = [
            (valid_geometry(feature).Distance(point), str(feature[id_field])) for feature in layer
        ]
        layer.SetSpatialFilter(None)
        if candidates:
            distance, site_id = min(candidates, key=lambda item: (item[0], item[1]))
            return 0, distance, site_id
    raise RuntimeError("Nessuna area trovata entro 500 km")


def main() -> None:
    source = ogr.Open(str(SOURCE), 0)
    points = source.GetLayerByName("megafarms_italy_points_valid")
    datasets = {
        key: (source.GetLayerByName(layer_name), id_field)
        for key, (layer_name, id_field) in DATASETS.items()
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)
    output = ogr.GetDriverByName("GPKG").CreateDataSource(str(OUTPUT))
    attributed = output.CreateLayer(POINT_LAYER, points.GetSpatialRef(), ogr.wkbPoint, ["SPATIAL_INDEX=YES"])
    for name, field_type in (
        ("source_fid", ogr.OFTInteger64), ("CountryName", ogr.OFTString),
        ("Type of Animal", ogr.OFTString),
        ("n2000_in", ogr.OFTInteger), ("n2000_n", ogr.OFTInteger),
        ("n2000_m", ogr.OFTReal), ("n2000_id", ogr.OFTString),
        ("euap_in", ogr.OFTInteger), ("euap_n", ogr.OFTInteger),
        ("euap_m", ogr.OFTReal), ("euap_id", ogr.OFTString),
    ):
        attributed.CreateField(ogr.FieldDefn(name, field_type))

    measurements = defaultdict(list)
    for point in points:
        geometry = point.GetGeometryRef()
        result = {
            key: proximity(layer, geometry, id_field)
            for key, (layer, id_field) in datasets.items()
        }
        feature = ogr.Feature(attributed.GetLayerDefn())
        feature.SetGeometry(geometry)
        feature.SetField("source_fid", point.GetFID())
        feature.SetField("CountryName", point["CountryName"])
        feature.SetField("Type of Animal", point["Type of Animal"])
        for key, prefix in (("natura2000", "n2000"), ("euap", "euap")):
            intersections, distance, site_id = result[key]
            feature.SetField(f"{prefix}_in", int(intersections > 0))
            feature.SetField(f"{prefix}_n", intersections)
            feature.SetField(f"{prefix}_m", distance)
            feature.SetField(f"{prefix}_id", site_id)
            measurements[(point["Type of Animal"], key)].append(distance)
        attributed.CreateFeature(feature)

    table = output.CreateLayer(TABLE_LAYER, geom_type=ogr.wkbNone)
    for name, field_type in (
        ("animal", ogr.OFTString), ("protected_dataset", ogr.OFTString),
        ("total_points", ogr.OFTInteger), ("inside_count", ogr.OFTInteger),
        ("within_1km", ogr.OFTInteger), ("within_5km", ogr.OFTInteger),
        ("median_m", ogr.OFTReal),
    ):
        table.CreateField(ogr.FieldDefn(name, field_type))

    rows = []
    for animal in ("Pigs", "Poultry"):
        for dataset in DATASETS:
            distances = measurements[(animal, dataset)]
            rows.append((
                animal, dataset, len(distances), sum(value == 0 for value in distances),
                sum(value <= 1_000 for value in distances),
                sum(value <= 5_000 for value in distances), median(distances),
            ))
    for row in rows:
        feature = ogr.Feature(table.GetLayerDefn())
        for index, value in enumerate(row):
            feature.SetField(index, value)
        table.CreateFeature(feature)
    output = None
    source = None

    with CSV.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow((
            "animal", "protected_dataset", "total_points", "inside_count",
            "within_1km", "within_5km", "median_m",
        ))
        writer.writerows(rows)

    for layer in (POINT_LAYER, TABLE_LAYER):
        run([
            "ogr2ogr", "-f", "GPKG", "-update", "-overwrite", str(SOURCE),
            str(OUTPUT), layer, "-nln", layer,
        ], check=True)

    print(f"Creati {POINT_LAYER}, {TABLE_LAYER} e {CSV}")
    for row in rows:
        print(f"{row[0]} / {row[1]}: dentro={row[3]}, entro 1 km={row[4]}, entro 5 km={row[5]}")


if __name__ == "__main__":
    main()
