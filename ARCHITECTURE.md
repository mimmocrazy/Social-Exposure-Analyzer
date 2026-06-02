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

## 2. Roadmap e Avanzamento (Sync: AI Journal)

Questa sezione rispecchia fedelmente l'ordine logico e cronologico delle implementazioni documentate in `AI_JOURNAL.md`.

### Fase 1: Backend Foundation
- [x] Inizializzazione struttura di progetto e documentazione architetturale.
- [x] Configurazione Database e modelli ORM.
- [x] Creazione endpoint principale di ingestion.
- [x] Setup sistema di logging centralizzato e gestione errori.

### Fase 2: Discovery OSINT & Testing Setup
- [x] Setup Ambiente di Test e Primo Unit Test.
- [x] Sviluppo modulo Discovery & Data Gathering.

### Fase 3: Sicurezza & Estrazione PII
- [x] Audit di Sicurezza Integrato e Setup Security Suite.
- [x] Security Review manuale approfondita.
- [x] Sviluppo Modulo NLP e OCR (Estrazione PII).

### Fase 4: Sviluppo Risk Engine & Scalabilità
- [x] Sviluppo Modulo Risk Engine.
- [x] Setup Load Testing e Analisi di Scalabilità.
- [x] Implementazione Test Orchestrator e Reportistica.

### Fase 5: Frontend Development & UI Revolution
- [x] Frontend Development e Integrazione.
- [x] Master Test Orchestrator e Validation Gate.
- [x] Redesign UX/UI Dashboard (Apple-Style Glassmorphism).
- [x] Raggruppamento PII & Audit AI Strutturato con Refining Estetico Premium.
- [x] Rivoluzione Dashboard (Moduli Sensori OSINT) & Sub-Scoring.
- [x] Trasparenza UI/UX High-Signal, Routine e Mappatura Sensori OSINT.
- [x] Semplificazione Dashboard, Animazioni Premium e Cronologia Ultime Ricerche.
- [x] Bypasso Autenticazione per Esecuzione Locale, Correzione ProgressBar e Restyling Hub Sensori OSINT.

### Fase 6: OSINT Avanzato & Stabilizzazione Core
- [x] Potenziamento OSINT: Anti-Allucinazione AI, Deduzione Identità e Aderenza alla Traccia.
- [x] Risoluzione Errore HTTP 429 Instagram Deep Scan & Stabilizzazione Suite Test.
- [x] Correlazione Vettori di Minaccia e Mitigazioni & Fix Stati Sensori OSINT.
- [x] Sostituzione Dork Inappropriata e Integrazione Modulo Data Breach (XposedOrNot).

### Fase 7: Pro Upgrade (LLM-Native & Cloud Preparation)
- [x] Inizializzazione Auth & Alembic.
- [x] Refactoring Architetturale OSINT & PII Extraction (Approccio LLM-Native).
- [x] Switch Architetturale AI Provider (Groq Integration).
- [x] Risoluzione Broken Images CORS e Ottimizzazione Rate Limits LLM.
- [x] UX Premium & Deep Scan Controls.

### Fase 8: Deploy Cloud Native & Conformità Accademica
- [x] Conformità Accademica Ibrida (SpaCy + OCR + LLM).
- [x] Deploy Cloud Native su Azure (Costo Zero) & Terminal UX Overhaul.
- [x] Stesura Documentazione Finale.

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
