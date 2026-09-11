# Domanda scientifica
Devo presentare ad un paper ad un congresso di Storia dell'ambiente. Io sono un esperto di digital humanities e vorrai mostrare ai colleghi di storia ambientale quali sono i vantaggi di usare moderni sistemi di analisi dei dati per la ricerca.
Un tema che verrà discusso al congresso è l'allevamento intensivo. Io pensavo di presentare una cosa su questo argomento partendo dai dati che si possono prendere da questo sito, in particolare quelli sull'italia: https://megafarms-europe.netlify.app/index.html

I dati sono di questo tipo:
POINT(11.916 42.4715)	Italy	Pigs
POINT(11.8539 42.7511)	Italy	Pigs
POINT(12.2779 42.4636)	Italy	Pigs
POINT(12.1706 42.516)	Italy	Pigs
POINT(12.4812 42.6206)	Italy	Pigs
POINT(12.5775 43.3568)	Italy	Pigs
POINT(12.6328 42.8555)	Italy	Pigs
POINT(12.9581 43.5858)	Italy	Pigs
POINT(12.3368 42.8401)	Italy	Pigs
POINT(12.3501 42.9881)	Italy	Pigs
POINT(12.2889 42.9806)	Italy	Pigs
POINT(12.3068 42.9781)	Italy	Pigs
POINT(12.2927 42.9679)	Italy	Pigs
POINT(12.5004 42.7932)	Italy	Pigs
POINT(12.3933 42.7531)	Italy	Pigs
POINT(12.375911 42.756133)	Italy	Pigs

Le domande sono:

1. Una volta che ho recuperato i dati come mi consigli di utilizzarli per uno studio sul tema ma in cui l'approccio digitale è determinante?
2. Altre idee?

---

## Prima risposta

Ottima idea di presentazione: puoi mostrare come le DH possano offrire nuove prospettive alla storia ambientale, e il tema dell'allevamento intensivo è perfetto perché tocca economia, territorio, paesaggio e ambiente.

### 1. Come utilizzare i dati per uno studio in cui l'approccio digitale è determinante

I dati che hai sono georeferenziati (coordinate puntuali) e tematici (tipo di allevamento: suini, bovini, pollame, ecc.).

Puoi:

