#!/usr/bin/env python3
"""Create a 10 km national grid and point densities by animal type."""
from collections import Counter
from math import ceil, floor
from pathlib import Path
from subprocess import run

from osgeo import ogr, osr

ogr.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/allevamenti.gpkg"
OUTPUT = ROOT / "data/derived/vectors/megafarms_grid_10km.gpkg"
GRID_SIZE = 10_000
SPECIES = {
    "Pigs": "megafarms_grid_10km_pigs",
    "Poultry": "megafarms_grid_10km_poultry",
}


def square(x: int, y: int) -> ogr.Geometry:
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for px, py in ((x, y), (x + GRID_SIZE, y), (x + GRID_SIZE, y + GRID_SIZE),
                   (x, y + GRID_SIZE), (x, y)):
        ring.AddPoint_2D(px, py)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    return polygon


def main() -> None:
    source = ogr.Open(str(SOURCE), 0)
    boundary_result = source.ExecuteSQL(
        "SELECT ST_Union(geom) AS geom FROM istat_comuni_2025", dialect="SQLITE"
    )
    boundary_feature = boundary_result.GetNextFeature()
    boundary = boundary_feature.GetGeometryRef().Clone()
    source.ReleaseResultSet(boundary_result)

    counts = {species: Counter() for species in SPECIES}
    points = source.GetLayerByName("megafarms_italy_points_valid")
    for feature in points:
        geometry = feature.GetGeometryRef()
        cell = (floor(geometry.GetX() / GRID_SIZE), floor(geometry.GetY() / GRID_SIZE))
        counts[feature["Type of Animal"]][cell] += 1

    min_x, max_x, min_y, max_y = boundary.GetEnvelope()
    columns = range(floor(min_x / GRID_SIZE), ceil(max_x / GRID_SIZE))
    rows = range(floor(min_y / GRID_SIZE), ceil(max_y / GRID_SIZE))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)
    output = ogr.GetDriverByName("GPKG").CreateDataSource(str(OUTPUT))
    crs = osr.SpatialReference()
    crs.ImportFromEPSG(3035)
    layers = {}
    for species, name in SPECIES.items():
        layer = output.CreateLayer(name, crs, ogr.wkbPolygon, ["SPATIAL_INDEX=YES"])
        for field in (
            ogr.FieldDefn("grid_id", ogr.OFTString),
            ogr.FieldDefn("grid_col", ogr.OFTInteger),
            ogr.FieldDefn("grid_row", ogr.OFTInteger),
            ogr.FieldDefn("cell_km2", ogr.OFTReal),
            ogr.FieldDefn("land_km2", ogr.OFTReal),
            ogr.FieldDefn("point_count", ogr.OFTInteger),
            ogr.FieldDefn("density_km2", ogr.OFTReal),
        ):
            layer.CreateField(field)
        layers[species] = layer

    totals = Counter()
    cell_count = 0
    for column in columns:
        for row in rows:
            geometry = square(column * GRID_SIZE, row * GRID_SIZE)
            land_km2 = geometry.Intersection(boundary).GetArea() / 1_000_000
            if not land_km2:
                continue
            cell_count += 1
            for species, layer in layers.items():
                count = counts[species][(column, row)]
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetGeometry(geometry)
                feature.SetField("grid_id", f"10km_{column}_{row}")
                feature.SetField("grid_col", column)
                feature.SetField("grid_row", row)
                feature.SetField("cell_km2", 100.0)
                feature.SetField("land_km2", land_km2)
                feature.SetField("point_count", count)
                feature.SetField("density_km2", count / 100.0)
                layer.CreateFeature(feature)
                totals[species] += count

    output = None
    source = None
    expected = {species: sum(values.values()) for species, values in counts.items()}
    if totals != expected:
        raise RuntimeError(f"Conteggi persi: attesi {expected}, ottenuti {dict(totals)}")

    for layer in SPECIES.values():
        run([
            "ogr2ogr", "-f", "GPKG", "-update", "-overwrite", str(SOURCE),
            str(OUTPUT), layer, "-nln", layer,
        ], check=True)

    print(f"Create {cell_count} celle in {OUTPUT}")
    print(", ".join(f"{species}: {totals[species]} punti" for species in SPECIES))


if __name__ == "__main__":
    main()
