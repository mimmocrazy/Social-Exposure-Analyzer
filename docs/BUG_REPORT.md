# Bug Report & Troubleshooting

Questo documento traccia storicamente i bug applicativi, gli "Edge Case" e le incoerenze scoperte durante l'audit profondo del progetto e lo sviluppo dell'ambiente di testing (FastAPI + SQLModel + Pytest). 
Raccoglie sia il *technical debt* risolto a livello di logica applicativa, sia le risoluzioni architetturali necessarie per mantenere il sistema deterministico e stabile nella CI/CD.

## 1. Anomalie Applicative (Runtime)

| ID | Data Scoperta | Componente | Descrizione Bug | Impatto | Soluzione Applicata |
|---|---|---|---|---|---|
| B01 | 2026-06-03 | `analyze.py` | Fallback errato: L'utilizzo di sequenze `if` separate per i provider (GitHub, Groq, Gemini) faceva scattare il fallback di Gemini anche quando l'estrazione andava a buon fine tramite gli altri provider. | Alto | Correzione logica del flusso di controllo passando a `if ... elif ... elif`. |
| B02 | 2026-06-03 | `risk_engine.py` | Loop infinito nella rotazione chiavi: In caso di errore 503, la funzione `rotate_gemini_key` entrava in ricorsione all'infinito causando un crash stack-overflow. | Critico | Implementato un tetto massimo di fallback (`len(GEMINI_KEYS)`) ed exit-condition sicure. |
| B03 | 2026-06-03 | `risk_engine.py` | Decommissioning di Llama3 su Groq: Il modello hardcodato `llama3-70b-8192` è stato deprecato dal provider, causando un errore 404/400 fisso. | Alto | Aggiornato il payload al modello `llama-3.3-70b-versatile` attualmente supportato e stabile. |

---

## 2. Test Environment Troubleshooting

I seguenti punti descrivono i fix architetturali applicati per far fronte alle collisioni tra i task in background, il mock del database e la libreria di testing `pytest`.

### 2.1 Missing API Key during Pytest Collection (google-genai)
**Sintomo:** Eseguendo `pytest tests/`, l'intera suite falliva alla fase di *Collection* con un errore fatale `ValueError: No API key was provided` originato dal client Gemini (`google-genai`).
**Causa:** In `backend/services/risk_engine.py`, il client Gemini veniva inizializzato a livello di modulo globale (`client = genai.Client()`). Durante l'importazione nei file di test, il file veniva letto ed eseguito immediatamente, andando a schiantarsi poiché le variabili d'ambiente di sviluppo locale non erano presenti nel context del testing puro.
**Risoluzione Architetturale:**
- È stato introdotto il pattern **Lazy Loading** per il client. 
- Implementata la funzione `get_client()` che inizializza il client solo alla prima chiamata, isolando l'ambiente globale da dipendenze esterne.

### 2.2 In-Memory SQLite Tables Vanishing (`OperationalError: no such table`)
**Sintomo:** L'esecuzione del test integrativo (`test_integration.py`) falliva con `sqlite3.OperationalError: no such table: profileanalysis`.
**Causa:** Nel file `conftest.py`, era stato configurato un database fittizio in-memory (`sqlite:///:memory:`). Tuttavia, SQLite in memoria, per default, distrugge il DB non appena la connessione originale si chiude. L'ORM creava le tabelle, ma non appena la transazione finiva, il database spariva.
**Risoluzione Architetturale:**
- È stata inserita in fase di *create_engine* la direttiva `poolclass=StaticPool`.
- Questo forza l'engine a riutilizzare la medesima connessione fisica, garantendo che le tabelle generate persistano per l'intera durata della sessione di test.

