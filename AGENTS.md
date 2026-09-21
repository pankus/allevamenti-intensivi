# Istruzioni per agenti

Prima di modificare analisi o dati, leggi `README.md` e `PROJECT.md`.

- Conserva ogni download originale in `data/raw/<ente>/<dataset>/<versione>/` con URL, data, licenza e versione documentati.
- Importa ogni vettore usato in `data/processed/allevamenti.gpkg`; non modificare gli originali.
- Usa EPSG:3035 per analisi metriche nazionali/europee e salva gli output in `data/derived/vectors/` o `data/derived/rasters/`.
- Ogni layer QGIS ha uno stile `.qml` in `styles/vectors/` o `styles/rasters/`; crea il `.qml` del raster nello stesso cambiamento che crea il raster.
- Mantieni filtri, assunzioni, controlli qualità e comandi riproducibili in `README.md`.
- Ogni `scripts/download_*.sh` dichiara una sola riga `URL="https://..."` e viene avviato da `scripts/run_downloads.py`, che controlla il link prima del download.
- Tratta le localizzazioni Megafarm come punti di presenza, non come misure di capi, emissioni o produzione.
- Prima di creare o modificare slide, leggi “Sistema grafico delle slide” in `README.md`: applica la sequenza dato→sintesi e i margini obbligatori “Fonti dati” e “Tecnica”; rigenera prima gli eventuali dati derivati indicati lì, poi esegui `scripts/build_slides.py`.
