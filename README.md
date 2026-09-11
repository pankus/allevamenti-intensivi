# Allevamenti intensivi in Italia

## Obiettivo

Prototipo riproducibile per un paper di storia dell'ambiente: mostrare come GIS e analisi spaziale permettono di passare da una mappa di localizzazioni di mega-allevamenti a risultati verificabili su concentrazione territoriale, uso/copertura del suolo e possibile pressione ambientale. I punti **non sono una misura del numero di capi, delle emissioni o della produzione**: ogni inferenza va formulata come presenza/concentrazione delle localizzazioni pubblicate.

L'analisi tratta la distribuzione dei punti come un indicatore di presenza/concentrazione territoriale, non come stima diretta di capi, emissioni, produzione o relazioni di filiera.

## Struttura dei dati

```text
data/
  raw/megafarms/                 # originale immutato e fonti future scaricate
  processed/allevamenti.gpkg     # tutti i vettori normalizzati, EPSG:3035
  derived/vectors/               # output vettoriali derivati
  derived/rasters/               # output raster derivati
styles/vectors/                  # .qml per ogni vettore
styles/rasters/                  # .qml obbligatorio per ogni raster derivato
qgis/allevamenti.qgs             # progetto QGIS
scripts/                         # comandi riproducibili
```

Non cancellare né sovrascrivere un file in `data/raw/`. Ogni download futuro va in `data/raw/<ente>/<dataset>/<versione>/`; il vettore importato/ritagliato va come nuovo layer in `data/processed/allevamenti.gpkg`. Conservare URL, data di download, licenza, versione e comando di trasformazione in questo README o in `docs/fonti.md`.

## Dati iniziali e controllo qualità

