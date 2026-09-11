#!/usr/bin/env python3
"""Attribute CLC 1990/2018 classes to current megafarm locations."""
import csv
from collections import Counter
from pathlib import Path
from subprocess import run

from osgeo import ogr

ogr.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/allevamenti.gpkg"
OUTPUT = ROOT / "data/derived/vectors/megafarms_clc_transitions.gpkg"
CSV = ROOT / "data/derived/vectors/megafarms_clc_transitions.csv"
POINT_LAYER = "megafarms_points_clc_1990_2018"
TABLE_LAYER = "megafarms_clc_transitions"
NEAREST_TOLERANCE = 200
LEVEL_1 = {
    "1": "Superfici artificiali",
    "2": "Superfici agricole",
    "3": "Territori boscati e ambienti seminaturali",
    "4": "Zone umide",
    "5": "Corpi idrici",
}


def clc_code(
    layer: ogr.Layer, point: ogr.Geometry, field: str
) -> tuple[str | None, bool, float | None]:
    layer.SetSpatialFilter(point)
    candidates = [feature for feature in layer if feature.GetGeometryRef().Intersects(point)]
    layer.SetSpatialFilter(None)
    if candidates:
        contained = [feature for feature in candidates if feature.GetGeometryRef().Contains(point)]
        if contained:
            candidates = contained
        candidates.sort(key=lambda feature: (feature[field], feature.GetFID()))
        return candidates[0][field], len(candidates) > 1, 0.0

    layer.SetSpatialFilter(point.Buffer(NEAREST_TOLERANCE))
    nearby = sorted(
        (feature.GetGeometryRef().Distance(point), feature[field], feature.GetFID())
        for feature in layer
    )
    layer.SetSpatialFilter(None)
    if nearby and nearby[0][0] <= NEAREST_TOLERANCE:
        return nearby[0][1], False, nearby[0][0]
    return None, False, None


def main() -> None:
    source = ogr.Open(str(SOURCE), 0)
    points = source.GetLayerByName("megafarms_italy_points_valid")
    clc_1990 = source.GetLayerByName("copernicus_clc_1990")
    clc_2018 = source.GetLayerByName("copernicus_clc_2018")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)
    output = ogr.GetDriverByName("GPKG").CreateDataSource(str(OUTPUT))
    attributed = output.CreateLayer(POINT_LAYER, points.GetSpatialRef(), ogr.wkbPoint, ["SPATIAL_INDEX=YES"])
    fields = (
        ("source_fid", ogr.OFTInteger64),
        ("CountryName", ogr.OFTString),
        ("Type of Animal", ogr.OFTString),
        ("clc_1990", ogr.OFTString),
        ("clc_2018", ogr.OFTString),
        ("clc1_1990", ogr.OFTString),
        ("clc1_2018", ogr.OFTString),
        ("clc1990_m", ogr.OFTReal),
        ("clc2018_m", ogr.OFTReal),
        ("clc_changed", ogr.OFTInteger),
    )
    for name, field_type in fields:
        attributed.CreateField(ogr.FieldDefn(name, field_type))

    transitions = Counter()
    ambiguous = Counter()
    missing = Counter()
    nearest = Counter()
    for point in points:
        geometry = point.GetGeometryRef()
        code_1990, ambiguous_1990, distance_1990 = clc_code(clc_1990, geometry, "code_90")
        code_2018, ambiguous_2018, distance_2018 = clc_code(clc_2018, geometry, "Code_18")
        ambiguous[1990] += ambiguous_1990
        ambiguous[2018] += ambiguous_2018
        missing[1990] += code_1990 is None
        missing[2018] += code_2018 is None
        nearest[1990] += bool(distance_1990)
        nearest[2018] += bool(distance_2018)

        feature = ogr.Feature(attributed.GetLayerDefn())
        feature.SetGeometry(geometry)
        feature.SetField("source_fid", point.GetFID())
        feature.SetField("CountryName", point["CountryName"])
        feature.SetField("Type of Animal", point["Type of Animal"])
        if code_1990:
            feature.SetField("clc_1990", code_1990)
            feature.SetField("clc1_1990", LEVEL_1[code_1990[0]])
        if code_2018:
            feature.SetField("clc_2018", code_2018)
            feature.SetField("clc1_2018", LEVEL_1[code_2018[0]])
        if distance_1990 is not None:
            feature.SetField("clc1990_m", distance_1990)
        if distance_2018 is not None:
            feature.SetField("clc2018_m", distance_2018)
        if code_1990 and code_2018:
            feature.SetField("clc_changed", int(code_1990 != code_2018))
        attributed.CreateFeature(feature)
        transitions[(point["Type of Animal"], code_1990 or "NA", code_2018 or "NA")] += 1

    table = output.CreateLayer(TABLE_LAYER, geom_type=ogr.wkbNone)
    for name, field_type in (
        ("animal", ogr.OFTString), ("clc_1990", ogr.OFTString),
        ("clc_2018", ogr.OFTString), ("point_count", ogr.OFTInteger),
        ("share_percent", ogr.OFTReal),
    ):
        table.CreateField(ogr.FieldDefn(name, field_type))

    rows = []
    for animal in ("Pigs", "Poultry"):
        total = sum(count for (kind, _, _), count in transitions.items() if kind == animal)
        for (kind, code_1990, code_2018), count in sorted(transitions.items()):
            if kind != animal:
                continue
            rows.append((animal, code_1990, code_2018, count, count / total * 100))
    for code_1990, code_2018 in sorted({(a, b) for _, a, b in transitions}):
        count = sum(value for (_, a, b), value in transitions.items() if (a, b) == (code_1990, code_2018))
        rows.append(("All", code_1990, code_2018, count, count / points.GetFeatureCount() * 100))

    for row in rows:
        feature = ogr.Feature(table.GetLayerDefn())
        for index, value in enumerate(row):
            feature.SetField(index, value)
        table.CreateFeature(feature)
    output = None
    source = None

    with CSV.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("animal", "clc_1990", "clc_2018", "point_count", "share_percent"))
        writer.writerows(rows)

    for layer in (POINT_LAYER, TABLE_LAYER):
        run([
            "ogr2ogr", "-f", "GPKG", "-update", "-overwrite", str(SOURCE),
            str(OUTPUT), layer, "-nln", layer,
        ], check=True)

    print(f"Creati {POINT_LAYER}, {TABLE_LAYER} e {CSV}")
    print(f"Classi mancanti: 1990={missing[1990]}, 2018={missing[2018]}")
    print(f"Assegnazioni al poligono più vicino: 1990={nearest[1990]}, 2018={nearest[2018]}")
    print(f"Punti su più poligoni: 1990={ambiguous[1990]}, 2018={ambiguous[2018]}")


if __name__ == "__main__":
    main()
