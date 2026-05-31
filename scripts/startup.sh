#!/bin/bash

echo "Starting Social Exposure Analyzer on Azure App Service..."

# Azure App Service mappa dinamicamente la porta 80 o 8080 sulla variabile d'ambiente $PORT
# Uvicorn (o Gunicorn) deve mettersi in ascolto su questa porta esatta.
PORT=${PORT:-8000}

# Installazione delle dipendenze di spacy (il modello linguistico italiano che non è in requirements.txt standard)
python -m spacy download it_core_news_lg || echo "Errore durante il download del modello spaCy"

# Esecuzione delle migrazioni del database (Alembic su PostgreSQL/SQLite)
echo "Esecuzione migrazioni database..."
python -m alembic upgrade head || echo "Errore durante le migrazioni Alembic"

# Avvio dell'applicazione tramite Uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port $PORT --proxy-headers