- Originale: `geodata/Italy points map.geojson`, copiato senza modifiche in `data/raw/megafarms/Italy points map.geojson`.
- Fonte dichiarata: [Megafarm Europe](https://megafarms-europe.netlify.app/index.html). La pagina definisce «industrial» come almeno 40.000 polli, 750 suini riproduttori o 2.000 suini da ingrasso. Verificare licenza, metodologia e data di estrazione prima della pubblicazione.
- `megafarms_italy_points` (GeoPackage): 2.146 record, trasformati da WGS 84 assunto (`EPSG:4326`) a `EPSG:3035`.
- `megafarms_italy_points_valid`: 2.145 record, usato nel progetto QGIS; esclude **solo** il record `[0,0]` (un suino), evidentemente fuori dall'Italia. Totali analizzabili: 903 suini, 1.242 pollame. Il record resta nel layer completo per audit.

L'assunzione WGS 84 deriva dalla convenzione GeoJSON e dalla natura delle coordinate; il file non contiene un oggetto CRS. Va confermata con il produttore dei dati.

## CRS adottato

Il progetto e i dati derivati usano **ETRS89 / LAEA Europe, EPSG:3035**. È una proiezione metrica a pari area con ambito dichiarato per analisi statistiche europee: è quindi idonea a buffer, aree, densità per km² e raster/grid comparabili. Non calcolare aree o densità in gradi (`EPSG:4326`).

Per un'eventuale analisi di distanze ad alta precisione locale si valuterà un CRS UTM per singola zona; per l'Italia intera, che attraversa più zone, EPSG:3035 evita discontinuità e conserva confrontabilità con CORINE/EEA.

Fonti: [EPSG 3035](https://epsg.org/crs_3035/ETRS89-extended-LAEA-Europe.html), [Copernicus CORINE Land Cover](https://land.copernicus.eu/en/products/corine-land-cover/).

## Griglia nazionale e densità dei punti

La griglia regolare usa celle di **10 × 10 km** in EPSG:3035, allineate ai multipli di 10.000 m del CRS. Sono conservate le 3.497 celle con intersezione areale con i confini comunali ISTAT 2025; le celle restano quadrate e non vengono ritagliate sulla costa. `cell_km2` vale quindi 100 e `density_km2` è `point_count / 100`. `land_km2` documenta la superficie terrestre nella cella e permette di riconoscere gli effetti di bordo costieri, ma non è usato come denominatore.

La scelta di 10 km è un compromesso nazionale verificato esplorativamente contro celle di 5 e 20 km. Per suini, le celle occupate e il massimo per cella sono rispettivamente 544/12, 321/27 e 174/53; per pollame 689/19, 401/26 e 204/77. La griglia da 5 km frammenta maggiormente i 2.145 punti, mentre quella da 20 km appiattisce i cluster locali.

Output: `data/derived/vectors/megafarms_grid_10km.gpkg`, replicato nel GeoPackage analitico come `megafarms_grid_10km_pigs` e `megafarms_grid_10km_poultry`. Controlli: 903 suini e 1.242 punti di pollame conservati; 321 e 401 celle occupate; geometrie valide. Gli stili sono in `styles/vectors/` e classificano la densità in punti/km².

Comando riproducibile:

```bash
python3 scripts/build_grid_density.py
```

La densità misura esclusivamente la concentrazione delle localizzazioni pubblicate, non capi, produzione, emissioni o pressione ambientale effettiva. Dimensione, allineamento e celle costiere possono modificare il pattern osservato.

## Conteggi e densità comunali

I punti sono attribuiti per intersezione ai confini `istat_comuni_2025`; eventuali punti esattamente sul confine vengono assegnati deterministicamente al codice comunale minore. In questa esecuzione non si verificano casi ambigui. La densità è `point_count / area_km2`, con area geometrica calcolata in EPSG:3035.

Output: `data/derived/vectors/megafarms_municipality_density.gpkg`, importato anche in `allevamenti.gpkg` come `megafarms_municipality_2025_pigs` e `megafarms_municipality_2025_poultry`. Ciascun layer contiene tutti i 7.896 comuni: 498 hanno almeno un punto suino e 604 almeno un punto di pollame; i totali restano 903 e 1.242. Le due geometrie ISTAT non valide (Sannicandro di Bari e Bronte) sono riparate solo nell'output derivato, senza modificare il layer sorgente. Gli stili in `styles/vectors/` usano classi comuni di punti/km² per rendere confrontabili le due categorie.

```bash
python3 scripts/build_municipality_density.py
```

Questi risultati dipendono dalle unità amministrative 2025 e sono soggetti al **modifiable areal unit problem (MAUP)**: aggregazioni e densità cambiano con forma, estensione e versione dei comuni. Il confronto con la griglia regolare serve a non scambiare un effetto dei confini amministrativi per un pattern territoriale stabile; i comuni 2025 non vanno inoltre retroproiettati senza cautela su periodi storici.

## Densità kernel

I raster separati per suini e pollame usano il kernel quartico di QGIS, senza pesi aziendali, con **bandwidth/raggio di 20 km** e celle di **2 km**. L'output QGIS scalato da punti/m² è convertito in punti/km², portato su un'estensione comune e ritagliato sul confine nazionale. Le celle interne senza influenza di punti valgono zero; l'esterno è NoData (`-9999`).

Il controllo esplorativo ha confrontato bandwidth di 10, 20 e 30 km a cella costante di 2 km. Per i suini i massimi risultano 0,2200, 0,1365 e 0,1080 punti/km², con supporti di 58.608, 113.260 e 159.732 km²; per il pollame 0,2753, 0,1727 e 0,1233, con supporti di 73.400, 136.728 e 190.248 km². I 10 km producono superfici più frammentate, i 30 km fondono maggiormente i cluster; 20 km conserva dettaglio regionale senza isolare quasi ogni singolo punto. La cella da 2 km campiona il bandwidth con dieci pixel.

Output: `data/derived/rasters/megafarms_kde_20km_pigs.tif` e `megafarms_kde_20km_poultry.tif`, entrambi EPSG:3035, 497 × 640 pixel. Gli stili `styles/rasters/megafarms_kde_20km_{pigs,poultry}.qml` adottano gli stessi intervalli per consentire il confronto. L'integrale dopo il ritaglio è 899,4 per i suini e 1.226,6 per il pollame, poco inferiore ai conteggi 903 e 1.242 perché la parte dei kernel che ricade in mare viene esclusa.

```bash
python3 scripts/build_kernel_density.py
```

Il risultato rappresenta intensità spaziale stimata delle sole localizzazioni note. Bandwidth e funzione kernel modificano forma e intensità degli hotspot; il raster non misura capi, emissioni o produzione.

## Classi e transizioni CORINE Land Cover

A ciascuno dei 2.145 punti attuali sono attribuiti per intersezione i codici CLC di terzo livello del 1990 e del 2018. Un solo punto, nel comune di Rosolina, cade in una lacuna topologica/costiera: in entrambi gli anni è assegnato alla classe più vicina entro la tolleranza dichiarata di 200 m (`142`, distanza 137,84 m). I campi `clc1990_m` e `clc2018_m` valgono zero per le intersezioni dirette e registrano la distanza per questo controllo; non risultano assegnazioni ambigue su confini tra più poligoni.

Output: `data/derived/vectors/megafarms_clc_transitions.gpkg`, importato anche in `allevamenti.gpkg` con il layer puntuale `megafarms_points_clc_1990_2018` e la tabella `megafarms_clc_transitions`. La stessa tabella è esportata come CSV nella directory derivata. Contiene conteggi e percentuali per suini, pollame e totale, distinti per coppia `clc_1990` → `clc_2018`; i codici seguono la nomenclatura ufficiale CLC. Sono diverse tra i due anni 65 attribuzioni suine (7,2%) e 179 avicole (14,4%).

```bash
python3 scripts/build_clc_transitions.py
```

Il confronto descrive il cambiamento di copertura del suolo **nelle localizzazioni oggi note**. Non dimostra che gli allevamenti esistessero nel 1990 o nel 2018, né che abbiano causato le transizioni osservate; risoluzione minima e generalizzazione CLC impongono inoltre di interpretare la classe come contesto territoriale, non come rilievo del singolo fabbricato.

## Primo download: confini ISTAT 2025

Eseguito con `scripts/download_istat_confini_2025.sh`. Il download originale (94,7 MB), URL e checksum sono in `data/raw/istat/confini_amministrativi/2025/`; il GeoPackage contiene i layer EPSG:3035 `istat_comuni_2025` (7.896), `istat_province_2025` (107) e `istat_regioni_2025` (20).

Usare l'orchestratore per controllare il collegamento prima di eseguire script Bash: `python3 scripts/run_downloads.py --check` oppure `python3 scripts/run_downloads.py`. Ogni nuovo script deve dichiarare la propria riga `URL="https://..."`; l'orchestratore la valida con `HEAD` e, se necessario, con `GET` a un byte.

I confini comunali sono il denominatore per conteggi e densità di punti per km²; province e regioni servono a leggibilità e controllo dei risultati. L'analisi principale di concentrazione userà anche una griglia regolare, per non dipendere solo dai confini amministrativi (MAUP).

## Piano dati vettoriali

1. **ISTAT confini amministrativi 2025** — già scaricato: unità di aggregazione e area di riferimento.
2. **CORINE Land Cover 1990 e 2018, vettore Copernicus** — scaricati e importati: contesto e mutamento del suolo.
3. **Rete idrografica nazionale ISPRA** — scaricata: rete nazionale a scala 1:250.000, utile per mappa e contesto di bacino; non per affermazioni di prossimità a 500 m o 1 km.
4. **Rete Natura 2000 MASE** — scaricata: siti SIC/ZSC/ZPS, per intersezione/distanza rispetto a siti della rete.
5. **EUAP MASE** — scaricato: parchi e riserve dell'Elenco Ufficiale Aree Protette; è un layer distinto da Natura 2000.

Per ora non scaricare dati di filiera, macelli, strade, falde vulnerabili o statistica dei capi: non sono necessari al primo nucleo dimostrativo e richiedono definizioni/temporalità aggiuntive. Tutti i quattro strati sopra sono vettoriali. Il prodotto di densità kernel sarà invece un raster derivato, con il suo `.qml`.

## Rete idrografica e Natura 2000

Eseguiti tramite l'orchestratore:

- `ispra_reticolo_idrografico`: 61.978 linee, da Reticolo Idrografico Nazionale ISPRA 1:250.000. Originale GeoPackage, URL e checksum: `data/raw/ispra/reticolo_idrografico/1_250000/`.
- `mase_natura2000_2025`: 2.649 poligoni, cartografia ufficiale SIC/ZSC/ZPS MASE trasmessa alla Commissione europea nel dicembre 2025. Archivio originale, URL e checksum: `data/raw/mase/natura2000/2025-12/`.

La Rete Natura 2000 non sostituisce l'**EUAP**: i due regimi possono sovrapporsi, ma non coincidono. L'EUAP è importato come `mase_euap_2010` (871 poligoni) da WFS ufficiale MASE; originale GeoPackage, URL e checksum: `data/raw/mase/euap/2010/`. È il VI Elenco ufficiale (2010, licenza CC BY 4.0): va trattato come strato storico di tutela, non come perimetrazione attuale. I layer restano separati, senza dissolvere le sovrapposizioni.

Entrambi sono importati in EPSG:3035 in `data/processed/allevamenti.gpkg`. La Natura 2000 è contemporanea e non va retroproiettata al 1990; per il confronto CLC documenta esposizione/contesto attuale, non tutela storica.

### Reticolo per le distanze

Il reticolo ISPRA 1:250.000 resta nel progetto come quadro nazionale e di bacino, ma non supporta misure di distanza di 500 m–1 km. Per l'analisi di prova è scelto **EU-Hydro River Network Database v1.3** (EEA/Copernicus): vettoriale, coerente su scala europea, con uso raccomandato fino a 1:30.000 e copertura italiana. Il task CLMS `29962405257` è stato completato e l'originale, URL sorgente e checksum sono in `data/raw/copernicus/eu_hydro/v1.3_2006-2012/`.

Tutti i 20 layer vettoriali del pacchetto sono importati in `allevamenti.gpkg` con prefisso `euhydro_`; il layer operativo per i corsi d'acqua è `euhydro_hydro_river_net_l` (95.002 feature).

EU-Hydro deriva soprattutto da fonti 2006–2012: descrive un'infrastruttura idrografica di riferimento, non lo stato attuale. Nei futuri approfondimenti sui cluster si potranno sostituire o verificare le distanze con i reticoli ufficiali regionali, normalmente più dettagliati ma non omogenei per data, scala, attributi e licenza. Non fonderli in un unico reticolo nazionale senza un controllo di armonizzazione. La raccolta e l'importazione sono ripetibili con `scripts/collect_copernicus_euhydro_italy.sh`.

Il piano operativo aggiornato è in [`TODO.md`](TODO.md).

## QGIS e stili

Aprire `qgis/allevamenti.qgs`. Il layer attivo è categorizzato: rosso = suini, blu = pollame. Lo stile indipendente è `styles/vectors/megafarms_italy_points.qml` (in QGIS: **Proprietà layer → Simbologia → Stile → Carica stile**).

Per ogni raster creato in `data/derived/rasters/` creare nello stesso momento il corrispondente `styles/rasters/<nome-raster>.qml`; nessun raster è stato ancora prodotto, quindi non è corretto inventarne uno o uno stile. Interpreto “qms” come il formato QGIS **`.qml`**: confermare se intendevi un formato diverso.

## Installazione

Su Ubuntu/Debian:

```bash
sudo apt update
sudo apt install qgis qgis-plugin-grass gdal-bin
qgis --version
ogr2ogr --version
```

QGIS 3.40+ e GDAL/OGR sono sufficienti per questa prima fase. Se si usa `scripts/build_qgis_project.py`, installare anche i binding Python distribuiti con QGIS (es. pacchetto `python3-pyqt6` della stessa distribuzione); il file `.qgs` già incluso non richiede Python.

## Riproducibilità

Importazione eseguita (l'originale resta intatto):

```bash
ogr2ogr -f GPKG data/processed/allevamenti.gpkg \
  'data/raw/megafarms/Italy points map.geojson' \
  -nln megafarms_italy_points -nlt POINT -s_srs EPSG:4326 -t_srs EPSG:3035
```

Per produrre un layer analitico, registrare nel README il filtro applicato e non sostituire il layer completo.

## Estratti CORINE Italia: 1990 e 2018

Il confronto è metodologicamente utile per descrivere il mutamento di uso/copertura del suolo **attorno agli attuali punti** fra 1990 e 2018. Non dimostra l'evoluzione storica degli allevamenti, perché i loro punti non sono storicizzati.

Il download ufficiale CLMS è asincrono e richiede una service key personale. Salvare il JSON completo creato nella pagina CLMS in `.secrets/clms-service-key.json`, quindi creare localmente `.env` (entrambi esclusi da `.gitignore`) con **una sola riga**:

```bash
CLMS_SERVICE_KEY_FILE=.secrets/clms-service-key.json
```

Non inserire la service key, token, username o password nel README, nei comandi, nei log o nel versionamento. `scripts/clms_access_token.py` genera in memoria un access token di breve durata e non lo salva. Lanciare prima il controllo del servizio e poi la richiesta:

```bash
python3 scripts/run_downloads.py --check download_copernicus_clc_italy.sh
python3 scripts/run_downloads.py download_copernicus_clc_italy.sh
```

`download_copernicus_clc_italy.sh` richiede due estratti vettoriali in GeoPackage, NUTS `IT`, EPSG:3035: CLC 1990 e CLC 2018. La risposta con i task ID viene conservata in `data/raw/copernicus/clc/requests/`; CLMS invia il collegamento del file pronto via e-mail e il download effettivo avviene manualmente.

Richiesta inviata il 2026-09-01: task CLMS `75776101196`. I file ricevuti sono conservati senza modifiche, insieme a URL stabile e SHA-256:

- `1990/U2000_CLC1990_V2020_20u1.gpkg` — 298.766.336 byte; SHA-256 `00c152f21d7a38233384ccf2362e3cba1575fa3ac25307375a85a4c4282cd1fb`; 115.431 poligoni; importato come `copernicus_clc_1990`.
- `2018/U2018_CLC2018_V2020_20u1.gpkg` — 292.876.288 byte; SHA-256 `523207c522f8140c3e876ceebeb3ee690ee9d4c35d1783a82349a1a9b2ba6a7e`; 112.742 poligoni; importato come `copernicus_clc_2018`.

Entrambi sono già in EPSG:3035. L'importazione è ripetibile con `scripts/import_copernicus_clc_italy.sh`; gli stili di base sono `styles/vectors/copernicus_clc_1990.qml` e `styles/vectors/copernicus_clc_2018.qml`.
