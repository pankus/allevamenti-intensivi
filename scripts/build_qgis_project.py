"""Build the QGIS project and its point-layer style."""
from pathlib import Path
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsCoordinateReferenceSystem,
    QgsMarkerSymbol,
    QgsProject,
    QgsRendererCategory,
    QgsVectorLayer,
)

ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "data/processed/allevamenti.gpkg"
STYLE = ROOT / "styles/vectors/megafarms_italy_points.qml"
PROJECT_FILE = ROOT / "qgis/allevamenti.qgz"


def symbol(color):
    return QgsMarkerSymbol.createSimple({
        "name": "circle", "color": color, "outline_color": "#ffffff",
        "outline_width": "0.35", "size": "2.4",
    })


def build():
    layer = QgsVectorLayer(
        f"{GPKG}|layername=megafarms_italy_points_valid", "Allevamenti intensivi (Italia)", "ogr"
    )
    if not layer.isValid():
        raise RuntimeError(f"Cannot open {GPKG}")

    renderer = QgsCategorizedSymbolRenderer("Type of Animal", [
        QgsRendererCategory("Pigs", symbol("#b2182b"), "Suini"),
        QgsRendererCategory("Poultry", symbol("#2166ac"), "Pollame"),
    ])
    layer.setRenderer(renderer)
    STYLE.parent.mkdir(parents=True, exist_ok=True)
    ok, message = layer.saveNamedStyle(str(STYLE))
    if not ok:
        raise RuntimeError(message)

    project = QgsProject.instance()
    project.clear()
    project.setCrs(QgsCoordinateReferenceSystem("EPSG:3035"))
    project.writeEntry("Paths", "/Absolute", False)
    project.addMapLayer(layer)
    PROJECT_FILE.parent.mkdir(parents=True, exist_ok=True)
    project.setFileName(str(PROJECT_FILE))
    if not project.write():
        raise RuntimeError(f"Cannot write {PROJECT_FILE}")
    print(f"Created {PROJECT_FILE}\nCreated {STYLE}")
    QApplication.quit()


QTimer.singleShot(0, build)
