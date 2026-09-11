#!/usr/bin/env python3
"""Update the QGIS project with all available source and derived layers."""
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)

ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = ROOT / "qgis/allevamenti.qgs"
GPKG = ROOT / "data/processed/allevamenti.gpkg"

GROUPS = {
    "Presenze e attribuzioni": [
        ("megafarms_italy_points_valid", "Allevamenti intensivi (presenze)", True),
        ("megafarms_points_clc_1990_2018", "Presenze con CLC 1990–2018", False),
        ("megafarms_points_protected_areas", "Presenze e prossimità alle aree protette", False),
    ],
    "Densità — griglia 10 km": [
        ("megafarms_grid_10km_pigs", "Densità suini — griglia 10 km", False),
        ("megafarms_grid_10km_poultry", "Densità pollame — griglia 10 km", False),
    ],
    "Densità — comuni 2025": [
        ("megafarms_municipality_2025_pigs", "Densità suini — comuni 2025", False),
        ("megafarms_municipality_2025_poultry", "Densità pollame — comuni 2025", False),
    ],
    "Densità kernel — 20 km": [
        ("megafarms_kde_20km_pigs", "KDE suini — bandwidth 20 km", False),
        ("megafarms_kde_20km_poultry", "KDE pollame — bandwidth 20 km", False),
    ],
    "Aree protette e idrografia": [
        ("mase_natura2000_2025", "Natura 2000 — 2025", False),
        ("mase_euap_2010", "EUAP — VI elenco 2010", False),
        ("ispra_reticolo_idrografico", "Reticolo idrografico ISPRA 1:250.000", False),
    ],
    "Copertura del suolo": [
        ("copernicus_clc_2018", "CORINE Land Cover 2018", False),
        ("copernicus_clc_1990", "CORINE Land Cover 1990", False),
    ],
    "Confini amministrativi ISTAT 2025": [
        ("istat_comuni_2025", "Comuni ISTAT 2025", False),
        ("istat_province_2025", "Province ISTAT 2025", False),
        ("istat_regioni_2025", "Regioni ISTAT 2025", True),
    ],
    "Tabelle di sintesi": [
        ("megafarms_clc_transitions", "Transizioni CLC 1990–2018", False),
        ("megafarms_protected_areas_summary", "Sintesi prossimità aree protette", False),
    ],
}


def add_layer(project, group, source_name, title, visible):
    raster = source_name.startswith("megafarms_kde_")
    if raster:
        source = ROOT / f"data/derived/rasters/{source_name}.tif"
        layer = QgsRasterLayer(str(source), title, "gdal")
        style = ROOT / f"styles/rasters/{source_name}.qml"
    else:
        layer = QgsVectorLayer(f"{GPKG}|layername={source_name}", title, "ogr")
        style_name = "megafarms_italy_points" if source_name == "megafarms_italy_points_valid" else source_name
        style = ROOT / f"styles/vectors/{style_name}.qml"

    if not layer.isValid():
        raise RuntimeError(f"Layer non valido: {source_name}")
    if style.exists():
        message, ok = layer.loadNamedStyle(str(style))
        if not ok:
            raise RuntimeError(f"Stile non valido {style}: {message}")
    elif layer.isSpatial():
        raise RuntimeError(f"Stile mancante: {style}")

    layer.setId(source_name)
    project.addMapLayer(layer, False)
    node = group.addLayer(layer)
    node.setItemVisibilityChecked(visible)


def prune_duplicate_project_styles():
    attachments = PROJECT_FILE.with_name(f"{PROJECT_FILE.stem}_attachments.zip")
    project_xml = PROJECT_FILE.read_text()
    match = re.search(r'projectStyleId="attachment:///([^"/]+)"', project_xml)
    if not attachments.exists() or not match:
        return
    keep = match.group(1)
    with ZipFile(attachments) as archive:
        content = {entry.filename: archive.read(entry) for entry in archive.infolist()}
    if keep not in content:
        return
    content = {name: data for name, data in content.items() if name == keep or not name.endswith("_styles.db")}
    PROJECT_FILE.write_text(re.sub(r'iccProfileId="attachment:///qt_temp-[^"]*"', 'iccProfileId=""', project_xml))
    temporary = attachments.with_suffix(".tmp")
    with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
        for name, data in content.items():
            archive.writestr(name, data)
    temporary.replace(attachments)


def main():
    app = QgsApplication([], False)
    app.initQgis()
    project = QgsProject.instance()
    if PROJECT_FILE.exists() and not project.read(str(PROJECT_FILE)):
        raise RuntimeError(f"Impossibile leggere {PROJECT_FILE}")

    project.setFileName(str(PROJECT_FILE))
    project.setTitle("Allevamenti intensivi in Italia")
    project.setCrs(QgsCoordinateReferenceSystem("EPSG:3035"))
    project.writeEntry("Paths", "/Absolute", False)
    project.layerTreeRoot().clear()
    project.removeAllMapLayers()

    expected = 0
    for group_name, specs in GROUPS.items():
        group = project.layerTreeRoot().addGroup(group_name)
        group.setExpanded(False)
        for spec in specs:
            add_layer(project, group, *spec)
            expected += 1

    if len(project.mapLayers()) != expected or not project.write():
        raise RuntimeError(f"Impossibile scrivere {PROJECT_FILE}")
    app.exitQgis()
    prune_duplicate_project_styles()
    print(f"Aggiornato {PROJECT_FILE}: {expected} layer in {len(GROUPS)} gruppi")


if __name__ == "__main__":
    main()
