#!/usr/bin/env python3
"""Compute exploratory distances from megafarm points to the ISPRA 1:250,000 network."""
import csv
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "data/processed/allevamenti.gpkg"
DETAIL = ROOT / "data/derived/vectors/megafarms_water_proximity_ispra.csv"
SUMMARY = ROOT / "data/derived/vectors/megafarms_water_proximity_ispra_summary.csv"
THRESHOLDS = (250, 500, 1000, 5000)
SQL = '''
SELECT p.fid+0 AS source_fid,
       p."Type of Animal" AS animal,
       MIN(ST_Distance(p.geom,r.geom)) AS distance_m
FROM megafarms_italy_points_valid p
JOIN rtree_ispra_reticolo_idrografico_geom x
  ON x.minx <= ST_X(p.geom)+10000 AND x.maxx >= ST_X(p.geom)-10000
 AND x.miny <= ST_Y(p.geom)+10000 AND x.maxy >= ST_Y(p.geom)-10000
JOIN ispra_reticolo_idrografico r ON r.fid=x.id
GROUP BY p.fid, animal
'''


def main():
    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory) / "distances.csv"
        subprocess.run([
            "ogr2ogr", "-f", "CSV", str(temporary), str(GPKG),
            "-dialect", "SQLite", "-sql", SQL,
        ], check=True)
        with temporary.open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))

    assert len(rows) == 2145
    with DETAIL.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("source_fid", "animal", "distance_m"))
        writer.writeheader()
        for row in rows:
            row["distance_m"] = f'{float(row["distance_m"]):.3f}'
            writer.writerow(row)

    with SUMMARY.open("w", newline="", encoding="utf-8") as stream:
        fields = ["animal", "total_points", "median_m"]
        for threshold in THRESHOLDS:
            fields += [f"within_{threshold}m", f"within_{threshold}m_percent"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for animal in ("Pigs", "Poultry"):
            distances = [float(row["distance_m"]) for row in rows if row["animal"] == animal]
            result = {"animal": animal, "total_points": len(distances), "median_m": f"{statistics.median(distances):.1f}"}
            for threshold in THRESHOLDS:
                count = sum(distance <= threshold for distance in distances)
                result[f"within_{threshold}m"] = count
                result[f"within_{threshold}m_percent"] = f"{count / len(distances) * 100:.2f}"
            writer.writerow(result)

    print(f"Creati {DETAIL} e {SUMMARY}")


if __name__ == "__main__":
    main()
