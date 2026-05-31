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

### Fase 2: Tests - Backend Foundation
- [x] Setup Pytest (`pytest.ini`, `conftest.py`).
- [x] Unit tests per operazioni CRUD e validazione input endpoint.

### Fase 3: AI & NLP Core Integration
- [x] Sviluppo modulo Discovery (Sherlock Adapter) e Scraping (Search Dorking).
- [x] Sviluppo modulo **NLP** (Estrazione PII con Presidio/spaCy).
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

### Fase 6: Azure Deployment & Documentazione
- [x] Configurazione script e workflow Azure (App Service, GitHub Actions).
- [x] Deploy Automation Script (`deploy_azure.sh`, `startup.sh`).
- [x] Stesura relazione finale (`docs/FINAL_REPORT.md` inclusiva di trasparenza AI come da `AI_JOURNAL.md`).

### Fase 7: Pro & Cloud Native Upgrade (Auth, Alembic, UI/UX)
- [ ] Inizializzazione Auth JWT e Security Models.
- [ ] Configurazione Alembic per Database Migrations (PostgreSQL/SQLite).
- [ ] Implementazione UI Frontend (Login/Register).
- [ ] Deploy Cloud Native Reale su Azure (con PostgreSQL).
