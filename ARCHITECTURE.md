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
- [x] Inizializzazione progetto FastAPI e struttura directory.
- [x] Configurazione Database e modelli ORM.
- [x] Creazione endpoint principale di ingestion (`/api/v1/analyze`).
- [x] Setup sistema di logging centralizzato e gestione errori.
- [x] Continuous Security Audit (SAST/SCA & Report Update).
- [x] Continuous Security Audit (Manuale).

### Phase 3: AI-Driven PII Extraction & Risk Assessment (Gemini Pro/Flash)
- Abbandono della libreria NLP statistica (SpaCy) in favore dell'uso di Google Gemini 2.5 Flash.
- **Workflow**: 
  - Il testo grezzo unito (scraped metadata + OSINT leaks) viene inviato interamente al modello LLM.
  - L'LLM restituisce in modalità **Structured Outputs** (JSON nativo) sia le PII estratte (Entity) sia il `RiskReport`.
- Lo storage nel database e l'invio alla Dashboard avvengono in formato strutturato, garantendo affidabilità e assenza di allucinazioni grazie alla restrizione dello schema JSON.
- [x] Sviluppo modulo **OCR** (Analisi immagini con Tesseract/EasyOCR).
- [x] Sviluppo modulo **Risk Engine** (Prompting Gemini Pro per Risk Score e Report).

### Fase 4: Tests - AI & Core
- [x] Mock testing per il servizio di scraping locale.
- [x] Integration testing per l'estrazione PII e OCR.
- [x] Mock testing per le risposte di Gemini Pro.

### Fase 5: Scalabilità & Orchestration
- [x] Load Testing e Scalabilità (Locust, System Design).
- [x] Sviluppo Test Orchestrator e Reportistica HTML.
- [x] **CONTINUOUS**: Master Orchestrator configurato (`scripts/full_system_check.py`).

### Fase 5.1: Frontend Development
- [x] Setup framework frontend (Vite, Tailwind, Tremor).
- [x] Sviluppo UI di input (SearchForm).
- [x] Sviluppo Dashboard Risultati (Risk Score, PII esposte, Report AI).
- [x] Integrazione API Frontend-Backend (Polling).

### Fase 5.5: Master Test Orchestrator
- [x] Setup Master Test Suite (Validation Gate API, DoS, Frontend).

### Fase 5.8: OSINT Core & Risk Sub-scoring
- [x] Installazione Dipendenze (Holehe).
- [x] Aggiornamento Modelli & Schema API (Risk Sub-scoring): Aggiornamento `backend/schemas.py` per i toggle OSINT e `backend/models/risk.py` per `RiskSubScores` (Identity, Network, Routine).
- [x] Backend Integrazione Moduli OSINT Core: Implementazione `holehe_adapter.py` e aggiornamento `scraper.py` per Instagram Deep Scan (sessionid) e switch DDG.
- [x] Prompt Engineering LLM: Aggiornamento `backend/services/risk_engine.py` per il mapping dei Risk Sub-scores e parsing dei risultati Holehe.
- [x] Frontend Rivoluzione Dashboard: Pannello "Sensori OSINT" nella home (toggles UI) e Data Visualization visiva con Progress Bars Tremor per le sub-metrizzazioni del rischio.
- [x] Documentazione Finale: Aggiornamento `AI_JOURNAL.md` e sync con `ARCHITECTURE.md`.

### Fase 5.9: Trasparenza UI/UX High-Signal, Routine e Mappatura Sensori OSINT
- [x] Modelli & Estrazione Source PII: Estensione del modello `Entity` in `backend/models/risk.py` per estrarre la fonte (`source`) di ciascuna informazione tramite Structured Outputs di Gemini.
- [x] Anti-Login Wall Optimization: Aggiornamento logica di `backend/services/scraper.py` per saltare lo standard scraping anonimo su Instagram quando il Deep Scan va a buon fine, evitando allucinazioni e warning.
- [x] Tooltip Informativi Fonti PII: Integrazione tooltip CSS puri su icona info `(i)` per visualizzare la fonte OSINT e la confidenza di ciascun dato sensibile nella Dashboard.
- [x] Widget Geolocalizzazione e Luoghi Frequenti: Sviluppo del widget "Routine e Luoghi Frequenti" che mappa e analizza i tag di geolocalizzazione estratti dagli ultimi post Instagram del target.
- [x] OSINT Sensors Hub UI: Integrazione dell'Analizzatore Strumenti OSINT per monitorare lo stato di attivazione e il funzionamento di Sherlock, Holehe, DuckDuckGo e Instagram Deep Scan.
- [x] Documentazione: Aggiornamento `AI_JOURNAL.md` e sync con `ARCHITECTURE.md`.

