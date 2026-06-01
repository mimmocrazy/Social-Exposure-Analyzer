# Test Environment Troubleshooting & Bugs

Questo documento descrive e traccia storicamente gli "Edge Case" dell'ambiente di testing (FastAPI + SQLModel + Pytest) che hanno richiesto una risoluzione architetturale o *Autonomous Optimizations* al fine di mantenere il sistema deterministico e stabile nella CI/CD.

## 1. Missing API Key during Pytest Collection (google-genai)
**Sintomo:** Eseguendo `pytest tests/`, l'intera suite falliva alla fase di *Collection* con un errore fatale `ValueError: No API key was provided` originato dal client Gemini (`google-genai`).
**Causa:** In `backend/services/risk_engine.py`, il client Gemini veniva inizializzato a livello di modulo globale (`client = genai.Client()`). Durante l'importazione nei file di test (per esempio, per testare il mock), il file veniva letto ed eseguito immediatamente, andando a schiantarsi poiché le variabili d'ambiente di sviluppo locale non erano presenti nel context del testing puro.
**Risoluzione Architetturale:**
- È stato introdotto il pattern **Lazy Loading** per il client. 
- Implementata la funzione `get_client()` che inizializza il client solo alla prima chiamata, isolando l'ambiente globale da dipendenze esterne.
- **Riferimento Codice:** [backend/services/risk_engine.py](../backend/services/risk_engine.py)

## 2. In-Memory SQLite Tables Vanishing (`OperationalError: no such table`)
**Sintomo:** L'esecuzione del test integrativo (`test_integration.py`) falliva con `sqlite3.OperationalError: no such table: profileanalysis`.
**Causa:** Nel file `conftest.py`, era stato configurato un database fittizio in-memory (`sqlite:///:memory:`). Tuttavia, SQLite in memoria, per default, distrugge il DB non appena la connessione originale si chiude. L'ORM `SQLModel.metadata.create_all(engine)` creava le tabelle, ma non appena la transazione finiva, il database spariva. Qualsiasi successiva connessione si ritrovava in un nuovo database vuoto.
**Risoluzione Architetturale:**
- È stata inserita in fase di *create_engine* la direttiva `poolclass=StaticPool` (da `sqlalchemy.pool import StaticPool`).
- Questo forza l'engine a riutilizzare la medesima connessione fisica, garantendo che le tabelle generate persistano per l'intera durata della sessione di test.
- **Riferimento Codice:** [tests/conftest.py](../tests/conftest.py)

## 3. BackgroundTasks Bypassing the Mocked Session Engine
**Sintomo:** Pur avendo sovrascritto correttamente la Dependency `get_session` nel `TestClient` per fargli usare il DB in-memory, l'endpoint `analyze_profile` falliva a valle. Nello specifico, il fallimento avveniva nel `run_scraping_task` eseguito in background (tramite `BackgroundTasks` di FastAPI) che restituiva di nuovo l'errore della tabella mancante.
**Causa:** I BackgroundTasks in FastAPI girano in modo disaccoppiato dal lifecycle della request. Mentre la richiesta web utilizzava il DB fittizio, la funzione in background eseguiva `with Session(engine) as session:`, importando **staticamente** il vero `engine` da `backend.database`. Il DB reale, non essendo mai stato inizializzato nel contesto isolato dei test, ovviamente era sprovvisto della tabella.
**Risoluzione Architetturale:**
- L'import dell'engine in `backend/api/routers/analyze.py` è stato trasformato in dinamico (eseguendo `import backend.database` e richiamando `backend.database.engine`).
- In `conftest.py`, viene "mockato" non solo il `get_session` della request, ma anche l'engine globale: `backend.database.engine = engine_in_memory`.
- In questo modo, quando il task asincrono in background istanzia il context manager, interroga l'engine corretto temporaneo e il test fluisce regolarmente.
- **Riferimenti Codice:** [backend/api/routers/analyze.py](../backend/api/routers/analyze.py), [tests/conftest.py](../tests/conftest.py)

## 4. UUID Serialization in BackgroundTasks (`AttributeError: 'str' object has no attribute 'hex'`)
**Sintomo:** Il test `test_analyze_profile` falliva poiché la query sul database in background andava in crash tentando di recuperare il record dell'analisi (`session.get(ProfileAnalysis, analysis_id)`).
**Causa:** L'endpoint passava l'id dell'analisi al `BackgroundTask` serializzandolo implicitamente come stringa (o SQLite, non avendo un tipo UUID nativo, lo restituiva come stringa). SQLAlchemy richiede un oggetto di tipo `uuid.UUID` per i campi mappati come Primary Key UUID per poterne estrarre la proprietà `.hex`.
**Risoluzione Architetturale:**
- Aggiunta una conversione esplicita all'inizio del Background Task per assicurarsi che, se l'ID ricevuto in input (o letto da SQLite) è una stringa, venga trasformato in oggetto `uuid.UUID` prima di interrogare il DB.
- **Riferimento Codice:** [backend/api/routers/analyze.py](../backend/api/routers/analyze.py) (inizio funzione `run_scraping_task`)