#### a. Creare mappe tematiche e di densità
- Trasforma i punti in una **mappa di densità** (kernel density) per mostrare le aree di concentrazione dell'allevamento intensivo in Italia.
- Confronta la distribuzione con layer ambientali: bacini idrici, aree protette, reti fluviali, uso del suolo (CORINE Land Cover), rete dei trasporti, distanza dai centri urbani o dai porti.
- Questo evidenzia **pattern territoriali** e possibili **pressioni ambientali** (es. vicinanza a corsi d'acqua o aree vulnerabili).

#### b. Analisi temporale (se hai date o puoi incrociare con altre fonti)
- Se i dati non hanno una data, puoi comunque mostrare la **distribuzione attuale** e confrontarla con fonti storiche (censimenti agrari, mappe catastali, foto aeree storiche).
- Potresti ricostruire l'evoluzione della zootecnia intensiva dagli anni '60 a oggi usando dati ISTAT, ministeriali o regionali, e incrociarli con la localizzazione attuale.

#### c. Analisi spaziale e modellizzazione
- Usa strumenti di **spatial analysis** (QGIS, Python con geopandas, R con sf) per:
  - calcolare la distanza da corpi idrici o aree urbane;
  - identificare cluster (hotspot) con metodi statistici (Getis-Ord, DBSCAN);
  - stimare la pressione ambientale (ad esempio, carico di azoto per km²).
- Puoi anche calcolare l'accessibilità: vicinanza a strade, porti, macelli, mangimifici.

#### d. Analisi testuale e documentale
- Integra i dati geografici con **fonti testuali** (normative, rapporti ambientali, articoli di stampa) usando strumenti di **text mining**.
- Ad esempio, analizza come è cambiata la percezione pubblica dell'allevamento intensivo, o come la normativa ha reagito alla crescita dei mega-allevamenti.

### 2. Altre idee per rafforzare l'approccio digitale

#### a. WebGIS interattivo
- Costruisci una **mappa interattiva** (con Leaflet, Mapbox, o QGIS2Web) in cui l'utente può esplorare i mega-allevamenti per tipo, regione, dimensione, e confrontarli con indicatori ambientali.
- Mostra la mappa durante il congresso: l'impatto visivo è immediato e potente.

#### b. Analisi di rete
- Crea una **rete** di connessioni tra allevamenti, macelli, mangimifici, porti e aziende di trasformazione.
- Puoi mostrare come il sistema zootecnico intensivo sia parte di una filiera globale e interconnessa.

#### c. Storymap
- Prepara una **storymap** (con ArcGIS StoryMaps o Knight Lab) che racconti l'evoluzione dell'allevamento intensivo in Italia, unendo dati, mappe, immagini storiche, interviste e fonti d'archivio.
- Unisce il rigore scientifico alla narrazione, rendendo il tuo intervento accessibile anche a un pubblico non tecnico.

#### d. Confronto europeo
- Usa i dati di altri paesi europei (il sito ne contiene) per un **confronto spaziale** tra modelli nazionali: ad esempio, concentrazione in Pianura Padana vs Catalogna vs Paesi Bassi.
- Analizza le differenze normative, economiche e ambientali.

#### e. Digital Public History
- Mostra come questi strumenti possano essere usati per coinvolgere il pubblico: mappe partecipative, raccolta di testimonianze, monitoraggio civico.
- Puoi citare progetti già esistenti (es. iniziative di citizen science sulla qualità dell'aria o dell'acqua nelle zone ad alta densità zootecnica).

Se vuoi, posso aiutarti a impostare una bozza dell'abstract o della struttura della presentazione.

---

## Osservazione successiva

I dati sono molto scarni. Ho solo il punto, la nazione (ridondante) e il tipo di allevamento: maiali o pollame. Ma cosa mi dice realmente la loro distribuzione sul territorio? Un pollo prodotto in Italia oggi può tranquillamente essere commercializzato in Germania. Non conosco nemmeno i nomi delle ditte e per quale grande distributore producono. Forse possiamo limitarci a vedere l'impronta ambientale sul territorio?

---

## Seconda risposta

Hai perfettamente ragione: con soli tre campi (coordinate, nazione, tipo di animale) non puoi fare inferenze economiche, commerciali o di filiera. Ma quei dati **possono comunque dirti molto sull'impronta ambientale e territoriale**, ed è lì che l'approccio digitale diventa determinante.

Il punto non è "chi produce per chi", ma **dove si concentra la pressione ambientale** e **quali territori ne sono più esposti**.

### 1. Cosa puoi davvero mostrare con questi dati

#### a. La geografia della pressione zootecnica
Anche senza nomi o volumi, la **densità spaziale** dei punti ti dice dove si concentra l'allevamento intensivo.

Puoi:
- calcolare la **densità kernel** per suini e pollame separatamente;
- evidenziare le **aree di cluster** (es. Pianura Padana, alcune zone della Lombardia, Emilia, Veneto, Piemonte);
- confrontare la distribuzione con i **confini amministrativi** (comuni, province, regioni) per individuare i territori più esposti.

Questo è già un risultato significativo per uno storico dell'ambiente: mostra **dove il fenomeno è territorialmente rilevante**.

#### b. Sovrapposizione con elementi ambientali sensibili
Puoi incrociare i punti con layer ambientali pubblici (ISTAT, ISPRA, Copernicus, OpenStreetMap):
- **rete idrografica** (fiumi, canali, laghi): quanti allevamenti sono entro 500 m o 1 km da un corpo idrico?
- **aree protette** (parchi, SIC, ZPS): quanti allevamenti ricadono dentro o vicino a zone di tutela?
- **uso del suolo** (CORINE Land Cover): in che contesto si trovano? Aree agricole intensive? Aree periurbane?
- **acquiferi vulnerabili** (es. alta pianura padana): la vicinanza a falde vulnerabili è un indicatore chiave per l'inquinamento da nitrati.

Questo ti permette di costruire un **indice di pressione ambientale** semplice ma efficace.

#### c. Analisi della prossimità tra allevamenti
Puoi calcolare la **distanza media tra allevamenti** della stessa tipologia o tra tipologie diverse.

Se i punti sono molto vicini tra loro, questo indica:
- elevata concentrazione territoriale;
- possibile **saturazione ambientale** (carico di reflui, odori, emissioni);
- competizione per risorse (acqua, suolo).

Puoi anche calcolare il **numero di allevamenti per km²** per unità amministrativa (comune o provincia) e creare una **classifica dei territori più densamente allevati**.

#### d. Confronto suini vs pollame
La distribuzione spaziale delle due categorie può essere diversa:
- i **suini** sono spesso legati a territori con forte produzione di mais (alimentazione) e a distretti di trasformazione (prosciutti, salumi);
- il **pollame** può essere più diffuso in aree periurbane o lungo direttrici di trasporto.

Mostrare queste differenze è già un risultato interessante: evidenzia **logiche territoriali diverse** all'interno dello stesso fenomeno.

### 2. Come rendere l'approccio digitale "determinante"

Anche con dati scarni, puoi dimostrare che:

- **L'analisi spaziale** trasforma un elenco di punti in **conoscenza territoriale**.
- **La sovrapposizione con layer ambientali** permette di formulare ipotesi di impatto senza bisogno di dati aziendali riservati.
- **La modellizzazione geografica** consente di individuare aree di criticità anche in assenza di informazioni sui volumi produttivi.

Puoi dire esplicitamente:  
> "Non sappiamo quanti capi ci siano in ogni allevamento, ma sappiamo dove sono. E la posizione, da sola, ci dice già molto sulla pressione che il territorio subisce."

### 3. Possibile struttura dell'intervento

1. **Introduzione**: cosa sono i "megafarms" e perché sono un problema ambientale e storiografico.
2. **Dati e metodo**: descrizione del dataset, limiti, strumenti usati (QGIS, Python, R).
3. **Risultati**:
   - mappa di densità nazionale;
   - hotspot regionali;
   - prossimità a fiumi, aree protette, acquiferi;
   - confronto suini/pollame.
4. **Interpretazione storica**: cosa ci dice questa geografia sull'evoluzione dell'allevamento intensivo in Italia? (es. continuità con la tradizione zootecnica padana, ma anche rottura con i modelli estensivi del passato).
5. **Conclusioni**: limiti e potenzialità dell'approccio digitale per la storia ambientale.

Se vuoi, posso aiutarti a:
- costruire una **mappa esplorativa** con i dati reali;
- calcolare alcune **metriche spaziali** (densità, distanza da fiumi, ecc.);
- preparare una **bozza di abstract** per il congresso.
