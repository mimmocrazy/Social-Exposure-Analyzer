# Social Engineering Risk Assessment Platform

## 1. Architettura di Sistema
Applicazione cloud-based strutturata in tre layer isolati, progettata per il deploy su **Microsoft Azure App Service**. Il sistema valuta l'esposizione di PII (Personally Identifiable Information) sui social network e calcola il rischio di impersonificazione/phishing.

### 1.1 Compartimentazione Repository
- `/backend`: Core logico, API RESTful, integrazione AI/NLP/OCR e persistenza dati.
- `/frontend`: Interfaccia utente reattiva per l'inserimento URL e la visualizzazione del Risk Report.
- `/tests`: Suite di test isolata (Unit & Integration) per garantire la robustezza del codice.

### 1.2 Tech Stack
- **Backend:** Python 3.11+, FastAPI.
- **Database:** SQLite (ambiente dev/demo).
- **Estrazione PII (NLP):** Microsoft Presidio / spaCy.
- **Estrazione Testo da Immagini (OCR):** Tesseract / EasyOCR.
- **LLM / Generazione Report:** Google Gemini Pro.
- **Scraping:** Librerie native locali (Playwright, BeautifulSoup).
- **Testing:** Pytest, HTTPX, pytest-cov.
- **Infrastruttura:** Microsoft Azure App Service.

---

## 2. Roadmap e Micro-Tasks

### Fase 1: Backend Foundation
- [ ] Inizializzazione progetto FastAPI e struttura directory.
- [ ] Configurazione Database e modelli ORM.
- [ ] Creazione endpoint principale di ingestion (`/api/v1/analyze`).
- [ ] Setup sistema di logging centralizzato e gestione errori.

### Fase 2: Tests - Backend Foundation
- [ ] Setup Pytest (`pytest.ini`, `conftest.py`).
- [ ] Unit tests per operazioni CRUD e validazione input endpoint.

### Fase 3: AI & NLP Core Integration
- [ ] Sviluppo modulo **Scraping** (Librerie native: Playwright/BeautifulSoup).
- [ ] Sviluppo modulo **NLP** (Estrazione PII con Presidio/spaCy).
- [ ] Sviluppo modulo **OCR** (Analisi immagini con Tesseract/EasyOCR).
- [ ] Sviluppo modulo **Risk Engine** (Prompting Gemini Pro per Risk Score e Report).

### Fase 4: Tests - AI & Core
- [ ] Mock testing per il servizio di scraping locale.
- [ ] Integration testing per l'estrazione PII e OCR.
- [ ] Mock testing per le risposte di Gemini Pro.

### Fase 5: Frontend Development
- [ ] Setup framework frontend.
- [ ] Sviluppo UI di input (URL social).
- [ ] Sviluppo Dashboard Risultati (Risk Score, PII esposte, Report AI).
- [ ] Integrazione API Frontend-Backend.

### Fase 6: Azure Deployment & Documentazione
- [ ] Configurazione variabili d'ambiente per Azure.
- [ ] Deploy su Azure App Service.
- [ ] Stesura relazione finale (inclusiva di trasparenza AI come da `AI_JOURNAL.md`).