## 5. Disallineamento Exception nel Risk Engine Fallback (`RuntimeError: Errore critico Gemini API`)
**Sintomo:** Il test `test_calculate_risk_fallback` in `test_ai_services.py` falliva ricevendo una `RuntimeError` anziché un oggetto `RiskReport` vuoto (di salvataggio).
**Causa:** Durante una revisione architetturale per evitare che il frontend ricevesse falsi report "sicuri" quando l'API Gemini andava in *Quota Exceeded*, il `risk_engine.py` è stato modificato per lanciare esplicitamente una `RuntimeError` che interroga l'errore asincrono, interrompendo la pipeline e scatenando il fallimento della task di orchestrazione. Il test, tuttavia, era rimasto ancorato alle vecchie aspettative (oggetto `RiskReport` generato come mock di fallback con `score=0`).
**Risoluzione Architetturale:**
- L'assertion del test in `test_ai_services.py` è stata modificata per usare `with pytest.raises(RuntimeError):` al fine di aspettarsi coerentemente il blocco della pipeline in caso di down o rate limit aspro da parte del LLM.
- **Riferimenti Codice:** [tests/test_ai_services.py](../tests/test_ai_services.py), [backend/services/risk_engine.py](../backend/services/risk_engine.py)

## 6. Local Import Patching Fallback (`AttributeError: module has no attribute 'calculate_risk'`)
**Sintomo:** Il test dell'endpoint `analyze_profile` andava in crash durante il patching del mock `mocker.patch('backend.api.routers.analyze.calculate_risk')`.
**Causa:** All'interno di `analyze.py`, per evitare loop circolari, l'importazione di `calculate_risk` avveniva a runtime (local import) dentro il BackgroundTask `run_scraping_task`. Questo significa che a livello globale il modulo router non possedeva affatto quell'attributo, rendendo inefficace il patching classico dall'esterno.
**Risoluzione Architetturale:**
- La strategia di patching è stata reindirizzata alla root source del servizio (`backend.services.risk_engine.calculate_risk`), fornendo un `AsyncMock` esplicito per scavalcare l'invocazione di rete asincrona.
- **Riferimento Codice:** [tests/test_analyze.py](../tests/test_analyze.py)

## 7. AsyncMock vs HTTPX Sync Properties (`TypeError: object of type 'coroutine' has no len()`)
**Sintomo:** I test dello Scraper (in particolare Instagram e FB) fallivano quando `BeautifulSoup` tentava di parsarne l'HTML di mock.
**Causa:** Nel mockare `httpx.AsyncClient.get` tramite un `AsyncMock` standard, Pytest tramutava **ogni** proprietà derivata (`.json()`, `.text`) in ulteriori coroutine. Httpx, al contrario, ha tali proprietà / metodi definiti come del tutto sincroni. `BeautifulSoup` ha ricevuto una coroutine su `.text` e, provando a estrarne la lunghezza (`len()`), ha sollevato l'errore fatale di tipo.
**Risoluzione Architetturale:**
- Implementata una definizione ibrida dei Mock: l'oggetto response in sé è un `AsyncMock` (visto che l'HTTP request asincrona prevede un `await`), ma i payload di payload e proprietà ad accesso diretto sono stati convertiti manualmente: `.json = MagicMock(return_value={...})` e `.text = PropertyMock(return_value='<html>...')`.
- **Riferimento Codice:** [tests/test_scraper.py](../tests/test_scraper.py)

## 8. React Testing Library Selector Ambiguity (`Found multiple elements with the text`)
**Sintomo:** Fallimento secco del frontend testing su Vitest all'interno di `App.test.jsx`.
**Causa:** Il componente `App.jsx` presenta una UI complessa con molta copy esplicativa. L'uso generico di `screen.getByText(/Social/i)` (studiato per matchare il Title h1) finiva con il matchare sia il titolo sia paragrafi di copy (es: "rischi di social engineering"). Dato che `getByText` esige obbligatoriamente di trovare uno e un solo elemento (pena crash del test), la doppia occorrenza rompeva l'asserzione.
**Risoluzione Architetturale:**
- Sostituzione delle asserzioni di testo generiche con varianti più sicure per l'integrità UI come `getAllByText` (assumendone poi l'array per validare l'esistenza), e query dirette per label o placeholder `getByPlaceholderText`.
- **Riferimento Codice:** [frontend/src/App.test.jsx](../frontend/src/App.test.jsx)
