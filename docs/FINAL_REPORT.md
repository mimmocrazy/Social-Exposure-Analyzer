# Social Exposure Analyzer - Relazione Finale di Progetto

## 1. Introduzione
Il presente documento descrive l'architettura, le tecnologie impiegate e i criteri di progettazione del progetto **Social Exposure Analyzer**, un'applicazione per il *Social Engineering Risk Assessment*. Il sistema è concepito per estrarre informazioni pubbliche (OSINT) da profili social, identificare le PII (Personally Identifiable Information) tramite intelligenza artificiale locale e calcolare, tramite LLM in cloud, un rischio di impersonificazione e attacco.

## 2. Architettura del Sistema
L'applicativo è strutturato in un'architettura cloud-ready a tre livelli, isolati e scalabili:

### 2.1 Backend (Python / FastAPI)
- **Framework:** FastAPI, selezionato per le sue prestazioni asincrone e per la generazione nativa di documentazione OpenAPI.
- **ORM & Persistenza:** SQLModel / SQLite. Utilizzato per astrarre le query SQL pur mantenendo le feature di validazione dati di Pydantic.
- **Asincronia e Resilienza:** L'elaborazione del rischio (scraping + NLP + LLM) avviene interamente in background tramite l'astrazione `BackgroundTasks` per evitare saturazioni della connessione HTTP del client. Un middleware Anti-DoS in ingresso previene payload malevoli maggiori di 10.000 bytes.

### 2.2 Frontend (React / Vite)
- **Librerie:** React, Tailwind CSS e Tremor (per la reportistica grafica).
- **Design Pattern:** Interfaccia ispirata al "Glassmorphism" in dark mode, focalizzata su reattività e chiarezza delle informazioni.
- **Polling Asincrono:** Integrata una logica di polling verso l'API backend per recuperare dinamicamente lo status dell'elaborazione in tempo reale.

### 2.3 Sicurezza e Deployment (Azure)
- **Vulnerabilità (OWASP Top 10):** Il codice è protetto da attacchi SSRF, Command Injection (tramite Whitelisting nel modulo subprocess) e Data Leaks. I log mascherano automaticamente le PII. Il dettaglio è consultabile nel file `SECURITY_REPORT.md`.
- **Infrastruttura:** L'applicazione include gli script `deploy_azure.sh` e un workflow per **GitHub Actions** al fine di avviare l'istanza su un servizio PaaS: *Microsoft Azure App Service*.

## 3. Modelli di Intelligenza Artificiale
Il progetto si fonda sull'utilizzo combinato e sequenziale di tre motori AI con scopi differenti:
1. **NLP (spaCy):** Processazione del linguaggio naturale rigorosamente in locale per intercettare Nomi, Organizzazioni, Località e indirizzi email (modello linguistico `it_core_news_lg`). Garantisce zero-latency e privacy totale per la classificazione iniziale delle entità.
2. **OCR (EasyOCR/Tesseract):** Deep Learning per visione artificiale. Usato per interpretare testo rasterizzato nelle immagini di profilo o nei bio-link.
3. **LLM (Google Gemini Pro):** Sfruttato *esclusivamente* nella fase finale. Non processa il testo sporco, ma riceve solo le PII estratte precedentemente formattate in JSON, assicurando un consumo di token bassissimo e una latenza minima. Sfrutta il feature "Structured Outputs" per restituire un *RiskReport* garantito.

## 4. Trasparenza sull'Uso dell'AI Generativa (AI_JOURNAL)
In conformità ai requisiti di progetto, lo sviluppo è stato guidato interamente da un *Lead System Architect AI* (Antigravity IDE integrato).
L'intero processo decisionale, i trade-off architetturali e i prompt inviati al motore LLM per generare le basi di codice sono pubblicamente tracciati e commentati nel file `AI_JOURNAL.md`. 
Le *Autonomous Optimizations* apportate dall'AI (come la correzione dei middleware e l'ingegnerizzazione dei BackgroundTasks) sono parimenti evidenziate nello storico di git, garantendo tracciabilità assoluta di chi ha scritto cosa e con quale logica di business.

## 5. Conclusioni
La piattaforma sviluppata rappresenta una baseline completa e aderente alle pratiche industriali di CI/CD, testing e security-first development. L'ambiente è pronto per accogliere ulteriori estensioni orizzontali (es. migrazione da SQLite a Cosmos DB o PostgreSQL per le analisi di massa).
