# Nota metodologica

## Scopo e unità di osservazione

L'analisi mostra cosa si può ricavare, con strumenti GIS riproducibili, da un elenco pubblico di localizzazioni attribuite a mega-allevamenti italiani. L'unità di osservazione è **un punto di presenza pubblicato**, distinto soltanto per categoria animale (`Pigs` o `Poultry`). I 2.145 punti analizzabili comprendono 903 presenze suine e 1.242 avicole; un ulteriore record suino con coordinate `[0,0]` è conservato nel layer completo ma escluso da tutte le analisi.

I punti non contengono numero di capi, capacità autorizzata, produzione, emissioni, ragione sociale, data di apertura o relazioni di filiera. Di conseguenza:

- un punto non equivale a un'azienda di dimensione nota né a una quantità uniforme;
- conteggi, densità e KDE misurano la concentrazione delle **localizzazioni**, non carichi zootecnici o ambientali;
- intersezioni e distanze descrivono prossimità spaziali, non impatto, contaminazione, rischio o causalità;
- non è possibile ricostruire commercio, filiere o cambiamento storico degli allevamenti con questo solo dataset.

## Processo analitico

Tutte le misure nazionali sono calcolate in ETRS89 / LAEA Europe (`EPSG:3035`), CRS metrico a pari area. Il record `[0,0]` è l'unico filtro applicato alle presenze. Suini e pollame sono sempre calcolati separatamente.

1. **Griglia regolare:** celle quadrate 10 × 10 km, non ritagliate alla costa; densità = punti/100 km². La scelta è stata confrontata con celle da 5 e 20 km.
2. **Comuni:** intersezione con i confini ISTAT 2025; densità sulla superficie comunale. I risultati dipendono dalla versione e dalla geometria delle unità amministrative (MAUP).
3. **KDE:** kernel quartico senza pesi, bandwidth 20 km, cella 2 km, ritaglio sul territorio nazionale. Il confronto esplorativo ha incluso bandwidth di 10 e 30 km.
4. **CLC:** attribuzione delle classi di terzo livello 1990 e 2018 ai punti attuali. Una lacuna costiera a Rosolina è risolta con la classe più vicina entro 200 m (137,84 m).
5. **Aree protette:** Natura 2000 ed EUAP sono misurate separatamente, senza dissolverle o unirle. Le soglie di 1 e 5 km sono descrittive e non normative.
6. **Idrografia:** il reticolo ISPRA 1:250.000 è usato per uno screening nazionale esplorativo della distanza euclidea, non per misure locali di precisione. L'analisi più accurata resta sospesa fino alla validazione dell'estratto nativo EU-Hydro.

I comandi, i controlli numerici e gli output sono descritti nel [`README.md`](../README.md); gli script sono in [`scripts/`](../scripts/).

## Temporalità e comparabilità

| Fonte | Riferimento temporale | Uso e limite |
|---|---|---|
| Megafarm Europe | snapshot non datato; file locale con timestamp 18 agosto 2026 | distribuzione corrente presunta, non serie storica |
| CLC | 1990 e 2018 | contesto del suolo presso punti oggi noti; nessuna prova che i siti esistessero nei due anni |
| ISTAT | confini al 1° gennaio 2025 | aggregazione contemporanea; soggetta a MAUP e variazioni amministrative |
| ISPRA reticolo | creazione indicata 2004, scala 1:250.000 | screening nazionale esplorativo; non prossimità locale di precisione |
| EUAP | VI elenco, 2010 | strato storico di tutela, non perimetrazione attuale |
| Natura 2000 | trasmissione dicembre 2025, banca dati ufficiale gennaio 2026 | tutela recente, non retroproiettabile al 1990 o 2018 |
| EU-Hydro v1.3 | fonti soprattutto 2006–2012 | analisi non ancora eseguita; infrastruttura di riferimento, non fotografia attuale |

Queste date non sono sincronizzate. Le sovrapposizioni servono a formulare domande e confronti territoriali, non a stabilire una sequenza causale.

## Fonti, licenze e riuso

- **Megafarm Europe:** [pagina sorgente](https://megafarms-europe.netlify.app/index.html). Nel materiale acquisito non sono documentate versione, data di estrazione, licenza o metodologia completa. Prima di pubblicare o ridistribuire il file puntuale occorre ottenere conferma dal produttore; fino ad allora il dataset va trattato come fonte esplorativa.
- **ISTAT 2025:** [confini amministrativi](https://www.istat.it/storage/cartografia/confini_amministrativi/non_generalizzati/2025/Limiti01012025.zip). La pagina [Open Data ISTAT](https://www.istat.it/dati/open-data/) indica CC BY 4.0 con citazione della fonte.
- **ISPRA:** [Reticolo Idrografico Nazionale](https://geodati.gov.it/resource/id/ispra_rm:01Idro250N_DT), scala 1:250.000, creazione 2004. Il metadato RNDT dichiara CC BY 4.0.
- **MASE Natura 2000:** [Schede e cartografie](https://www.mase.gov.it/portale/schede-e-cartografie). Le condizioni specifiche consentono uso non commerciale con citazione, ma vietano distribuzione, adattamento e modifica; sono adottate queste condizioni più restrittive. I vettori non vanno inclusi negli artefatti finali distribuiti.
- **MASE EUAP:** WFS del Geoportale nazionale, VI elenco 2010. Le [note legali del Geoportale](https://gn.mase.gov.it/portale/note-legali) indicano CC BY 4.0 per i dati scaricabili, ferma restando la verifica del metadato dello specifico prodotto.
- **Copernicus CLC ed EU-Hydro:** la [data policy CLMS](https://land.copernicus.eu/en/data-policy) prevede accesso pieno, aperto e gratuito; richiede attribuzione della fonte, dichiarazione delle modifiche e divieto di suggerire approvazione ufficiale dell'Unione europea.

Gli originali, i relativi URL e SHA-256 sono conservati in `data/raw/`. La cartella è una fonte di audit e non implica che ogni originale possa essere ridistribuito pubblicamente.

## Lettura corretta dei risultati

Le mappe mostrano forti concentrazioni territoriali, ma il termine “hotspot” è usato in senso esplorativo: identifica massimi di conteggio o intensità KDE e non l'esito di Getis-Ord, DBSCAN o altro test inferenziale. La diversa distribuzione di suini e pollame può orientare nuove ricerche, ma non permette da sola di spiegare specializzazioni produttive o filiere.

CLC descrive **contesto**, non causalità. La vicinanza alle aree protette descrive **prossimità**, non pressione misurata. Per parlare di impronta ambientale sarebbero necessari almeno consistenza dei capi, gestione dei reflui, emissioni, consumi idrici, autorizzazioni, qualità ambientale e cronologia dei siti.

## Stato della ricerca

I risultati disponibili costituiscono un nucleo dimostrativo riproducibile per l'intervento. Sul reticolo ISPRA è disponibile uno screening idrografico nazionale dichiaratamente esplorativo: entro 1 km dai corsi rappresentati ricadono il 37,1% dei punti suini e il 56,1% di quelli avicoli; il dato non misura contaminazione o connessione di deflusso e può sovrastimare le distanze perché il reticolo omette corsi minori. L'analisi di prossimità più accurata su EU-Hydro resta bloccata: il primo estratto è stato respinto perché privo di geometrie lineari e il task GDB sostitutivo `10074359711` è ancora in coda all'11 settembre 2026. I risultati ISPRA non devono essere presentati come sostituti della futura analisi EU-Hydro.
