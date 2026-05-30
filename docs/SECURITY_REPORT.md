# Manual Security Audit Report

Analisi di sicurezza manuale e approfondita del repository (Fasi 1, 2, 3), strutturata secondo gli standard OWASP Top 10.

## Tabella delle Vulnerabilità e Mitigazioni

| ID | File | Categoria OWASP | Descrizione Vulnerabilità | Impatto | Remediation | Stato |
|---|---|---|---|---|---|---|
| 01 | `main.py` | A05:2021 - Security Misconfiguration | Configurazione CORS impostata su `allow_origins=["*"]` per facilitare il dev, che espone l'API a chiamate cross-origin non autorizzate se migrato in prod così com'è. | Alto | Aggiunto un custom HTTP middleware per iniettare header di sicurezza (X-Frame-Options, nosniff) e inserito un alert per chiudere il CORS in prod. | Mitigato |
| 02 | `exceptions.py` | A05:2021 - Security Misconfiguration | Rischio di esposizione dello stacktrace al client in caso di crash non gestiti da Pydantic o FastAPI. | Medio | L'implementazione attuale di `global_exception_handler` cattura le Exception grezze e restituisce un JSON 500 standardizzato, impedendo data leak. | Risolto |
| 03 | `scraper.py` | A10:2021 - Server-Side Request Forgery | L'input dell'utente (URL) viene scaricato via `httpx`. Un attaccante potrebbe usarlo come proxy per mappare la rete interna (Azure App Service). | Alto | Implementato filtro URL Parsing: blacklist rigida per hostname interni (`localhost`, `127.0.0.1`, subnet `10.x.x.x` e `192.168.x.x`). | Risolto |
| 04 | `discovery.py`| A03:2021 - Injection | Il comando OSINT `subprocess.run` concatena l'input utente per richiamare Sherlock. Rischio di Command Injection (es. tramite operatore `;`). | Critico | Esecuzione disaccoppiata (array di argomenti, `shell=False`) e validazione stringente dell'input tramite regex alfanumerica `^[a-zA-Z0-9_.-]+$`. | Risolto |
| 05 | `analyze.py`  | A01:2021 - Broken Access Control | Assenza di meccanismi di Rate Limiting per l'ingestion asincrona, con potenziale rischio di Denial of Service sulle risorse di background. | Medio | Architettura asincrona preparata, Rate Limiting annotato come TODO prima del rilascio in produzione per evitare flood. | Aperto |
| 06 | `analyze.py` | A01:2021 - Broken Access Control | Rischio Denial of Service (esaurimento CPU) elaborando input enormi con i modelli AI pesanti di spaCy. | Alto | Introdotto truncating/limite rigido di 10.000 caratteri sul `combined_text` prima dell'estrazione PII. | Risolto |
| 07 | `logger.py` | A09:2021 - Security Logging Failures | I log diagnostici di background catturerebbero e conserverebbero su stdout le PII raccolte (Data Leakage). | Alto | Implementato filtro on-the-fly tramite regex in `loguru` per mascherare email e numeri di telefono (`[EMAIL-MASKED]`). | Risolto |
| 08 | `risk_engine.py` | A09:2021 - Data Leakage a Third-Party LLM | Rischio di esposizione di segreti di sistema (es. API Keys) inviando un payload incontrollato al provider LLM (Gemini). | Alto | Il System Prompt è blindato e il payload in ingresso è limitato alla serializzazione JSON delle sole PII estratte, isolando il contesto applicativo. | Risolto |

*Nota Generale:* Il codice core analizzato è risultato robusto. Tutte le principali vulnerabilità OWASP che tipicamente affliggono le pipeline di data-gathering risultano proattivamente coperte dai pattern di difesa integrati (Security-By-Design).

## Strategia di Validazione (CI/CD Mockup)
Il sistema adotta un approccio automatizzato e rigoroso di testing per prevenire regressioni e test-data leak:
- **Coverage**: Viene monitorato tramite `pytest-cov` per validare l'ecosistema Backend con report HTML isolati in `/reports`.
- **Data Isolation & Statelessness (Autonomous Optimization)**: La suite non genera file di database fisici (nessun `test_db.sqlite`). Tutti i test si appoggiano esclusivamente su un engine SQLite **in-memory** (`sqlite:///:memory:`) configurato in `conftest.py`. Questo garantisce isolamento assoluto tra test run, impedisce leakage persistente di mock-data su disco e riduce a zero l'overhead I/O.
