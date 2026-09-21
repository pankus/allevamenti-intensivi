#!/usr/bin/env python3
"""Generate the teaching slides from the published summary tables."""
import base64
import csv
import html
import shutil
import sqlite3
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
SLIDES = ROOT / "outputs/slides"
W, H = 1920, 1080
BG = "#F4F0E6"
INK = "#173F35"
MUTED = "#62756D"
RULE = "#CED5CC"
STABLE = "#CBD7C8"
CHANGE = "#D65F32"
PIGS = "#9A583D"
POULTRY = "#356D78"
FONT = "Noto Sans, Arial, sans-serif"


def text(x, y, value, size, *, fill=INK, weight=400, anchor="start", spacing=0):
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
        f'letter-spacing="{spacing}">{html.escape(str(value))}</text>'
    )


def multiline(x, y, lines, size, *, fill=INK, weight=400, leading=1.35, anchor="start"):
    return "".join(
        text(x, y + i * size * leading, line, size, fill=fill, weight=weight, anchor=anchor)
        for i, line in enumerate(lines)
    )


def embedded_png(path, x, y, width, height, *, fit="xMidYMid meet"):
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<image x="{x}" y="{y}" width="{width}" height="{height}" '
        f'preserveAspectRatio="{fit}" href="data:image/png;base64,{payload}"/>'
    )


def cropped_png(path, x, y, width, height, viewbox, image_size):
    vx, vy, vw, vh = viewbox
    iw, ih = image_size
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<svg x="{x}" y="{y}" width="{width}" height="{height}" '
        f'viewBox="{vx} {vy} {vw} {vh}" preserveAspectRatio="xMidYMid meet">'
        f'<image x="0" y="0" width="{iw}" height="{ih}" '
        f'href="data:image/png;base64,{payload}"/></svg>'
    )


def read_rows(name):
    with (TABLES / name).open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def pct(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",") + "%"


def start(label, title_lines, subtitle, desc):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f"<title>{html.escape(title_lines[0])}</title>",
        f"<desc>{html.escape(desc)}</desc>",
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        text(110, 88, label, 22, fill=CHANGE, weight=700, spacing=2.2),
    ]
    y = 168
    for line in title_lines:
        parts.append(text(110, y, line, 56, weight=700))
        y += 64
    parts.extend([
        text(110, 292, subtitle, 24, fill=MUTED),
        f'<line x1="110" y1="338" x2="1810" y2="338" stroke="{RULE}" stroke-width="2"/>',
    ])
    return parts