### 2.3 BackgroundTasks Bypassing the Mocked Session Engine
**Sintomo:** Pur avendo sovrascritto correttamente la Dependency `get_session` nel `TestClient` per fargli usare il DB in-memory, l'endpoint `analyze_profile` falliva a valle nel task asincrono.
**Causa:** I BackgroundTasks in FastAPI girano in modo disaccoppiato dal lifecycle della request. Mentre la richiesta web utilizzava il DB fittizio, la funzione in background importava **staticamente** il vero `engine` da `backend.database`, che nel contesto isolato dei test era sprovvisto della tabella.
**Risoluzione Architetturale:**
- L'import dell'engine in `backend/api/routers/analyze.py` è stato trasformato in dinamico (eseguendo `import backend.database` e richiamando `backend.database.engine`).
- In `conftest.py`, viene "mockato" non solo il `get_session` della request, ma anche l'engine globale: `backend.database.engine = engine_in_memory`.

### 2.4 UUID Serialization in BackgroundTasks
**Sintomo:** Il test `test_analyze_profile` falliva poiché la query sul database in background andava in crash tentando di recuperare il record dell'analisi.
**Causa:** L'endpoint passava l'id dell'analisi al `BackgroundTask` serializzandolo implicitamente come stringa. SQLAlchemy richiede un oggetto di tipo `uuid.UUID` per estrarne la proprietà `.hex`.
**Risoluzione Architetturale:**
- Aggiunta una conversione esplicita all'inizio del Background Task per assicurarsi che, se l'ID ricevuto in input è una stringa, venga trasformato in oggetto `uuid.UUID` prima di interrogare il DB.

### 2.5 Disallineamento Exception nel Risk Engine Fallback
**Sintomo:** Il test `test_calculate_risk_fallback` in `test_ai_services.py` falliva ricevendo una `RuntimeError` anziché un oggetto `RiskReport` vuoto.
**Causa:** Durante una revisione architetturale il `risk_engine.py` è stato modificato per lanciare esplicitamente una `RuntimeError` interrompendo la pipeline in caso di Quota Exceeded. Il test, tuttavia, era rimasto ancorato alle vecchie aspettative.
**Risoluzione Architetturale:**
- L'assertion del test in `test_ai_services.py` è stata modificata per usare `with pytest.raises(RuntimeError):`.

### 2.6 Local Import Patching Fallback
**Sintomo:** Il test dell'endpoint `analyze_profile` andava in crash durante il patching del mock `mocker.patch('backend.api.routers.analyze.calculate_risk')`.
**Causa:** All'interno di `analyze.py`, per evitare loop circolari, l'importazione di `calculate_risk` avveniva a runtime (local import) dentro il BackgroundTask. Questo rende inefficace il patching classico dall'esterno sul router.
**Risoluzione Architetturale:**
- La strategia di patching è stata reindirizzata alla root source del servizio (`backend.services.risk_engine.calculate_risk`).

### 2.7 AsyncMock vs HTTPX Sync Properties
**Sintomo:** I test dello Scraper fallivano quando `BeautifulSoup` tentava di parsarne l'HTML di mock.
**Causa:** Nel mockare `httpx.AsyncClient.get` tramite un `AsyncMock` standard, Pytest tramutava ogni proprietà derivata (`.json()`, `.text`) in coroutine. Httpx, al contrario, ha tali proprietà definite come sincrone, causando crash quando `BeautifulSoup` tentava di leggerle.
**Risoluzione Architetturale:**
- Implementata una definizione ibrida dei Mock: l'oggetto response è un `AsyncMock`, ma i payload sono stati convertiti manualmente (`.text = PropertyMock(return_value='<html>...')`).

### 2.8 React Testing Library Selector Ambiguity
**Sintomo:** Fallimento secco del frontend testing su Vitest all'interno di `App.test.jsx`.
**Causa:** L'uso generico di `screen.getByText` finiva col matchare sia il titolo sia paragrafi di testo (es: "Social"). Dato che `getByText` esige di trovare un solo elemento, la doppia occorrenza rompeva l'asserzione.
**Risoluzione Architetturale:**
- Sostituzione delle asserzioni generiche con query mirate e inattaccabili basate su ID o placeholder (`getByPlaceholderText`).

*Nota: Questo documento combinato attesta l'evoluzione strutturale del codice, il refactoring proattivo e la rigorosa gestione degli edge case.*
