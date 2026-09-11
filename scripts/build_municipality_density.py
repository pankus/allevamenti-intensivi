#!/usr/bin/env python3
"""Count megafarm locations and calculate density by 2025 municipality."""
from collections import Counter
from pathlib import Path
from subprocess import run

from osgeo import ogr

ogr.UseExceptions()

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/allevamenti.gpkg"
OUTPUT = ROOT / "data/derived/vectors/megafarms_municipality_density.gpkg"
SPECIES = {
    "Pigs": "megafarms_municipality_2025_pigs",
    "Poultry": "megafarms_municipality_2025_poultry",
}


def main() -> None:
    source = ogr.Open(str(SOURCE), 0)
    municipalities = source.GetLayerByName("istat_comuni_2025")
    points = source.GetLayerByName("megafarms_italy_points_valid")
    counts = {species: Counter() for species in SPECIES}
    ambiguous = 0

    for point in points:
        geometry = point.GetGeometryRef()
        municipalities.SetSpatialFilter(geometry)
        candidates = [
            municipality for municipality in municipalities
            if municipality.GetGeometryRef().Intersects(geometry)
        ]
        municipalities.SetSpatialFilter(None)
        if not candidates:
            raise RuntimeError(f"Punto {point.GetFID()} fuori da ogni comune")
        contained = [candidate for candidate in candidates if candidate.GetGeometryRef().Contains(geometry)]
        if contained:
            candidates = contained
        if len(candidates) > 1:
            ambiguous += 1
        municipality = min(candidates, key=lambda feature: feature["PRO_COM_T"])
        counts[point["Type of Animal"]][municipality.GetFID()] += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)
    output = ogr.GetDriverByName("GPKG").CreateDataSource(str(OUTPUT))
    layers = {}
    for species, name in SPECIES.items():
        layer = output.CreateLayer(
            name, municipalities.GetSpatialRef(), ogr.wkbMultiPolygon, ["SPATIAL_INDEX=YES"]
        )
        for field in (
            ogr.FieldDefn("pro_com_t", ogr.OFTString),
            ogr.FieldDefn("comune", ogr.OFTString),
            ogr.FieldDefn("cod_reg", ogr.OFTInteger),
            ogr.FieldDefn("cod_prov", ogr.OFTInteger),
            ogr.FieldDefn("area_km2", ogr.OFTReal),
            ogr.FieldDefn("point_count", ogr.OFTInteger),
            ogr.FieldDefn("density_km2", ogr.OFTReal),
        ):
            layer.CreateField(field)
        layers[species] = layer

    totals = Counter()
    repaired = 0
    municipalities.ResetReading()
    for municipality in municipalities:
        geometry = municipality.GetGeometryRef().Clone()
        if not geometry.IsValid():
            geometry = ogr.ForceToMultiPolygon(geometry.MakeValid())
            repaired += 1
        area_km2 = geometry.GetArea() / 1_000_000
        for species, layer in layers.items():
            count = counts[species][municipality.GetFID()]
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetGeometry(geometry)
            feature.SetField("pro_com_t", municipality["PRO_COM_T"])
            feature.SetField("comune", municipality["COMUNE"])
            feature.SetField("cod_reg", municipality["COD_REG"])
            feature.SetField("cod_prov", municipality["COD_PROV"])
            feature.SetField("area_km2", area_km2)
            feature.SetField("point_count", count)
            feature.SetField("density_km2", count / area_km2)
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

    print(", ".join(f"{species}: {totals[species]} punti" for species in SPECIES))
    print(f"Punti su confini comunali con assegnazione deterministica: {ambiguous}")
    print(f"Geometrie comunali riparate nell'output: {repaired}")


if __name__ == "__main__":
    main()
