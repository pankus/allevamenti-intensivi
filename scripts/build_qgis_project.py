#!/usr/bin/env python3
"""Update the QGIS project with all available source and derived layers."""
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

from qgis.PyQt.QtGui import QColor, QFont
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutItemPage,
    QgsLayoutItemScaleBar,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsPrintLayout,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
    QgsTextFormat,
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


def place(layout, item, x, y, width, height):
    layout.addLayoutItem(item)
    unit = Qgis.LayoutUnit.Millimeters
    item.attemptMove(QgsLayoutPoint(x, y, unit))
    item.attemptResize(QgsLayoutSize(width, height, unit))
    return item


def add_label(layout, text, box, size, bold=False):
    label = place(layout, QgsLayoutItemLabel(layout), *box)
    label.setText(text)
    font = QFont("DejaVu Sans")
    font.setBold(bold)
    text_format = QgsTextFormat()
    text_format.setFont(font)
    text_format.setSize(size)
    label.setTextFormat(text_format)
    return label


def add_legend(layout, map_item, box, layers):
    legend = place(layout, QgsLayoutItemLegend(layout), *box)
    legend.setTitle("Legenda")
    legend.setLinkedMap(map_item)
    legend.setSyncMode(Qgis.LegendSyncMode.Manual)
    root = legend.model().rootGroup()
    root.clear()
    for layer, title in layers:
        root.addLayer(layer).setName(title)
    legend.adjustBoxSize()


def add_scale(layout, map_item, box, segment_km):
    scale = place(layout, QgsLayoutItemScaleBar(layout), *box)
    scale.setStyle("Single Box")
    scale.setLinkedMap(map_item)
    scale.setUnits(Qgis.DistanceUnit.Kilometers)
    scale.setNumberOfSegments(4 if segment_km == 25 else 3)
    scale.setUnitsPerSegment(segment_km)
    scale.setUnitLabel("km")
    scale.update()


def add_layout(project, name, title, orientation, extent, layer_ids, legend_entries, segment_km, footer):
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(name)
    layout.pageCollection().page(0).setPageSize("A4", orientation)
    portrait = orientation == QgsLayoutItemPage.Orientation.Portrait
    add_label(layout, title, (12 if portrait else 10, 7, 186 if portrait else 277, 16), 20 if portrait else 18, True)
    map_box = (12, 29, 143, 235) if portrait else (10, 27, 215, 151)
    map_item = place(layout, QgsLayoutItemMap(layout), *map_box)
    map_item.setId("map")
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeColor(QColor("#555555"))
    map_item.setLayers([project.mapLayer(layer_id) for layer_id in layer_ids])
    map_item.setExtent(extent)
    add_legend(
        layout,
        map_item,
        (160, 31, 38, 90) if portrait else (230, 29, 57, 110),
        [(project.mapLayer(layer_id), label) for layer_id, label in legend_entries],
    )
    add_scale(layout, map_item, (17, 249, 65, 10) if portrait else (16, 163, 70, 10), segment_km)
    add_label(layout, footer, (12, 269, 186, 17) if portrait else (10, 184, 277, 15), 7)
    project.layoutManager().addLayout(layout)


def build_layouts(project):
    names = {
        "01 — Distribuzione nazionale",
        "02 — Hotspot suini — Pianura Padana centrale",
        "03 — Hotspot pollame — Pianura Padana centro-orientale",
    }
    manager = project.layoutManager()
    for layout in list(manager.printLayouts()):
        if layout.name() in names:
            manager.removeLayout(layout)

    national_extent = project.mapLayer("istat_regioni_2025").extent()
    national_extent.scale(1.06)
    add_layout(
        project,
        "01 — Distribuzione nazionale",
        "Allevamenti intensivi in Italia",
        QgsLayoutItemPage.Orientation.Portrait,
        national_extent,
        ["megafarms_italy_points_valid", "istat_regioni_2025"],
        [("megafarms_italy_points_valid", "Presenze pubblicate"), ("istat_regioni_2025", "Confini regionali")],
        100,
        "Fonti: Megafarm Europe; ISTAT 2025. Elaborazione: 11 settembre 2026.\n"
        "I punti indicano presenze pubblicate, non capi, emissioni o produzione.",
    )

    common_layers = ["megafarms_italy_points_valid", "istat_province_2025", "ispra_reticolo_idrografico"]
    common_legend = [
        ("megafarms_italy_points_valid", "Presenze pubblicate"),
        ("istat_province_2025", "Confini provinciali"),
        ("ispra_reticolo_idrografico", "Reticolo ISPRA"),
    ]
    footer = (
        "Fonti: Megafarm Europe; ISTAT 2025; ISPRA. Elaborazione: 11 settembre 2026.\n"
        "KDE quartico: bandwidth 20 km, cella 2 km. I punti indicano presenze, non capi o emissioni."
    )
    for name, title, raster, extent in [
        (
            "02 — Hotspot suini — Pianura Padana centrale",
            "Hotspot suini · Pianura Padana centrale",
            "megafarms_kde_20km_pigs",
            QgsRectangle(4230000, 2370000, 4450000, 2525000),
        ),
        (
            "03 — Hotspot pollame — Pianura Padana centro-orientale",
            "Hotspot pollame · Pianura Padana centro-orientale",
            "megafarms_kde_20km_poultry",
            QgsRectangle(4310000, 2330000, 4590000, 2510000),
        ),
    ]:
        add_layout(
            project,
            name,
            title,
            QgsLayoutItemPage.Orientation.Landscape,
            extent,
            [*common_layers, raster],
            [common_legend[0], (raster, "Densità KDE (punti/km²)"), *common_legend[1:]],
            25,
            footer,
        )


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

    build_layouts(project)
    if len(project.mapLayers()) != expected or not project.write():
        raise RuntimeError(f"Impossibile scrivere {PROJECT_FILE}")
    app.exitQgis()
    prune_duplicate_project_styles()
    print(f"Aggiornato {PROJECT_FILE}: {expected} layer in {len(GROUPS)} gruppi")


if __name__ == "__main__":
    main()
