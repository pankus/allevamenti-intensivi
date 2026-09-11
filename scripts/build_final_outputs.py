#!/usr/bin/env python3
"""Build presentation tables and export the three QGIS layouts as PNG."""
import csv
import sqlite3
from pathlib import Path

from qgis.core import QgsApplication, QgsLayoutExporter, QgsProject

ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "data/processed/allevamenti.gpkg"
PROJECT = ROOT / "qgis/allevamenti.qgs"
TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
SPECIES = {"Pigs": "pigs", "Poultry": "poultry"}
LAYOUTS = {
    "01 — Distribuzione nazionale": "figure_01_national_distribution.png",
    "02 — Hotspot suini — Pianura Padana centrale": "figure_02_pigs_hotspot.png",
    "03 — Hotspot pollame — Pianura Padana centro-orientale": "figure_03_poultry_hotspot.png",
}


def write_csv(name, header, rows):
    with (TABLES / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def build_tables(project):
    database = sqlite3.connect(GPKG)
    summary = []
    top_municipalities = []
    clc_context = []
    for animal, key in SPECIES.items():
        total = database.execute(
            'SELECT count(*) FROM megafarms_italy_points_valid WHERE "Type of Animal"=?', (animal,)
        ).fetchone()[0]
        grid = database.execute(
            f"SELECT count(*) FILTER (WHERE point_count>0), max(point_count), max(density_km2) "
            f"FROM megafarms_grid_10km_{key}"
        ).fetchone()
        municipalities = database.execute(
            f"SELECT count(*) FILTER (WHERE point_count>0), max(point_count) "
            f"FROM megafarms_municipality_2025_{key}"
        ).fetchone()
        changed = database.execute(
            'SELECT sum(clc_changed) FROM megafarms_points_clc_1990_2018 WHERE "Type of Animal"=?',
            (animal,),
        ).fetchone()[0]
        raster = project.mapLayer(f"megafarms_kde_20km_{key}")
        maximum = raster.dataProvider().bandStatistics(1).maximumValue
        summary.append((
            animal, total, *grid[:2], f"{grid[2]:.2f}", *municipalities,
            changed, f"{changed / total * 100:.1f}", f"{maximum:.4f}",
        ))

        rows = database.execute(
            f"SELECT pro_com_t, comune, point_count, density_km2 "
            f"FROM megafarms_municipality_2025_{key} "
            f"WHERE point_count>0 ORDER BY point_count DESC, pro_com_t LIMIT 10"
        )
        top_municipalities.extend(
            (animal, rank, code, municipality, count, f"{density:.4f}")
            for rank, (code, municipality, count, density) in enumerate(rows, 1)
        )

        rows = database.execute(
            'SELECT clc1_1990, clc1_2018, count(*) FROM megafarms_points_clc_1990_2018 '
            'WHERE "Type of Animal"=? GROUP BY clc1_1990, clc1_2018 '
            'ORDER BY count(*) DESC, clc1_1990, clc1_2018',
            (animal,),
        )
        clc_context.extend(
            (animal, old, new, count, f"{count / total * 100:.2f}") for old, new, count in rows
        )

    write_csv(
        "table_01_summary.csv",
        ("animal", "total_points", "occupied_grid_cells", "max_points_10km_cell",
         "max_grid_density_km2", "occupied_municipalities", "max_points_municipality",
         "clc_changed_count", "clc_changed_percent", "kde_max_points_km2"),
        summary,
    )
    write_csv(
        "table_02_protected_areas.csv",
        ("animal", "protected_dataset", "total_points", "inside_count", "inside_percent",
         "within_1km", "within_1km_percent", "within_5km", "within_5km_percent", "median_m"),
        (
            (animal, dataset, total, inside, f"{inside / total * 100:.2f}", near1,
             f"{near1 / total * 100:.2f}", near5, f"{near5 / total * 100:.2f}", f"{median:.1f}")
            for animal, dataset, total, inside, near1, near5, median in database.execute(
                "SELECT animal, protected_dataset, total_points, inside_count, within_1km, "
                "within_5km, median_m FROM megafarms_protected_areas_summary ORDER BY animal, protected_dataset"
            )
        ),
    )
    write_csv(
        "table_03_top_municipalities.csv",
        ("animal", "rank_by_point_count", "municipality_code", "municipality",
         "point_count", "density_km2"),
        top_municipalities,
    )
    write_csv(
        "table_04_clc_level1_transitions.csv",
        ("animal", "clc_level1_1990", "clc_level1_2018", "point_count", "share_percent"),
        clc_context,
    )
    database.close()


def export_figures(project):
    layouts = {layout.name(): layout for layout in project.layoutManager().printLayouts()}
    for name, filename in LAYOUTS.items():
        layout = layouts.get(name)
        if layout is None:
            raise RuntimeError(f"Layout mancante: {name}")
        output = FIGURES / filename
        image = QgsLayoutExporter(layout).renderPageToImage(0, dpi=200)
        if image.isNull() or not image.save(str(output), "PNG"):
            raise RuntimeError(f"Esportazione fallita: {name}")


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    app = QgsApplication([], False)
    app.initQgis()
    project = QgsProject.instance()
    if not project.read(str(PROJECT)):
        raise RuntimeError(f"Impossibile leggere {PROJECT}")
    build_tables(project)
    export_figures(project)
    print(f"Create 4 tabelle in {TABLES} e 3 figure in {FIGURES}")
    app.exitQgis()


if __name__ == "__main__":
    main()