def sidebar(parts, sources, technique=None):
    x = 1515
    parts.append(f'<line x1="1470" y1="382" x2="1470" y2="930" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(x, 405, "FONTI DATI", 17, fill=CHANGE, weight=700, spacing=1.4))
    y = 445
    for name, description in sources:
        parts.append(text(x, y, name, 19, weight=700))
        y += 28
        for line in description:
            parts.append(text(x, y, line, 16, fill=MUTED))
            y += 23
        y += 18
    if technique:
        y = max(y + 8, 690)
        parts.append(f'<line x1="{x}" y1="{y - 26}" x2="1810" y2="{y - 26}" stroke="{RULE}"/>')
        parts.append(text(x, y, "TECNICA", 17, fill=CHANGE, weight=700, spacing=1.4))
        y += 34
        parts.append(text(x, y, technique[0], 19, weight=700))
        y += 29
        for line in technique[1]:
            parts.append(text(x, y, line, 16, fill=MUTED))
            y += 23


def finish(parts, number, source_line="Elaborazione propria"):
    parts.extend([
        f'<line x1="110" y1="984" x2="1810" y2="984" stroke="{RULE}"/>',
        text(110, 1024, source_line, 16, fill=MUTED),
        text(1810, 1024, number, 16, fill=MUTED, weight=700, anchor="end"),
        "</svg>",
    ])
    return "\n".join(parts)


def table_block(parts, headers, rows, widths, *, x=110, y=430, row_h=62, font_size=18):
    total = sum(widths)
    parts.append(f'<rect x="{x}" y="{y}" width="{total}" height="{row_h}" rx="7" fill="{INK}"/>')
    cursor = x
    for header, width in zip(headers, widths):
        parts.append(text(cursor + 15, y + 39, header, 16, fill=BG, weight=700))
        cursor += width
    for i, row in enumerate(rows):
        row_y = y + row_h * (i + 1)
        fill = "#E7E6DC" if i % 2 == 0 else "#EEEADF"
        parts.append(f'<rect x="{x}" y="{row_y}" width="{total}" height="{row_h}" fill="{fill}"/>')
        cursor = x
        for value, width in zip(row, widths):
            parts.append(text(cursor + 15, row_y + 39, value, font_size, weight=600 if cursor == x else 400))
            cursor += width


def data_slide(number, label, title, subtitle, headers, rows, widths, question, source):
    parts = start(label, (title,), subtitle, f"Estratto didattico di {label.lower()}")
    table_block(parts, headers, rows, widths)
    parts.extend([
        text(110, 875, "DAL DATO ALLA DOMANDA", 17, fill=CHANGE, weight=700, spacing=1.4),
        text(390, 875, question, 25, weight=700),
    ])
    return finish(parts, number, source)


def slide_01_clc_explainer():
    parts = start(
        "IL METODO  ·  CORINE LAND COVER",
        ("Una lingua comune per descrivere", "la copertura del suolo europeo"),
        "Copernicus assegna ogni area a una classe gerarchica confrontabile nel tempo",
        "Spiegazione della classificazione gerarchica CLC.",
    )
    parts.extend([
        text(110, 390, "DAL GENERALE AL DETTAGLIO", 18, fill=MUTED, weight=700, spacing=1.4),
        f'<rect x="110" y="420" width="560" height="88" rx="8" fill="{STABLE}"/>',
        text(138, 457, "LIVELLO 1", 17, fill=MUTED, weight=700), text(305, 478, "2  Superfici agricole", 29, weight=700),
        f'<rect x="165" y="526" width="505" height="88" rx="8" fill="#D8D7B5"/>',
        text(193, 563, "LIVELLO 2", 17, fill=MUTED, weight=700), text(360, 584, "21  Seminativi", 29, weight=700),
        f'<rect x="220" y="632" width="450" height="88" rx="8" fill="#E4D69E"/>',
        text(248, 660, "LIVELLO 3", 17, fill=MUTED, weight=700), text(248, 700, "211  Seminativi in aree non irrigue", 22, weight=700),
        text(110, 770, "CLC descrive il contesto territoriale,", 23, weight=600),
        text(110, 804, "non il singolo edificio o la proprietà del suolo.", 22, fill=MUTED),
        f'<line x1="760" y1="382" x2="760" y2="830" stroke="{RULE}" stroke-width="2"/>',
        text(820, 390, "ESEMPIO REALE · PUNTO SUINO 105", 18, fill=CHANGE, weight=700, spacing=1.4),
        f'<rect x="820" y="470" width="380" height="250" rx="10" fill="#E4D69E"/>',
        f'<path d="M820 560 C900 510 980 600 1060 540 S1160 520 1200 500 V720 H820 Z" fill="#D2C47F"/>',
        f'<circle cx="1010" cy="590" r="15" fill="{INK}"/><circle cx="1010" cy="590" r="25" fill="none" stroke="{BG}" stroke-width="5"/>',
        text(850, 512, "1990", 24, fill=MUTED, weight=700), text(850, 684, "211", 45, weight=800),
        text(850, 710, "seminativi in aree non irrigue", 18, weight=600),
        text(1260, 602, "→", 54, fill=CHANGE, weight=700, anchor="middle"),
        f'<rect x="1320" y="470" width="380" height="250" rx="10" fill="#D7B3A6"/>',
        f'<path d="M1320 560 L1435 520 L1510 570 L1600 505 L1700 535 V720 H1320 Z" fill="#C88670"/>',
        f'<circle cx="1510" cy="590" r="15" fill="{INK}"/><circle cx="1510" cy="590" r="25" fill="none" stroke="{BG}" stroke-width="5"/>',
        text(1350, 512, "2018", 24, fill=MUTED, weight=700), text(1350, 684, "121", 45, fill=CHANGE, weight=800),
        text(1350, 710, "aree industriali o commerciali", 18, weight=600),
        text(820, 770, "Il punto resta fermo. Cambia la classe del poligono CLC.", 23, weight=700),
        text(820, 808, "La transizione 211 → 121 ricorre in 23 localizzazioni.", 21, fill=MUTED),
        text(110, 920, "PERCHÉ È UTILE", 17, fill=CHANGE, weight=700, spacing=1.4),
        text(320, 920, "Rende confrontabili luoghi e anni diversi con le stesse categorie.", 24, weight=700),
    ])
    return finish(parts, 1, "Fonte: Copernicus CORINE Land Cover 1990 e 2018, V2020_20u1 · schema non cartografico")


def slide_02_clc_data(rows):
    sample = [
        ("Suini", "Superfici agricole", "Superfici agricole", "764", "84,61%"),
        ("Suini", "Superfici agricole", "Superfici artificiali", "28", "3,10%"),
        ("Pollame", "Superfici agricole", "Superfici agricole", "1.041", "83,82%"),
        ("Pollame", "Superfici agricole", "Superfici artificiali", "48", "3,86%"),
    ]
    return data_slide(2, "DATI DI PARTENZA  ·  TABELLA 04", "Le transizioni CLC diventano una tabella", "Una riga per specie e coppia di macroclassi 1990 → 2018", ("Specie", "CLC 1990", "CLC 2018", "Punti", "Quota"), sample, (150, 360, 360, 150, 150), "Quanto cambia il risultato usando classi più o meno dettagliate?", "Dati: Megafarm Europe + Copernicus CLC; elaborazione propria")


def slide_03_clc_scale(summary, transitions):
    level1_changed = {}
    for animal in ("Pigs", "Poultry"):
        stable = sum(int(r["point_count"]) for r in transitions if r["animal"] == animal and r["clc_level1_1990"] == r["clc_level1_2018"])
        total = int(summary[animal]["total_points"])
        level1_changed[animal] = (total - stable) / total * 100
    parts = start("RISULTATO  ·  SCALA DELLA CLASSIFICAZIONE", ("Più dettaglio rende visibili", "più cambiamenti"), "La percentuale dipende dal livello gerarchico scelto", "Confronto delle variazioni CLC al primo e al terzo livello.")
    for i, (animal, label, color) in enumerate((("Pigs", "SUINI", PIGS), ("Poultry", "POLLAME", POULTRY))):
        y = 460 + i * 220
        values = (level1_changed[animal], float(summary[animal]["clc_changed_percent"]))
        parts.extend([text(110, y, label, 25, weight=700), text(310, y - 55, "Macroclasse", 18, fill=MUTED), text(310, y + 60, "Classe dettagliata", 18, fill=MUTED)])
        for j, value in enumerate(values):
            by = y - 78 + j * 115
            width = value / 16 * 900
            parts.extend([f'<rect x="520" y="{by}" width="900" height="48" rx="6" fill="#E1E2D9"/>', f'<rect x="520" y="{by}" width="{width}" height="48" rx="6" fill="{color}"/>', text(540 + width, by + 34, pct(value), 23, fill=INK, weight=800)])
    sidebar(parts, [("Megafarm Europe", ("Localizzazioni attuali", "distinte per specie.")), ("Copernicus CLC", ("Copertura del suolo", "1990 e 2018."))], ("Gerarchia CLC", ("Il livello 1 raggruppa grandi", "famiglie; il livello 3 distingue", "classi territoriali specifiche.")))
    return finish(parts, 3, "Elaborazione: table_01_summary.csv + table_04_clc_level1_transitions.csv")


def slide_04_clc_summary(summary, transitions):
    totals = sum(int(summary[a]["total_points"]) for a in summary)
    stable_agri = sum(int(r["point_count"]) for r in transitions if r["clc_level1_1990"] == r["clc_level1_2018"] == "Superfici agricole")
    agri_art = sum(int(r["point_count"]) for r in transitions if r["clc_level1_1990"] == "Superfici agricole" and r["clc_level1_2018"] == "Superfici artificiali")
    parts = start("RISULTATO  ·  TRANSIZIONI CLC", ("Il contesto cambia più spesso", "nelle localizzazioni avicole"), "Classe CORINE di terzo livello confrontata nello stesso punto", "Sintesi delle transizioni CLC 1990–2018.")
    bar_x, bar_w = 390, 760
    for i, (animal, label) in enumerate((("Pigs", "SUINI"), ("Poultry", "POLLAME"))):
        y = 455 + i * 150
        changed = float(summary[animal]["clc_changed_percent"])
        stable = 100 - changed
        stable_w = bar_w * stable / 100
        parts.extend([text(110, y, label, 25, weight=700), text(110, y + 35, summary[animal]["total_points"] + " punti", 19, fill=MUTED), f'<rect x="{bar_x}" y="{y - 35}" width="{bar_w}" height="58" rx="8" fill="{STABLE}"/>', f'<rect x="{bar_x + stable_w}" y="{y - 35}" width="{bar_w - stable_w}" height="58" fill="{CHANGE}"/>', text(bar_x + 20, y + 4, pct(stable) + " invariata", 22, weight=700), text(1395, y + 2, pct(changed), 38, fill=CHANGE, weight=800, anchor="end")])
    parts.extend([f'<line x1="110" y1="730" x2="1400" y2="730" stroke="{RULE}"/>', text(110, 790, pct(stable_agri / totals * 100), 48, weight=800), text(110, 830, "agricolo in entrambi gli anni", 22, fill=MUTED), text(570, 790, pct(agri_art / totals * 100), 48, fill=CHANGE, weight=800), text(570, 830, "da agricolo ad artificiale", 22, fill=MUTED), text(110, 900, "Le localizzazioni sono attuali: il confronto non dimostra presenza storica o causalità.", 21, weight=600)])
    sidebar(parts, [("Megafarm Europe", ("Punti di presenza attuali,", "non numero di capi.")), ("Copernicus CLC", ("Poligoni europei di", "copertura del suolo."))])
    return finish(parts, 4, "Fonti: Megafarm Europe; Copernicus CORINE Land Cover V2020_20u1")


def slide_05_summary_data(summary):
    rows = []
    for animal, label in (("Pigs", "Suini"), ("Poultry", "Pollame")):
        r = summary[animal]
        rows.append((label, r["total_points"], r["occupied_grid_cells"], r["occupied_municipalities"], r["clc_changed_percent"] + "%", r["kde_max_points_km2"]))
    return data_slide(5, "DATI DI PARTENZA  ·  TABELLA 01", "Due righe riassumono il dataset", "Indicatori territoriali separati per specie", ("Specie", "Punti", "Celle", "Comuni", "CLC cambia", "Max KDE"), rows, (180, 160, 180, 190, 210, 190), "Le due specie hanno la stessa diffusione e concentrazione?", "Dati: Megafarm Europe, ISTAT, Copernicus CLC; elaborazione propria")


def slide_06_overview(summary):
    parts = start("RISULTATO  ·  DIMENSIONE E DIFFUSIONE", ("Il pollame è più numeroso", "e territorialmente più diffuso"), "Punti, celle da 10 km e comuni occupati", "Confronto della diffusione delle localizzazioni per specie.")
    metrics = (("LOCALIZZAZIONI", "total_points", 1300), ("CELLE DA 10 KM", "occupied_grid_cells", 450), ("COMUNI", "occupied_municipalities", 650))
    for m, (label, field, maximum) in enumerate(metrics):
        y = 420 + m * 165
        parts.append(text(110, y, label, 18, fill=MUTED, weight=700, spacing=1.2))
        for j, (animal, name, color) in enumerate((("Pigs", "Suini", PIGS), ("Poultry", "Pollame", POULTRY))):
            value = int(summary[animal][field])
            by = y + 28 + j * 52
            parts.extend([text(110, by + 25, name, 18, weight=600), f'<rect x="260" y="{by}" width="{value / maximum * 920}" height="34" rx="5" fill="{color}"/>', text(1210, by + 26, f"{value:,}".replace(",", "."), 22, weight=800, anchor="end")])
    sidebar(parts, [("Megafarm Europe", ("Punti geolocalizzati e", "tipo animale.")), ("ISTAT 2025", ("Confini amministrativi", "ufficiali dei comuni.")), ("Elaborazione propria", ("Griglia regolare", "10 × 10 km."))])
    return finish(parts, 6, "Punti = localizzazioni pubblicate; non capi, produzione o emissioni")


def slide_07_lenses(summary):
    parts = start("METODO  ·  TRE LENTI SPAZIALI", ("La concentrazione cambia", "con il metodo di osservazione"), "I valori rispondono a domande diverse e non condividono lo stesso asse", "Confronto tra griglia, comuni e densità kernel.")
    panels = (
        ("GRIGLIA 10 × 10 KM", "Massimo in una cella", "27", "26", "Conta i punti entro quadrati uguali."),
        ("COMUNI", "Massimo in un comune", "13", "28", "Conta entro confini amministrativi."),
        ("KERNEL DENSITY", "Massimo punti/km²", "0,137", "0,173", "Stima una superficie continua."),
    )
    for i, (name, desc, pig, poultry, note) in enumerate(panels):
        x = 110 + i * 440
        parts.extend([text(x, 420, name, 17, fill=CHANGE, weight=700, spacing=1), text(x, 458, desc, 18, fill=MUTED), text(x, 535, pig, 48, fill=PIGS, weight=800), text(x, 567, "suini", 18, fill=MUTED), text(x + 190, 535, poultry, 48, fill=POULTRY, weight=800), text(x + 190, 567, "pollame", 18, fill=MUTED), f'<line x1="{x}" y1="610" x2="{x + 370}" y2="610" stroke="{RULE}"/>', multiline(x, 650, (note,), 18, fill=MUTED)])
    parts.extend([text(110, 815, "PERCHÉ USARLE INSIEME", 17, fill=CHANGE, weight=700, spacing=1.3), text(110, 855, "Se il pattern resta visibile con più metodi, è meno probabile che dipenda solo dai confini scelti.", 23, weight=700)])
    sidebar(parts, [("Megafarm Europe", ("Localizzazioni usate", "come punti non pesati.")), ("ISTAT 2025", ("Confini comunali.",))], ("Kernel density", ("Ogni punto diffonde la propria", "influenza nello spazio.", "Qui: raggio 20 km, celle 2 km.")))
    return finish(parts, 7, "Elaborazioni in EPSG:3035; massimi KDE e griglia non sono intercambiabili")


def slide_08_protected_data(rows):
    sample = []
    names = {"natura2000": "Natura 2000", "euap": "EUAP"}
    for r in rows:
        sample.append(("Suini" if r["animal"] == "Pigs" else "Pollame", names[r["protected_dataset"]], r["inside_percent"] + "%", r["within_1km_percent"] + "%", r["within_5km_percent"] + "%", str(round(float(r["median_m"]) / 1000, 1)).replace(".", ",") + " km"))
    return data_slide(8, "DATI DI PARTENZA  ·  TABELLA 02", "Distanze e soglie diventano confrontabili", "Una riga per specie e regime di tutela", ("Specie", "Tutela", "Dentro", "≤1 km", "≤5 km", "Mediana"), sample, (170, 230, 160, 160, 160, 190), "Quante localizzazioni ricadono dentro o vicino alle aree tutelate?", "Dati: Megafarm Europe + MASE Natura 2000 2025 ed EUAP 2010")


def proximity_slide(number, title_lines, subtitle, rows, dataset, maximum, sources, caveat):
    selected = {r["animal"]: r for r in rows if r["protected_dataset"] == dataset}
    parts = start("RISULTATO  ·  PROSSIMITÀ CUMULATIVA", title_lines, subtitle, "Quote cumulative delle localizzazioni per distanza dalle aree tutelate.")
    xvals = (300, 720, 1140)
    labels = ("DENTRO", "ENTRO 1 KM", "ENTRO 5 KM")
    for x, label in zip(xvals, labels):
        parts.extend([f'<line x1="{x}" y1="430" x2="{x}" y2="790" stroke="{RULE}"/>', text(x, 830, label, 18, fill=MUTED, weight=700, anchor="middle")])
    for animal, name, color in (("Pigs", "Suini", PIGS), ("Poultry", "Pollame", POULTRY)):
        r = selected[animal]
        values = [float(r[k]) for k in ("inside_percent", "within_1km_percent", "within_5km_percent")]
        points = [(x, 790 - value / maximum * 340) for x, value in zip(xvals, values)]
        parts.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="7"/>')
        label_dx = -22 if animal == "Pigs" else 22
        for (x, y), value in zip(points, values):
            parts.extend([f'<circle cx="{x}" cy="{y}" r="12" fill="{color}"/>', text(x + label_dx, y - 24, pct(value), 20, fill=color, weight=800, anchor="middle")])
        parts.extend([f'<circle cx="200" cy="{890 if animal == "Pigs" else 930}" r="8" fill="{color}"/>', text(220, 897 if animal == "Pigs" else 937, name + " · mediana " + str(round(float(r["median_m"]) / 1000, 1)).replace(".", ",") + " km", 19, weight=700)])
    parts.append(text(620, 915, caveat, 18, fill=MUTED))
    sidebar(parts, sources, ("Soglie cumulative", ("“Entro 5 km” comprende anche", "i punti entro 1 km e quelli interni.", "Non sono fasce normative.")))
    return finish(parts, number, "Distanze minime calcolate in EPSG:3035; prossimità non equivale a impatto")


def slide_11_municipal_data(rows):
    sample_rows = []
    for r in rows[:3] + rows[10:13]:
        sample_rows.append(("Suini" if r["animal"] == "Pigs" else "Pollame", r["rank_by_point_count"], r["municipality"], r["province"], r["region"], r["point_count"], str(round(float(r["density_km2"]), 3)).replace(".", ",")))
    return data_slide(11, "DATI DI PARTENZA  ·  TABELLA 03", "Una graduatoria comunale non è una mappa", "Conteggio e densità sono conservati come misure distinte", ("Specie", "Pos.", "Comune", "Provincia", "Regione", "Punti", "Punti/km²"), sample_rows, (150, 90, 300, 220, 220, 140, 180), "Quali comuni emergono, e quanto dipende dalla loro superficie?", "Dati: Megafarm Europe + confini comunali ISTAT 2025")


def ranking_slide(number, animal, title, rows):
    selected = [r for r in rows if r["animal"] == animal]
    color = PIGS if animal == "Pigs" else POULTRY
    parts = start("RISULTATO  ·  GRADUATORIA COMUNALE", (title,), "Ordinamento per numero di localizzazioni, non per densità", "Primi dieci comuni per conteggio di localizzazioni.")
    for i, r in enumerate(selected):
        y = 405 + i * 52
        width = int(r["point_count"]) / 30 * 760
        place = f'{r["municipality"]} — {r["province"]}, {r["region"]}'
        parts.extend([text(110, y + 26, str(i + 1), 17, fill=MUTED, weight=700), text(160, y + 26, place, 15, weight=600), f'<rect x="520" y="{y}" width="{width}" height="34" rx="5" fill="{color}"/>', text(1290, y + 26, r["point_count"], 20, weight=800, anchor="end"), text(1410, y + 26, str(round(float(r["density_km2"]), 3)).replace(".", ",") + "/km²", 16, fill=MUTED, anchor="end")])
    sidebar(parts, [("Megafarm Europe", ("Punti di presenza", "per specie.")), ("ISTAT 2025", ("Poligoni e superficie", "dei comuni."))], ("Graduatoria", ("Ordina i conteggi entro ciascun", "confine comunale. Non misura", "dimensione degli allevamenti.")))
    return finish(parts, number, "Scala delle barre comune alle due specie: 0–30 localizzazioni")


def slide_14_maup(rows):
    parts = start("METODO  ·  CONTEGGIO E DENSITÀ", ("I confini comunali possono", "cambiare la graduatoria"), "Gli stessi punti producono risultati diversi se cambia il denominatore territoriale", "Confronto fra conteggio e densità nei comuni in graduatoria.")
    x0, y0, pw, ph = 180, 800, 1120, 390
    parts.extend([f'<line x1="{x0}" y1="{y0}" x2="{x0 + pw}" y2="{y0}" stroke="{INK}" stroke-width="2"/>', f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 - ph}" stroke="{INK}" stroke-width="2"/>', text(x0 + pw / 2, 865, "Numero di localizzazioni", 20, anchor="middle"), text(110, 440, "Punti/km²", 18, fill=MUTED)])
    for value in (0, 10, 20, 30):
        x = x0 + value / 30 * pw
        parts.extend([f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0 - ph}" stroke="{RULE}"/>', text(x, y0 + 32, value, 16, fill=MUTED, anchor="middle")])
    for value in (0, .2, .4, .6, .8):
        y = y0 - value / .8 * ph
        parts.extend([f'<line x1="{x0}" y1="{y}" x2="{x0 + pw}" y2="{y}" stroke="{RULE}"/>', text(x0 - 20, y + 6, str(value).replace(".", ","), 16, fill=MUTED, anchor="end")])
    labels = {"Forlì", "Roverchiara", "Orzinuovi", "Borghi", "Isola della Scala"}
    for r in rows:
        x = x0 + int(r["point_count"]) / 30 * pw
        y = y0 - float(r["density_km2"]) / .8 * ph
        color = PIGS if r["animal"] == "Pigs" else POULTRY
        parts.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{color}"/>')
        if r["municipality"] in labels:
            parts.append(text(x + 12, y - 12, r["municipality"], 15, fill=color, weight=700))
    sidebar(parts, [("Megafarm Europe", ("Localizzazioni.",)), ("ISTAT 2025", ("Confini e aree", "comunali."))], ("MAUP", ("Il risultato di un’aggregazione", "dipende da forma e dimensione", "delle unità territoriali scelte.")))
    return finish(parts, 14, "Sono mostrati i venti comuni delle due graduatorie, non tutti i comuni italiani")


def slide_15_geomorphon_data(rows):
    wanted = (("Pigs", "flat"), ("Pigs", "slope"), ("Pigs", "valley"), ("Poultry", "flat"), ("Poultry", "slope"), ("Poultry", "valley"))
    labels = {"flat": "pianura locale", "slope": "versante", "valley": "valle"}
    lookup = {(r["animal"], r["geomorphon_label"]): r for r in rows}
    sample = []
    for animal, form in wanted:
        r = lookup[(animal, form)]
        sample.append(("Suini" if animal == "Pigs" else "Pollame", labels[form], r["point_count"], pct(float(r["share_percent"])), f'{float(r["elev_median"]):.0f} m'))
    return data_slide(15, "DATI DI PARTENZA  ·  GEOMORPHON", "Il rilievo diventa una tabella di forme", "Una riga per specie e forma locale del terreno", ("Specie", "Forma", "Punti", "Quota punti", "Quota mediana"), sample, (190, 300, 160, 180, 220), "In quali forme del territorio ricadono le localizzazioni?", "Dati: Megafarm Europe + Copernicus DEM GLO-30; elaborazione GRASS r.geomorphon")


def slide_16_geomorphon(rows, medians):
    lookup = {(r["animal"], r["geomorphon_label"]): float(r["share_percent"]) for r in rows}
    parts = start("RISULTATO  ·  FORME DEL TERRENO", ("I punti suini insistono soprattutto", "su superfici localmente pianeggianti"), "Il pollame presenta una distribuzione geomorfologica più diversificata", "Distribuzione delle localizzazioni per forma locale del terreno.")
    categories = (("Pianura locale", "flat"), ("Versante", "slope"), ("Valle", "valley"), ("Crinale", "ridge"), ("Dosso", "spur"))
    for i, (label, key) in enumerate(categories):
        y = 410 + i * 82
        pig = lookup[("Pigs", key)]
        poultry = lookup[("Poultry", key)]
        parts.extend([
            text(110, y + 24, label, 19, weight=600),
            f'<rect x="320" y="{y}" width="{pig / 80 * 820}" height="26" rx="4" fill="{PIGS}"/>',
            text(1165, y + 21, pct(pig), 18, fill=PIGS, weight=800),
            f'<rect x="320" y="{y + 34}" width="{poultry / 80 * 820}" height="26" rx="4" fill="{POULTRY}"/>',
            text(1165, y + 55, pct(poultry), 18, fill=POULTRY, weight=800),
        ])
    parts.extend([
        f'<circle cx="110" cy="856" r="8" fill="{PIGS}"/>', text(130, 863, "Suini", 18, weight=700),
        f'<circle cx="230" cy="856" r="8" fill="{POULTRY}"/>', text(250, 863, "Pollame", 18, weight=700),
        text(470, 863, f"Quota mediana complessiva: suini {medians['Pigs']:.1f} m · pollame {medians['Poultry']:.1f} m".replace(".", ","), 20, fill=MUTED),
        text(110, 920, "“Pianeggiante” descrive la forma locale, non implica necessariamente bassa quota.", 20, weight=600),
    ])
    sidebar(parts, [("Megafarm Europe", ("Localizzazioni attuali." ,)), ("Copernicus DEM", ("Modello digitale di elevazione", "GLO-30, ricampionato a 100 m."))], ("GRASS r.geomorphon", ("Classifica automaticamente ogni", "cella in una forma del terreno", "osservando l’intorno: qui ~1 km.")))
    return finish(parts, 16, "Parametri: search=10 celle, flat=1°; 2.145 punti con quota e classe valide")


def slide_17_integrated(joint, medians, agricultural):
    parts = start("IPOTESI  ·  TERRITORIO E PRODUZIONE", ("Il contesto è misurabile,", "l’impatto non ancora"), "Geomorfologia, copertura del suolo e quota descrivono dove sono i punti, non i loro effetti", "Integrazione delle caratteristiche territoriali e limiti della domanda causale.")
    for i, (animal, label, color) in enumerate((("Pigs", "SUINI", PIGS), ("Poultry", "POLLAME", POULTRY))):
        x = 110 + i * 450
        parts.extend([
            text(x, 410, label, 19, fill=color, weight=700, spacing=1.2),
            text(x, 476, pct(joint[animal]), 48, fill=color, weight=800),
            multiline(x, 512, ("in contesto insieme", "agricolo e pianeggiante"), 19, fill=MUTED, weight=600),
            text(x, 610, pct(agricultural[animal]), 34, weight=800), text(x, 640, "in superfici agricole CLC 2018", 17, fill=MUTED),
            text(x, 700, f"{medians[animal]:.1f} m".replace(".", ","), 34, weight=800), text(x, 730, "quota mediana", 17, fill=MUTED),
        ])
    parts.extend([
        f'<line x1="1010" y1="390" x2="1010" y2="900" stroke="{RULE}" stroke-width="2"/>',
        text(1060, 420, "PER VERIFICARE UN IMPATTO SERVONO", 17, fill=CHANGE, weight=700, spacing=1.1),
        text(1060, 475, "1  Superficie degli impianti", 22, weight=700),
        text(1090, 507, "Impronte degli edifici, ortofoto e autorizzazioni.", 17, fill=MUTED),
        text(1060, 565, "2  Intensità produttiva", 22, weight=700),
        text(1090, 597, "Capi, capacità autorizzata, reflui ed emissioni.", 17, fill=MUTED),
        text(1060, 655, "3  Esiti agricoli e ambientali", 22, weight=700),
        text(1090, 687, "Rese, superfici coltivate, nitrati, acqua e aria.", 17, fill=MUTED),
        f'<rect x="1060" y="750" width="350" height="120" rx="8" fill="#E8DDD0"/>',
        text(1085, 790, "CON QUESTI DATI", 16, fill=CHANGE, weight=700),
        multiline(1085, 824, ("Si individuano contesti e aree", "in cui costruire la ricerca causale."), 18, weight=600),
    ])
    sidebar(parts, [("Megafarm Europe", ("Presenze, senza superficie", "o capacità produttiva.")), ("Copernicus", ("CLC 2018 e DEM GLO-30.",)), ("GRASS GIS", ("Forme r.geomorphon.",))], ("Incrocio puntuale", ("Associa a ogni localizzazione", "la classe CLC, la forma del", "terreno e la quota.")))
    return finish(parts, 17, "Il confronto è descrittivo: non misura occupazione di suolo, produzione o inquinamento")


def slide_18_water_screening():
    parts = start("METODO  ·  SCREENING IDROLOGICO", ("La distanza dall’acqua segnala", "prossimità, non inquinamento"), "Un esempio didattico per selezionare aree da approfondire", "Schema di un indicatore di prossimità e connessione potenziale al reticolo idrografico.")
    parts.extend([
        text(110, 390, "ESEMPIO SCHEMATICO · NON È UN RISULTATO", 17, fill=CHANGE, weight=700, spacing=1.2),
        f'<path d="M180 790 C330 690 300 520 500 560 S720 760 840 620 S1030 400 1320 470" fill="none" stroke="#4A91C5" stroke-width="18" stroke-linecap="round"/>',
        f'<path d="M630 690 C700 620 720 530 700 430" fill="none" stroke="#78B4D8" stroke-width="9" stroke-linecap="round"/>',
        f'<circle cx="350" cy="510" r="15" fill="{PIGS}"/><circle cx="575" cy="470" r="15" fill="{POULTRY}"/><circle cx="980" cy="700" r="15" fill="{PIGS}"/>',
        f'<line x1="350" y1="510" x2="390" y2="650" stroke="{MUTED}" stroke-width="3" stroke-dasharray="8 8"/>',
        f'<line x1="575" y1="470" x2="650" y2="610" stroke="{MUTED}" stroke-width="3" stroke-dasharray="8 8"/>',
        f'<line x1="980" y1="700" x2="920" y2="570" stroke="{MUTED}" stroke-width="3" stroke-dasharray="8 8"/>',
        text(270, 480, "≤250 m", 19, fill=PIGS, weight=800), text(530, 440, "250–1.000 m", 19, fill=POULTRY, weight=800), text(960, 740, ">1 km", 19, fill=PIGS, weight=800),
        text(110, 850, "1", 28, fill=CHANGE, weight=800), text(150, 850, "Misura la distanza minima", 20, weight=700),
        text(490, 850, "2", 28, fill=CHANGE, weight=800), text(530, 850, "Aggiunge pendenza e deflusso", 20, weight=700),
        text(930, 850, "3", 28, fill=CHANGE, weight=800), text(970, 850, "Seleziona casi da verificare", 20, weight=700),
        text(110, 915, "Domanda corretta: quali localizzazioni sono più vicine o potenzialmente connesse al reticolo?", 21, weight=700),
    ])
    sidebar(parts, [("Megafarm Europe", ("Localizzazioni attuali." ,)), ("EU-Hydro", ("Reticolo dettagliato previsto;", "estratto valido ancora atteso.")), ("Copernicus DEM", ("Pendenza e direzione", "potenziale del deflusso."))], ("Screening", ("Ordina i casi per priorità.", "Non stima contaminanti né", "dimostra un impatto.")))
    return finish(parts, 18, "Il reticolo ISPRA 1:250.000 non supporta soglie di 250 m–1 km; distanze mostrate solo a scopo illustrativo")


def slide_19_water_result(rows):
    selected = {row["animal"]: row for row in rows}
    parts = start("RISULTATO PARZIALE  ·  RETICOLO ISPRA", ("Il pollame risulta più vicino", "ai corsi d’acqua rappresentati"), "Distanza euclidea dal reticolo nazionale alla scala 1:250.000", "Risultato esplorativo della prossimità al reticolo ISPRA.")
    thresholds = (("≤250 m", "within_250m_percent"), ("≤500 m", "within_500m_percent"), ("≤1 km", "within_1000m_percent"), ("≤5 km", "within_5000m_percent"))
    xvals = (260, 560, 860, 1160)
    for x, (label, _) in zip(xvals, thresholds):
        parts.extend([f'<line x1="{x}" y1="430" x2="{x}" y2="790" stroke="{RULE}"/>', text(x, 830, label, 18, fill=MUTED, weight=700, anchor="middle")])
    for animal, name, color in (("Pigs", "Suini", PIGS), ("Poultry", "Pollame", POULTRY)):
        values = [float(selected[animal][field]) for _, field in thresholds]
        points = [(x, 790 - value / 100 * 340) for x, value in zip(xvals, values)]
        parts.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="7"/>')
        offset = -20 if animal == "Pigs" else 20
        for (x, y), value in zip(points, values):
            parts.extend([f'<circle cx="{x}" cy="{y}" r="11" fill="{color}"/>', text(x + offset, y - 22, pct(value), 18, fill=color, weight=800, anchor="middle")])
        median = float(selected[animal]["median_m"]) / 1000
        ly = 890 if animal == "Pigs" else 930
        parts.extend([f'<circle cx="180" cy="{ly - 7}" r="8" fill="{color}"/>', text(200, ly, f"{name} · mediana {median:.2f} km".replace(".", ","), 19, weight=700)])
    parts.append(text(650, 915, "Risultato utile per screening nazionale, non per distanze locali di precisione.", 18, fill=MUTED))
    sidebar(parts, [("Megafarm Europe", ("2.145 localizzazioni." ,)), ("ISPRA", ("Reticolo idrografico nazionale", "alla scala 1:250.000."))], ("Distanza minima", ("Segmento più breve tra punto", "e linea d’acqua rappresentata.", "Non segue il deflusso reale.")))
    return finish(parts, 19, "Risultato esplorativo: il reticolo generalizzato può omettere corsi minori e sovrastimare le distanze")


def slide_20_national_map():
    figure = ROOT / "outputs/figures/figure_01_national_distribution.png"
    parts = start("MAPPA  ·  DISTRIBUZIONE NAZIONALE", ("Le presenze si concentrano", "soprattutto nell’Italia settentrionale"), "La mappa mostra localizzazioni, non dimensione o produzione degli impianti", "Distribuzione nazionale delle localizzazioni per specie.")
    parts.append(cropped_png(figure, 110, 370, 500, 555, (70, 180, 1120, 1660), (1653, 2338)))
    parts.extend([
        text(680, 420, "COSA RENDE VISIBILE", 17, fill=CHANGE, weight=700, spacing=1.2),
        text(680, 475, "Concentrazione", 25, weight=700), multiline(680, 508, ("Molti punti si addensano nella", "Pianura Padana."), 19, fill=MUTED),
        text(680, 610, "Differenze tra specie", 25, weight=700), multiline(680, 643, ("Suini e pollame condividono alcune", "aree, ma non la stessa geografia."), 19, fill=MUTED),
        text(680, 745, "Limite", 25, weight=700), multiline(680, 778, ("La sovrapposizione dei simboli", "nasconde la densità locale."), 19, fill=MUTED),
        f'<circle cx="690" cy="882" r="10" fill="{PIGS}"/>', text(715, 889, "Suini", 18, weight=700),
        f'<circle cx="820" cy="882" r="10" fill="{POULTRY}"/>', text(845, 889, "Pollame", 18, weight=700),
    ])
    sidebar(parts, [("Megafarm Europe", ("Punti di presenza", "distinti per specie.")), ("ISTAT 2025", ("Confini regionali", "ufficiali."))], ("Mappa di punti", ("Mostra posizione e distribuzione.", "Non pesa i punti per capi", "o capacità produttiva.")))
    return finish(parts, 20, "Cartografia: qgis/allevamenti.qgs · figura_01_national_distribution.png")


def hotspot_map_slide(number, title, subtitle, filename, color):
    figure = ROOT / "outputs/figures" / filename
    parts = start("MAPPA  ·  DENSITÀ KERNEL", title, subtitle, "Mappa di dettaglio della densità kernel e delle localizzazioni pubblicate.")
    parts.append(embedded_png(figure, 110, 365, 1280, 550, fit="xMidYMid slice"))
    parts.extend([
        f'<rect x="125" y="850" width="470" height="52" rx="6" fill="{BG}" opacity="0.92"/>',
        text(145, 884, "Il colore di fondo rappresenta la densità stimata", 18, fill=color, weight=700),
    ])
    sidebar(parts, [("Megafarm Europe", ("Punti suini e avicoli." ,)), ("ISTAT 2025", ("Confini provinciali." ,)), ("ISPRA", ("Reticolo nazionale", "1:250.000, solo contesto."))], ("Kernel density", ("Distribuisce ogni punto", "entro un raggio di 20 km.", "“Hotspot” non è un test statistico.")))
    return finish(parts, number, "KDE: bandwidth 20 km, cella 2 km; valori in punti/km²")


def main():
    summary_rows = read_rows("table_01_summary.csv")
    summary = {r["animal"]: r for r in summary_rows}
    protected = read_rows("table_02_protected_areas.csv")
    municipalities = read_rows("table_03_top_municipalities.csv")
    transitions = read_rows("table_04_clc_level1_transitions.csv")
    with (ROOT / "data/derived/vectors/megafarms_dem_geomorphon_summary.csv").open(encoding="utf-8") as stream:
        geomorphons = list(csv.DictReader(stream))
    with (ROOT / "data/derived/vectors/megafarms_water_proximity_ispra_summary.csv").open(encoding="utf-8") as stream:
        water = list(csv.DictReader(stream))
    assert sum(int(r["total_points"]) for r in summary_rows) == 2145
    database = sqlite3.connect(ROOT / "data/processed/allevamenti.gpkg")
    assert database.execute(
        'SELECT "Type of Animal", clc_1990, clc_2018 FROM megafarms_points_clc_1990_2018 WHERE source_fid=105'
    ).fetchone() == ("Pigs", "211", "121")
    assert database.execute(
        "SELECT point_count FROM megafarms_clc_transitions WHERE animal='All' AND clc_1990='211' AND clc_2018='121'"
    ).fetchone()[0] == 23
    medians, joint, agricultural = {}, {}, {}
    for animal in ("Pigs", "Poultry"):
        elevations = [row[0] for row in database.execute(
            'SELECT dem_elev_m FROM megafarms_points_dem_geomorphon WHERE "Type of Animal"=?', (animal,)
        )]
        total = len(elevations)
        medians[animal] = statistics.median(elevations)
        joint_count = database.execute(
            '''SELECT count(*) FROM megafarms_points_dem_geomorphon g
               JOIN megafarms_points_clc_1990_2018 c USING(source_fid)
               WHERE g."Type of Animal"=? AND g.geomorphon_label='flat'
               AND c.clc1_2018='Superfici agricole' ''', (animal,)
        ).fetchone()[0]
        agricultural_count = database.execute(
            '''SELECT count(*) FROM megafarms_points_clc_1990_2018
               WHERE "Type of Animal"=? AND clc1_2018='Superfici agricole' ''', (animal,)
        ).fetchone()[0]
        joint[animal] = joint_count / total * 100
        agricultural[animal] = agricultural_count / total * 100
    database.close()

    slides = {
        "slide_01_clc_explainer": slide_01_clc_explainer(),
        "slide_02_clc_data": slide_02_clc_data(transitions),
        "slide_03_clc_scale": slide_03_clc_scale(summary, transitions),
        "slide_04_clc_transitions": slide_04_clc_summary(summary, transitions),
        "slide_05_summary_data": slide_05_summary_data(summary),
        "slide_06_dataset_overview": slide_06_overview(summary),
        "slide_07_spatial_lenses": slide_07_lenses(summary),
        "slide_08_protected_areas_data": slide_08_protected_data(protected),
        "slide_09_natura2000": proximity_slide(9, ("Oltre metà dei punti è entro 5 km", "da un sito Natura 2000"), "Confronto cumulativo per specie", protected, "natura2000", 65, [("Megafarm Europe", ("Localizzazioni attuali.",)), ("Natura 2000 MASE", ("SIC, ZSC e ZPS,", "fornitura 2025."))], "Mediane: suini 4,8 km · pollame 4,0 km"),
        "slide_10_euap": proximity_slide(10, ("La prossimità alle aree EUAP", "è meno frequente"), "Confronto cumulativo per specie", protected, "euap", 30, [("Megafarm Europe", ("Localizzazioni attuali.",)), ("EUAP MASE", ("Parchi e riserve del", "VI Elenco, 2010."))], "Mediane: suini 8,2 km · pollame 10,3 km"),
        "slide_11_municipalities_data": slide_11_municipal_data(municipalities),
        "slide_12_pigs_municipalities": ranking_slide(12, "Pigs", "Orzinuovi guida la graduatoria suina", municipalities),
        "slide_13_poultry_municipalities": ranking_slide(13, "Poultry", "Forlì e Isola della Scala guidano il pollame", municipalities),
        "slide_14_count_vs_density": slide_14_maup(municipalities),
        "slide_15_geomorphon_data": slide_15_geomorphon_data(geomorphons),
        "slide_16_geomorphon_results": slide_16_geomorphon(geomorphons, medians),
        "slide_17_territory_impact_limits": slide_17_integrated(joint, medians, agricultural),
        "slide_18_water_screening": slide_18_water_screening(),
        "slide_19_water_screening_result": slide_19_water_result(water),
        "slide_20_national_map": slide_20_national_map(),
        "slide_21_pigs_hotspot_map": hotspot_map_slide(21, ("L’hotspot suino emerge", "nella Pianura Padana centrale"), "Densità stimata e localizzazioni pubblicate", "figure_02_pigs_hotspot.png", PIGS),
        "slide_22_poultry_hotspot_map": hotspot_map_slide(22, ("L’hotspot avicolo si estende", "verso la Pianura Padana orientale"), "Densità stimata e localizzazioni pubblicate", "figure_03_poultry_hotspot.png", POULTRY),
    }

    SLIDES.mkdir(parents=True, exist_ok=True)
    expected = {f"{name}.{ext}" for name in slides for ext in ("svg", "png", "pdf")}
    for old in SLIDES.glob("slide_*.*"):
        if old.name not in expected:
            old.unlink()
    converter = shutil.which("rsvg-convert")
    for name, content in slides.items():
        svg = SLIDES / f"{name}.svg"
        svg.write_text(content, encoding="utf-8")
        if converter:
            subprocess.run([converter, "-w", str(W), "-h", str(H), str(svg), "-o", str(svg.with_suffix(".png"))], check=True)
            subprocess.run([converter, "-f", "pdf", str(svg), "-o", str(svg.with_suffix(".pdf"))], check=True)
    print(f"Create {len(slides)} slide in {SLIDES}" + (" con PNG e PDF" if converter else ""))


if __name__ == "__main__":
    main()
