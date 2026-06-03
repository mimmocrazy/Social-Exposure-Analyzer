# Usa un'immagine base ufficiale Python (compatta)
FROM python:3.11-slim

# Imposta variabili d'ambiente per Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installa dipendenze di sistema richieste da psycopg2 e spacy
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crea e imposta la working directory
WORKDIR /app

# Installa PyTorch versione CPU per risparmiare 2.5GB di spazio ed evitare crash su Azure Free
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copia i requirement e installali
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Scarica il modello linguistico di SpaCy in italiano in anticipo per non rallentare l'avvio
RUN python -m spacy download it_core_news_sm

# Scarica i modelli OCR in anticipo per evitare latenza e log superflui
RUN python -c "import easyocr; easyocr.Reader(['it', 'en'], gpu=False, verbose=False)"

# Copia il codice del backend
COPY backend/ ./backend/

# Esponi la porta 80 (standard Azure App Service)
EXPOSE 80

# Avvia FastAPI tramite Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
