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

Non cancellare né sovrascrivere un file in `data/raw/`. Ogni download futuro va in `data/raw/<ente>/<dataset>/<versione>/`; il vettore importato/ritagliato va come nuovo layer in `data/processed/allevamenti.gpkg`. Conservare URL, data di download, licenza, versione e comando di trasformazione in questo README o nella [nota metodologica](docs/nota_metodologica.md).

## Inventario delle fonti

| Fonte | Acquisizione locale | Versione/riferimento | Licenza o condizione documentata |
|---|---:|---|---|
| [Megafarm Europe](https://megafarms-europe.netlify.app/index.html) | file datato 18-08-2026; procedura non registrata | snapshot non datato | non indicata: confermare prima di pubblicare o ridistribuire |
| [ISTAT](https://www.istat.it/storage/cartografia/confini_amministrativi/non_generalizzati/2025/Limiti01012025.zip) | 01-09-2026 | confini al 01-01-2025 | [CC BY 4.0](https://www.istat.it/dati/open-data/) |
| [ISPRA](https://geodati.gov.it/resource/id/ispra_rm:01Idro250N_DT) | 01-09-2026 | reticolo creato nel 2004, scala 1:250.000 | CC BY 4.0 nel metadato RNDT |
| [MASE Natura 2000](https://www.mase.gov.it/portale/schede-e-cartografie) | 01-09-2026 | trasmissione dicembre 2025, ufficiale gennaio 2026 | solo uso non commerciale con citazione; vietate distribuzione, adattamento e modifica |
| MASE EUAP, WFS ufficiale | 01-09-2026 | VI elenco 2010 | [CC BY 4.0](https://gn.mase.gov.it/portale/note-legali), da verificare sul metadato specifico |
| [Copernicus CLC](https://land.copernicus.eu/en/products/corine-land-cover) | 01-09-2026 | 1990 e 2018, V2020_20u1 | [accesso CLMS pieno, aperto e gratuito](https://land.copernicus.eu/en/data-policy), con attribuzione e dichiarazione delle modifiche |
| [Copernicus EU-Hydro](https://land.copernicus.eu/en/products/eu-hydro/eu-hydro-river-network-database) | primo estratto 01-09-2026 | v1.3, soprattutto 2006–2012 | stessa data policy CLMS; estratto valido ancora in attesa |

URL e SHA-256 sono conservati accanto agli originali. Per il file Megafarm il checksum è `efe54661397d83c32f2f95c79e61d4bca71abca14f8d5a99cae8fef1ba7abea3`; licenza, data di estrazione e versione restano lacune della fonte. Le condizioni specifiche Natura 2000 sono più restrittive delle note generali del Geoportale e sono quindi quelle adottate per gli artefatti distribuiti.

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

Il controllo esplorativo ha confrontato bandwidth di 10, 20 e 30 km a cella costante di 2 km. Per i suini i massimi risultano 0,2200, 0,1373 e 0,1080 punti/km², con supporti di 58.608, 113.260 e 159.732 km²; per il pollame 0,2753, 0,1732 e 0,1233, con supporti di 73.400, 136.728 e 190.248 km². I 10 km producono superfici più frammentate, i 30 km fondono maggiormente i cluster; 20 km conserva dettaglio regionale senza isolare quasi ogni singolo punto. La cella da 2 km campiona il bandwidth con dieci pixel.

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

## Prossimità alle aree tutelate

Per ogni punto sono calcolati separatamente numero di poligoni intersecati, distanza minima in metri e codice del sito più vicino per `mase_natura2000_2025` e `mase_euap_2010`. I due regimi non sono dissolti né uniti: un punto può intersecare più siti Natura 2000, mentre le eventuali sovrapposizioni tra Natura 2000 ed EUAP restano due osservazioni distinte. Le sei geometrie EUAP non valide sono riparate solo in memoria durante il calcolo; l'originale non viene modificato.

Output: `data/derived/vectors/megafarms_protected_areas.gpkg`, importato anche in `allevamenti.gpkg` come `megafarms_points_protected_areas` e tabella `megafarms_protected_areas_summary`; il riepilogo è esportato anche in CSV. Tra i suini, 12 punti intersecano Natura 2000 e 4 EUAP; tra il pollame, rispettivamente 14 e 3. Entro 1 km ricadono 88/26 punti suini e 154/35 punti avicoli (Natura 2000/EUAP); entro 5 km 479/237 e 744/233. Le distanze mediane sono 4.792 e 8.173 m per i suini, 4.029 e 10.315 m per il pollame.

```bash
python3 scripts/build_protected_areas_proximity.py
```

Le soglie di 1 e 5 km sono riepiloghi descrittivi, non fasce normative né prove di impatto. Natura 2000 rappresenta la fornitura MASE 2025; EUAP è il VI Elenco del 2010 e va interpretato come strato storico di tutela, non come perimetrazione attuale. Distanza e intersezione non dimostrano da sole pressione, contaminazione o relazione causale.

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

Dati di filiera, macelli, strade, falde vulnerabili e statistiche dei capi non fanno parte del nucleo dimostrativo: richiederebbero definizioni, licenze e temporalità aggiuntive. Gli input elencati sono vettoriali; i due raster KDE sono prodotti derivati e hanno ciascuno il proprio `.qml`.

## Rete idrografica e Natura 2000

Eseguiti tramite l'orchestratore:

```bash
python3 scripts/run_downloads.py --check \
  download_ispra_rete_idrografica.sh download_mase_natura2000_2025.sh download_mase_euap_2010.sh
python3 scripts/run_downloads.py \
  download_ispra_rete_idrografica.sh download_mase_natura2000_2025.sh download_mase_euap_2010.sh
```

- `ispra_reticolo_idrografico`: 61.978 linee, da Reticolo Idrografico Nazionale ISPRA 1:250.000. Originale GeoPackage, URL e checksum: `data/raw/ispra/reticolo_idrografico/1_250000/`.
- `mase_natura2000_2025`: 2.649 poligoni, cartografia ufficiale SIC/ZSC/ZPS MASE trasmessa alla Commissione europea nel dicembre 2025. Archivio originale, URL e checksum: `data/raw/mase/natura2000/2025-12/`.

La Rete Natura 2000 non sostituisce l'**EUAP**: i due regimi possono sovrapporsi, ma non coincidono. L'EUAP è importato come `mase_euap_2010` (871 poligoni) da WFS ufficiale MASE; originale GeoPackage, URL e checksum: `data/raw/mase/euap/2010/`. È il VI Elenco ufficiale (2010, licenza CC BY 4.0): va trattato come strato storico di tutela, non come perimetrazione attuale. I layer restano separati, senza dissolvere le sovrapposizioni.

Entrambi sono importati in EPSG:3035 in `data/processed/allevamenti.gpkg`. La Natura 2000 è contemporanea e non va retroproiettata al 1990; per il confronto CLC documenta esposizione/contesto attuale, non tutela storica.

### Reticolo per le distanze

Il reticolo ISPRA 1:250.000 resta nel progetto come quadro nazionale e di bacino, ma non supporta misure di distanza di 500 m–1 km. Per l'analisi di prova è scelto **EU-Hydro River Network Database v1.3** (EEA/Copernicus): vettoriale, coerente su scala europea, con uso raccomandato fino a 1:30.000 e copertura italiana.

Il controllo geometrico ha respinto l'estratto GeoPackage del task CLMS `29962405257`: il layer `HYDRO/River_Net_l` contiene 95.002 record ma **zero geometrie**, perché la conversione dal formato originale GDB ha prodotto campi geometrici nulli per linee e punti. L'archivio originale, URL e checksum restano in `data/raw/copernicus/eu_hydro/v1.3_2006-2012/` per audit; i 20 layer importati sono stati rimossi da `allevamenti.gpkg` per impedirne l'uso accidentale.

L'11 settembre 2026 è stato richiesto un nuovo estratto nel formato nativo **GDB**, task CLMS `10074359711`, attualmente in coda. `scripts/import_copernicus_euhydro_italy.sh` ora accetta solo il GDB e interrompe l'importazione se `River_Net_l` non contiene geometrie lineari. Raccolta e importazione saranno ripetibili con `scripts/collect_copernicus_euhydro_italy.sh` quando il task sarà pronto.

EU-Hydro deriva soprattutto da fonti 2006–2012: descrive un'infrastruttura idrografica di riferimento, non lo stato attuale. Nei futuri approfondimenti sui cluster si potranno sostituire o verificare le distanze con i reticoli ufficiali regionali, normalmente più dettagliati ma non omogenei per data, scala, attributi e licenza. Non fonderli in un unico reticolo nazionale senza un controllo di armonizzazione.

Il piano operativo aggiornato è in [`TODO.md`](TODO.md).

## QGIS e stili

Aprire `qgis/allevamenti.qgs`, in EPSG:3035. Il progetto contiene 19 layer organizzati in otto gruppi coerenti con il processo: presenze e attribuzioni, densità su griglia, densità comunali, densità kernel, aree protette e idrografia, copertura del suolo, confini amministrativi e tabelle di sintesi. All'apertura sono visibili solo le presenze categorizzate (rosso = suini, blu = pollame) e i confini regionali, per evitare sovrapposizioni ambigue.

Tutti i 15 layer vettoriali spaziali caricati hanno un `.qml` in `styles/vectors/`; le due tabelle senza geometria non richiedono simbologia. I raster KDE hanno stili confrontabili in `styles/rasters/`, con intervalli comuni e unità in punti/km². EU-Hydro sarà aggiunto solo dopo la disponibilità e la validazione dell'estratto GDB.

Il gestore layout contiene tre tavole A4 con titolo, legenda, scala, fonti, data e avvertenza interpretativa: `01 — Distribuzione nazionale` in verticale; `02 — Hotspot suini — Pianura Padana centrale` e `03 — Hotspot pollame — Pianura Padana centro-orientale` in orizzontale. Le finestre di dettaglio, rispettivamente `4230000,2370000,4450000,2525000` e `4310000,2330000,4590000,2510000` in EPSG:3035, includono i massimi osservati nelle griglie da 10 km. In entrambe restano visibili i punti di suini e pollame per confronto, mentre lo sfondo KDE è specifico della categoria indicata nel titolo. “Hotspot” descrive qui un massimo esplorativo di densità, non l'esito di un test statistico di clustering.

Il progetto conserva percorsi relativi ed è aggiornabile, a QGIS chiuso, con:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=/usr/share/qgis/python \
  python3 scripts/build_qgis_project.py
```

## Installazione

Su Ubuntu/Debian:

```bash
sudo apt update
sudo apt install qgis qgis-plugin-grass gdal-bin
qgis --version
ogr2ogr --version
```

Il progetto e le esportazioni sono stati validati con QGIS 4.2.2 e GDAL 3.13. Per eseguire gli script QGIS servono i binding Python della stessa distribuzione; il file `.qgs` già incluso può essere aperto senza eseguire Python.

## Artefatti finali

La [nota metodologica](docs/nota_metodologica.md) raccoglie assunzioni, limiti temporali, condizioni di riuso e regole d'interpretazione. Le tre tavole QGIS sono esportate a 200 dpi in `outputs/figures/`. Le quattro tabelle in `outputs/tables/` sono CSV UTF-8 con intestazione, separatore virgola e punto come separatore decimale; `animal` mantiene i valori sorgente `Pigs` e `Poultry`. Quando si apre un CSV in un foglio elettronico, `municipality_code` va importato come testo per non perdere gli zeri iniziali.

### `table_01_summary.csv` — quadro comparativo

Una riga per categoria animale. Riunisce indicatori con unità diverse:

- `total_points`: presenze analizzabili;
- `occupied_grid_cells` e `max_points_10km_cell`: celle da 10 km con almeno un punto e massimo conteggio in una cella;
- `max_grid_density_km2`: massimo della griglia, cioè conteggio/100 km²;
- `occupied_municipalities` e `max_points_municipality`: comuni con almeno una presenza e massimo conteggio comunale;
- `clc_changed_count` e `clc_changed_percent`: punti la cui classe CLC di **terzo livello** differisce tra 1990 e 2018;
- `kde_max_points_km2`: massimo del raster KDE con bandwidth 20 km.

**Grafico consigliato:** una scheda numerica per i totali, affiancata da piccoli grafici a barre o dot plot separati per conteggi, percentuali e densità. Suini e pollame vanno accostati in ogni pannello. Non usare un unico asse, un radar chart o sommare gli indicatori: scale e significati non sono omogenei. Il massimo KDE non è direttamente intercambiabile con la densità della griglia, perché deriva da uno smoothing continuo.

### `table_02_protected_areas.csv` — prossimità cumulativa

Una riga per combinazione categoria animale × fonte di tutela (`natura2000` o `euap`). `inside_count` indica l'intersezione; `within_1km` e `within_5km` includono cumulativamente anche i punti più vicini e quelli interni. Le colonne `_percent` usano `total_points` della categoria come denominatore; `median_m` è la mediana delle distanze minime.

**Grafico consigliato:** un dot plot o line chart cumulativo con soglie `dentro`, `≤1 km`, `≤5 km` sull'asse x e percentuale sull'asse y, in pannelli separati per Natura 2000 ed EUAP e con una linea per specie. La mediana, espressa in metri, va mostrata in un piccolo pannello separato. Non usare barre impilate: le classi sono annidate e verrebbero erroneamente percepite come parti indipendenti. Le soglie descrivono prossimità, non fasce normative o impatto.

### `table_03_top_municipalities.csv` — graduatorie comunali

Contiene i primi dieci comuni per `point_count`, separatamente per specie. `rank_by_point_count` è quindi una graduatoria per conteggio, non per densità; `density_km2` aggiunge il rapporto con l'area comunale e può cambiare molto con dimensione e forma del comune.

**Grafico consigliato:** due bar chart orizzontali, uno per specie, ordinati per `point_count` e con la stessa scala. Se si vuole discutere l'effetto dell'area, aggiungere uno scatter plot `point_count` × `density_km2` con etichette dei comuni, invece di usare un doppio asse. Presentare sempre la graduatoria insieme alla mappa e ricordare il MAUP: i confini ISTAT 2025 influenzano conteggi e densità.

### `table_04_clc_level1_transitions.csv` — contesto del suolo

Aggrega i punti per macroclasse CLC 1990 (`clc_level1_1990`) e 2018 (`clc_level1_2018`), separatamente per specie. `share_percent` è la quota sul totale della specie. Questa tabella usa il **primo livello** CLC; perciò non deve riprodurre necessariamente i 65 cambiamenti suini e 179 avicoli di `table_01_summary.csv`, calcolati al terzo livello: una transizione può cambiare sottoclasse restando nella stessa macroclasse.

**Grafico consigliato:** una heatmap di transizione per specie, con classe 1990 sulle righe, classe 2018 sulle colonne e colore proporzionale a `share_percent`; rende subito distinguibili permanenze sulla diagonale e cambiamenti fuori diagonale. Un diagramma alluvionale/Sankey può essere usato come visualizzazione narrativa secondaria, ma i flussi minori rischiano di scomparire dietro la prevalenza delle superfici agricole. Le transizioni riguardano il contesto dei punti oggi noti, non la storia o l'effetto causale degli allevamenti.

A QGIS chiuso, tutti gli artefatti finali si rigenerano con:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=/usr/share/qgis/python \
  python3 scripts/build_final_outputs.py
```

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
