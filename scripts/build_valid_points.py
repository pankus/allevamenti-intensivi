#!/usr/bin/env python3
"""Create the analysis layer, excluding the single [0,0] source record."""
from pathlib import Path
from subprocess import run

ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "data/processed/allevamenti.gpkg"

run([
    "ogr2ogr", "-f", "GPKG", "-update", "-overwrite", str(GPKG), str(GPKG),
    "-dialect", "SQLITE", "-sql",
    "SELECT * FROM megafarms_italy_points WHERE ST_Y(geom) >= 0",
    "-nln", "megafarms_italy_points_valid",
], check=True)