### Fase 5.10: Risoluzione Errore HTTP 429 Instagram Deep Scan & Stabilizzazione Suite Test
- [x] Abilitazione supporto HTTP/2 in `httpx` (libreria `h2`) per bypassare il fingerprinting anti-bot di Instagram.
- [x] Correzione typo User-Agent (`come Gecko` -> `like Gecko`) e arricchimento header browser-like (`X-ASBD-ID`, `X-IG-App-ID`, Referer, Origin).
- [x] Automazione del Deep Scan per target Instagram in modalità Zero-Login (senza sessionid per profili pubblici).
- [x] Stabilizzazione e correzione dell'autenticazione JWT nella suite di test in `conftest.py`.
- [x] Strutturazione e correlazione dei Vettori di Minaccia e delle relative Mitigazioni direttamente nel modello `MitigationSection`.
- [x] Mappatura precisa degli stati dei sensori OSINT nel frontend tramite l'introduzione di un blocco `metadata` inviato dal backend.

### Fase 5.11: Modulo Data Breach (XposedOrNot) & Dorking
- [x] Sostituzione della dork di ricerca sensibile in `scraper.py` con una dork mirata ai Data Breach (`pastebin OR dump OR data breach`).
- [x] Sviluppo di un nuovo servizio backend (`databreach_service.py`) per l'interrogazione dell'API pubblica e gratuita XposedOrNot.
- [x] Integrazione automatica in `analyze.py`: individuazione email estratte e query simultanea per l'elenco dei Data Breach noti.
- [x] Inserimento di regole di calcolo fittizie nel system prompt del Risk Engine (`risk_engine.py`) per calibrare matematicamente il peso delle email compromesse (es. +30 punti).

### Fase 6: Azure Deployment & Documentazione
- [x] Configurazione script e workflow Azure (App Service, GitHub Actions).
- [x] Deploy Automation Script (`deploy_azure.sh`, `startup.sh`).
- [x] Stesura relazione finale (`docs/FINAL_REPORT.md` inclusiva di trasparenza AI come da `AI_JOURNAL.md`).

### Fase 7: Pro & Cloud Native Upgrade (Auth, Alembic, UI/UX)
- [x] Inizializzazione Auth JWT e Security Models.
- [x] Configurazione Alembic per Database Migrations (PostgreSQL/SQLite).
- [x] Implementazione UI Frontend (Login/Register).
### Fase 7.1: UI Premium & Auth Bypass Locale
- [x] Semplificazione del workflow frontend tramite bypass completo del blocco `AuthScreen` (accesso diretto a `MainApp`).
- [x] Bypasso middleware JWT in `auth.py` con iniezione automatica di utente locale di default per l'archiviazione history senza barriere di login.
- [x] Restyling "Premium" della sezione `Analizzatore Strumenti OSINT`: transizione a griglia 2x2 con effetti glassmorphism, contatori dinamici basati sui payload reali (es. numero leak DDG, account Sherlock, hit Holehe) per massima trasparenza telemetrica.
- [x] Correzione rendering colori `ProgressBar` Tremor (fix da `rose/amber` a `red/amber`).

### Fase 7.2: Risoluzione Definitiva Rate Limits API AI (Gemini + Groq)
- [x] Integrazione del Provider **Groq** (modelli Llama 3) come alternativa a Google Gemini per aggirare i severi Rate Limit (errore 429) e i blocchi del Free Tier in Europa.
- [x] Refactoring dei servizi `risk_engine.py` e `analyze.py` con switch dinamico basato su variabile d'ambiente (`AI_PROVIDER="groq"` o `"gemini"`).
- [x] Implementazione del Parsing JSON per Groq (Structured Outputs).

### Fase 8: Deploy Cloud Native Reale su Azure
- [ ] Deploy Cloud Native Reale su Azure (con PostgreSQL).

---

## 3. System Design & Cloud Roadmap
L'architettura è stata progettata seguendo il paradigma **Event-Driven / Asynchronous** per garantire scalabilità e resilienza su Azure App Service.

### 3.1 Disaccoppiamento Ingestion / Processing
1. **API Ingestion**: Il router `/api/v1/analyze` (Rest API) in modalità "fire-and-forget" (HTTP 202 Accepted).
2. **Worker in Background**: L'analisi (Discovery -> Scraping -> OCR -> NLP -> Risk Engine) è delegata a `BackgroundTasks` nativi di FastAPI, prevenendo timeout (es. 230 secondi su Azure App Service).

### 3.2 Sicurezza: Anti-DoS e Rate Limiting
- **Middleware 413 Payload Too Large**: Qualsiasi richiesta con `Content-Length > 10.000 byte` viene respinta istantaneamente all'ingresso.
- **Hard Limit NLP**: Truncating del payload OSINT prima del NLP/LLM a max 15.000 caratteri.

### 3.3 Roadmap Scalabilità (Azure)
- **Database**: Migrazione da SQLite in locale a CosmosDB o Azure SQL.
- **Worker**: Migrazione da `BackgroundTasks` asincroni in-process a una message queue distribuita (Azure Service Bus) per pool di `Azure Functions`.
