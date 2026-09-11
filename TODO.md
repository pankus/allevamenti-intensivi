# TODO analisi e visualizzazione

## 1. Completare gli input

- [x] Completato il task CLMS `75776101196`: scaricati manualmente gli estratti Italia CLC 1990 e 2018, conservati in `data/raw/copernicus/clc/<anno>/` e importati in `data/processed/allevamenti.gpkg`.
- [x] Registrati in `README.md` nomi, dimensioni, checksum, URL sorgente, layer effettivi e comando d'importazione dei due file.
- [ ] Sostituire l'estratto EU-Hydro del task `29962405257`, respinto perché `River_Net_l` ha 95.002 record ma geometrie tutte nulle. Richiesto il formato nativo GDB con task `10074359711` (in coda); dopo il download validare e importare `euhydro_hydro_river_net_l`, mantenendolo distinto dal reticolo ISPRA 1:250.000.

## 2. Analisi

- [x] Creare una griglia regolare nazionale in EPSG:3035 e calcolare, separatamente per suini e pollame, numero di punti e densità per km².
- [x] Calcolare gli stessi conteggi per comune; dichiarare la dipendenza dalle unità amministrative (MAUP).
- [x] Generare due raster di densità kernel, uno per suini e uno per pollame; scegliere e documentare cella e bandwidth dopo un controllo esplorativo.
- [x] Attribuire a ciascun punto la classe CLC 1990 e CLC 2018 e produrre una tabella delle transizioni di copertura del suolo attorno ai punti attuali.
- [x] Calcolare intersezione e distanza da Natura 2000 ed EUAP, senza unire i due layer e senza interpretare l'EUAP 2010 come tutela attuale.
- [ ] Solo dopo il download EU-Hydro: calcolare distanze dai corsi d'acqua. Escludere i risultati se il dettaglio della sorgente non regge la soglia scelta.

## 3. QGIS e stili

- [x] Aggiungere al progetto QGIS punti, confini ISTAT, idrografia ISPRA, EUAP, Natura 2000, CLC e output derivati. Dividi in gruppi in modo organico sulla base del processo realizzato
- [x] Creare uno stile `.qml` per ogni vettore caricato o scarica gli stili per i dati di base ove possibile.
- [x] Creare e salvare accanto a ogni raster il rispettivo `.qml` con palette, intervalli e unità leggibili.
- [x] Comporre una mappa nazionale e due mappe di dettaglio sui cluster, con titolo, legenda, scala, fonte e data.

## 4. Metodo e consegna

- [ ] Aggiornare README con ogni comando, filtro e fonte realmente usati.
- [ ] Scrivere una nota metodologica: punti = presenza, non capi/emissioni; CLC = contesto, non causalità; limiti temporali dei layer.
- [ ] Preparare tabelle e figure finali riproducibili per l'intervento.

## Nota sul reticolo idrografico

**Scelta proposta: EU-Hydro v1.3**. È più adatto alla prossimità rispetto al reticolo ISPRA 1:250.000, ha copertura europea coerente e un uso raccomandato fino a scala 1:30.000. È però riferito soprattutto al 2006–2012: va descritto come infrastruttura idrografica di riferimento, non come fotografia attuale.

Alternativa per uno studio locale molto preciso: usare i reticoli ufficiali regionali nei soli territori hotspot. OpenStreetMap è un controllo esplorativo possibile, ma non il layer principale del paper per la sua disomogeneità e licenza ODbL.

Fonti: [EU-Hydro EEA/Copernicus](https://land.copernicus.eu/en/products/eu-hydro/eu-hydro-river-network-database), [guida EU-Hydro](https://land.copernicus.eu/en/technical-library/eu-hydro_user_guide/%40%40download/file), [reticolo ISPRA](https://inspire-geoportal.ec.europa.eu/srv/api/records/ispra_rm:01Idro250N_DT).
