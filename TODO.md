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
- [x] Usare Copernicus DEM GLO-30 per attribuire quota e classe geomorfologica ai punti degli allevamenti. Conservati i tile originali in `data/raw/copernicus/dem/glo30/tiles/`; uniti i tile e poi riproiettato un unico DEM EPSG:3035 a 100 m prima di `r.geomorphon`; salvati output puntuali/tabellari in `data/derived/vectors/`, creati i relativi `.qml`. Interpretare quota/geomorfologia come contesto fisico, non come impatto o causalità.

### 2.1 Domande storiche e passaggi successivi

**Domanda storica principale**

> La geografia attuale dei mega-allevamenti è il risultato di una specializzazione territoriale di lungo periodo oppure di una riconfigurazione recente della zootecnia italiana?

Le localizzazioni Megafarm non sono datate: con i dati attuali questa domanda non è ancora pienamente verificabile.

**Domanda alla quale possiamo già rispondere**

> Quali paesaggi italiani ospitano oggi le maggiori concentrazioni di mega-allevamenti e come sono cambiati, tra 1990 e 2018, i contesti territoriali nei quali queste localizzazioni ricadono?

Le analisi già prodotte permettono di descrivere:

- la diversa geografia di suini e pollame;
- la concentrazione rispetto a pianure, basse quote e superfici agricole;
- le transizioni CLC nei luoghi in cui ricadono i punti attuali;
- la prossimità ad aree tutelate e, con i limiti documentati, ai corsi d'acqua;
- i territori che emergono stabilmente usando comuni, griglia regolare e KDE.

Il risultato va formulato come **selettività e territorializzazione** delle localizzazioni attuali: gli allevamenti non sono distribuiti casualmente, ma ricorrono in determinati paesaggi. Non è invece possibile affermare che abbiano causato le trasformazioni CLC o misurare produzione, emissioni e impatto ambientale.

**Ipotesi storica da verificare**

> L'intensificazione non ha semplicemente aumentato la produzione, ma ha concentrato progressivamente aziende e possibili pressioni territoriali in pochi distretti specializzati.

**Passaggi successivi**

- [ ] Reperire una serie storica dei censimenti agricoli ISTAT, dagli anni Sessanta in avanti, con numero di aziende e capi per specie alla scala territoriale più dettagliata e confrontabile disponibile.
- [ ] Verificare continuità di definizioni, confini amministrativi e unità di rilevazione prima di costruire confronti temporali.
- [ ] Ricostruire per provincia o comune la variazione del numero di aziende, dei capi e della dimensione media aziendale, tenendo distinti suini e pollame.
- [ ] Confrontare le traiettorie storiche con gli hotspot Megafarm attuali per distinguere persistenza di antichi distretti, concentrazione recente e aree in declino.
- [ ] Selezionare uno o due casi di studio emersi dal confronto quantitativo e verificarli con fonti storiche locali, pianificazione, fotografie aeree e documentazione d'impresa o amministrativa.
- [ ] Usare l'analisi digitale per scegliere territori, periodi e fonti da approfondire, non per retrodatare automaticamente le localizzazioni attuali.

## 3. QGIS e stili

- [x] Aggiungere al progetto QGIS punti, confini ISTAT, idrografia ISPRA, EUAP, Natura 2000, CLC e output derivati. Dividi in gruppi in modo organico sulla base del processo realizzato
- [x] Creare uno stile `.qml` per ogni vettore caricato o scarica gli stili per i dati di base ove possibile.
- [x] Creare e salvare accanto a ogni raster il rispettivo `.qml` con palette, intervalli e unità leggibili.
- [x] Comporre una mappa nazionale e due mappe di dettaglio sui cluster, con titolo, legenda, scala, fonte e data.

## 4. Metodo e consegna

- [x] Aggiornare README con ogni comando, filtro e fonte realmente usati.
- [x] Scrivere una nota metodologica: punti = presenza, non capi/emissioni; CLC = contesto, non causalità; limiti temporali dei layer.
- [x] Preparare tabelle e figure finali riproducibili per l'intervento.

## Nota sul reticolo idrografico

**Scelta proposta: EU-Hydro v1.3**. È più adatto alla prossimità rispetto al reticolo ISPRA 1:250.000, ha copertura europea coerente e un uso raccomandato fino a scala 1:30.000. È però riferito soprattutto al 2006–2012: va descritto come infrastruttura idrografica di riferimento, non come fotografia attuale.

Alternativa per uno studio locale molto preciso: usare i reticoli ufficiali regionali nei soli territori hotspot. OpenStreetMap è un controllo esplorativo possibile, ma non il layer principale del paper per la sua disomogeneità e licenza ODbL.

Fonti: [EU-Hydro EEA/Copernicus](https://land.copernicus.eu/en/products/eu-hydro/eu-hydro-river-network-database), [guida EU-Hydro](https://land.copernicus.eu/en/technical-library/eu-hydro_user_guide/%40%40download/file), [reticolo ISPRA](https://inspire-geoportal.ec.europa.eu/srv/api/records/ispra_rm:01Idro250N_DT).
