# Relazione Tecnica Estesa: Social Exposure Analyzer
**Sistemi Distribuiti e Cloud Computing**

---

## 1. Architettura di Sistema e Flusso dei Dati (Overview)
*Social Exposure Analyzer* è un sistema distribuito progettato per l'aggregazione, l'analisi e la validazione OSINT (Open Source Intelligence) volta a quantificare l'esposizione al rischio di *Social Engineering*. 
L'applicativo adotta un'architettura **Client-Server Asincrona** basata su micro-task. Il Frontend (React) agisce come centro di comando e visualizzazione (Dashboard), mentre il Backend (FastAPI in Python) funge da Orchestratore Distribuito per moduli di Scraping, Motori NLP e modelli LLM (Large Language Models).

---

## 2. Deep Dive sul Frontend (Interfaccia Utente e Stato)
Il Frontend è stato sviluppato utilizzando **React**, **Vite**, **TailwindCSS** per lo styling "Glassmorphism" e la libreria **Tremor** per la visualizzazione dei dati e dei grafici.
Ogni componente dell'interfaccia ha un riscontro diretto sulle chiamate API scambiate con il backend.

### 2.1 Hero Section e Parametrizzazione dell'Analisi
La schermata iniziale permette all'utente di definire il perimetro d'azione dei worker backend. I controlli UI gestiscono uno stato React (`useState`) complesso che compone il payload JSON inviato all'endpoint `POST /api/v1/analyze`.

* **Barra di Ricerca (Target):** Accetta uno username o un URL diretto. Il backend applica un parser per normalizzare il target.
* **Selettore di Profondità (FAST / STD / DEEP):** Modifica la capienza dell'estrazione dei social post. Nello specifico, si mappa a una variabile `analysis_depth` che il backend traduce in limiti numerici: *FAST (5 Post)*, *STD (12 Post)*, *DEEP (20+ Post)*, bilanciando il rate-limit e la latenza.
* **Configurazione Sensori OSINT (Toggles):** L'attivazione di questi sensori non cambia solo una flag a livello di UI, ma orchestra l'attivazione di veri e propri "Agenti" (worker) specializzati nel backend, ognuno con implicazioni architetturali e capacità di intrusione differenti:
  * **DuckDuckGo Dorking:** Oltrepassa il perimetro dei social network. Implica l'esecuzione automatizzata di query con operatori avanzati (Dorks) sui motori di ricerca per rintracciare l'alias dell'utente all'interno di *Pastebin*, dump di database o forum underground. L'obiettivo non è trovare ciò che l'utente ha pubblicato volontariamente, ma ciò che è "sfuggito" (es. data breaches o leak aziendali correlati).
  * **Cross-Check Email (Holehe OSINT):** Se attivato, implica un'analisi comportamentale basata su vettori laterali. Il worker interroga le API di "Reset Password" di oltre 120 piattaforme web (da Twitter a servizi di dating e forum). Poiché le piattaforme rispondono diversamente se una mail esiste ("*Ti abbiamo inviato un link*") o meno ("*Utente non trovato*"), il sistema riesce a mappare la presenza digitale nascosta dell'utente senza mai notificarlo o allertarlo.
  * **Instagram Deep Scan (Cookie `sessionid`):** L'inserimento del `sessionid` trasforma l'applicativo da un semplice bot a un browser "autenticato" (Impersonation). Questo comporta il bypass totale dei Login Wall e dei rigidi Rate Limit di Meta. Tecnicamente, permette di superare la limitazione della singola biografia pubblica, sbloccando l'estrazione in batch dell'intera timeline dei post, l'analisi delle caption, dei geotag (cruciale per identificare la routine) e della rete relazionale (follower/following).
  * **Facebook Deep Scan (Cookie `c_user` / `xs`):** Speculare a Instagram, ma architettonicamente usa richieste dirette agli endpoint mbasic (o GraphQL) per eludere i moderni sistemi anti-bot. Questo implica la capacità di estrarre dati altamente strutturati e sensibili dalle tab "Informazioni", prelevando lo storico lavorativo, l'educazione, le parentele e le frequentazioni, generando la fetta più grossa di vulnerabilità a tecniche di *Spear Phishing*.

*Snippet (Frontend API) - Preparazione del payload e attivazione dei sensori:*
```javascript
export const startAnalysis = async (target_url, enable_ddg, enable_holehe, ig_sessionid, enable_fb_scan, fb_c_user, fb_xs, analysis_depth) => {
    // La UI trasforma lo stato globale (i toggle) in questo payload JSON
    const response = await apiClient.post(`/analyze`, { 
        target_url, enable_ddg, enable_holehe, ig_sessionid,
        enable_fb_scan, fb_c_user, fb_xs, analysis_depth
    });
    return response.data; // Ritorna l'analysis_id asincrono (HTTP 202)
};
```

### 2.2 Sincronizzazione Asincrona (Il Terminale Virtuale)
Trattandosi di task OSINT che possono richiedere svariati minuti, il blocco dell'interfaccia utente (Synchronous Blocking) è inaccettabile. Il componente `TerminalLoading` risolve il problema usando il pattern del **Short Polling** tramite `React Query`.
1. Il client fa una chiamata `POST /analyze` e riceve subito HTTP 202 Accepted con un `analysis_id`.
2. Ogni 800 millisecondi, il frontend esegue una `GET /api/v1/analyze/{id}` per verificare lo stato di avanzamento (`PENDING` o `COMPLETED`) e la `current_phase`.
3. Un hook di React (`useEffect`) ascolta i cambiamenti della `current_phase` (es: `Instagram Deep Scan`, `Estrazione NLP`) e immette in una coda di rendering visivo (il Terminale) una serie di log formattati con delay stocastici (animazioni via `setTimeout`), donando la sensazione di un monitoraggio locale a latenza-zero.

*Snippet (Frontend React Query) - Short Polling intelligente:*
```javascript
const { data, isLoading } = useQuery({
  queryKey: ['analysis', analysisId],
  queryFn: () => getAnalysisStatus(analysisId),
  enabled: !!analysisId,
  // Esegue il polling non invasivo ogni 800ms solo finché l'analisi è in corso
  refetchInterval: (query) => {
    if (!query.state.data) return 800;
    return query.state.data.status === 'PENDING' ? 800 : false; // Ferma il polling su COMPLETED/FAILED
  },
});
```

### 2.3 Dashboard dei Risultati (Rendering Condizionale e UI)
A elaborazione terminata, l'UI collassa il terminale per rivelare la dashboard interattiva.
* **RadialProgress (Calcolo dello Score):** Sviluppato con SVG custom e animato tramite `Framer Motion`. Il cerchio si riempie in base al **Risk Score (0-100)** ritornato dal Risk Engine LLM. Più lo score è alto, più il colore vira dinamicamente dal verde al rosso neon applicando drop-shadow dinamiche.
* **Sub-Scores Metrics:** Tre barre orizzontali mostrano i sotto-punteggi (Identità, Relazioni, Routine) valutati semanticamente dall'Intelligenza Artificiale in base alla gravità dei dati esposti.
* **PII Grid Widget:** I Dati Sensibili Estrapolati (PII) vengono divisi logicamente dall'algoritmo del frontend in `Core PII` (Email, Numeri, Indirizzi IP, Target) e `Contextual PII` (Organizzazioni, Età, Occupazione), mostrando badge dedicati per fonte e percentuale di confidenza generata dai modelli NLP.

---

## 3. Integrazione Moduli OSINT e Scraping (L'Orchestratore)
Il backend FastAPI esegue le analisi all'interno di Thread separati o contesti asincroni (coroutine). 

*Snippet (Backend Python) - Fire and Forget pattern via FastAPI:*
```python
@app.post("/api/v1/analyze", status_code=202)
async def analyze_target(request: AnalysisRequest, background_tasks: BackgroundTasks):
    analysis_id = str(uuid.uuid4())
    # Fire and Forget: l'elaborazione NLP/Scraping viene delegata a un worker asincrono
    # senza bloccare il thread principale o la connessione del client React.
    background_tasks.add_task(orchestrator_pipeline, analysis_id, request)
    return {"analysis_id": analysis_id, "status": "PENDING"}
```

### 3.1 Sherlock (Discovery Iniziale)
Il primo passaggio dell'orchestratore consiste nell'effettuare una scansione di "Name squatting" e Discovery tramite il motore **Sherlock**. Viene scandagliato l'intero web per capire su quanti (e quali) social network l'username target è registrato, restringendo i perimetri per lo scraping successivo.

### 3.2 Modulo Scraping Instagram e Facebook (Graceful Degradation e Impersonation)
Lo scraping è il modulo centrale della raccolta dati. Essendo le piattaforme social ostili all'estrazione automatizzata, il sistema implementa architetture di resilienza e *Graceful Degradation*:

* **Instagram Deep Scan (SessionID e Fallback):** Sfruttando i cookie iniettati dal frontend, lo scraper istanzia richieste autenticate (mimando l'header di un browser reale). Questo sblocca l'estrazione in batch dell'intera timeline dei post, l'analisi delle caption, dei geotag e della rete relazionale (follower/following).
Tuttavia, l'orchestratore implementa un **meccanismo di Fallback Intelligente**: se il `sessionid` fornito dall'utente innesca controlli anti-bot e la piattaforma restituisce un errore `HTTP 403 Forbidden` (nascondendo le foto), il sistema rileva l'anomalia in tempo reale. Invece di far fallire l'analisi (Hard Fail), attua una *graceful degradation* rimuovendo i cookie "al volo" e ri-eseguendo la richiesta in modalità "ospite pubblico". Se il profilo bersaglio è pubblico, questa manovra assicura l'estrazione garantita della timeline senza interruzioni.

* **Facebook Deep Scan:** Lavora in modo speculare richiedendo i cookie `c_user` e `xs` per accedere alle API GraphQL o alle URL `mbasic.facebook.com`. Questo approccio massimizza la quantità di dati estraibili dalle sezioni private (cronologia lavorativa, amicizie), minimizzando i blocchi anti-bot.

### 3.3 DuckDuckGo Dorking
Se l'analista lo abilita tramite UI, viene attivato un modulo specifico che esegue query (Dorks) in background (es: `"nome bersaglio" pastebin OR dump OR "data breach"`). Serve a rintracciare porzioni di log sparsi nel clearnet o nel darkweb accessibile che contengono l'alias della vittima.

### 3.4 Holehe (Verifica Cross-Site)
Appena il modulo NLP individua un indirizzo Email in una biografia o in un post, l'orchestratore inietta la stringa in **Holehe**, il quale controlla asincronamente se quell'email è iscritta a determinati servizi web sfruttando la funzione di reset della password (senza avvisare il bersaglio). Il risultato certifica in modo univoco se la vittima usa Twitter, Github, OnlyFans, Spotify, ecc.

---

## 4. NLP, Estrazione Dati Sensibili (PII) e OCR
Una volta ottenuto un "Dump" grezzo di post, biografie e log, entra in gioco la Pipeline NLP.

1. **OCR (Optical Character Recognition):** Se i post contengono immagini (es: la foto di una carta d'imbarco o un badge aziendale), la libreria di Computer Vision elabora i frame per trasformare i pixel in testo analizzabile.
2. **SpaCy (Named Entity Recognition - NER):** Tutto il testo grezzo e OCRizzato passa attraverso modelli semantici pre-addestrati caricati in memoria (RAM). `SpaCy` tagga logicamente le parole individuando pattern (Regex) e regole linguistiche: se trova "Lavoro per Amazon Italia", identifica "Amazon Italia" come entità `ORGANIZATION`. Se trova un formato data vicino a "Oggi compio", estrae l'età o il compleanno. Questi dati taggati sono i PII che la Dashboard visualizzerà nel "PII Grid Widget".

---

## 5. Audit AI e Risk Engine Multilivello
Il blocco finale del sistema è la stesura dell'Audit di Rischio, demandata interamente a Modelli LLM Generativi avanzati.

### 5.1 Calcolo dello Score e Generazione Strutturata
Tutti i PII e le stringhe OSINT vengono aggregati in un JSON di Payload compresso (per eludere il limite dei token) inviato in input al LLM con un prompt di Inception ingegneristico che obbliga il modello a restituire un *JSON Strutturato*. Il modello AI valuta le minacce attive (es: "Trovato Numero di Telefono e Località, pericolo vishing alto") determinando il **Risk Score**.

### 5.2 High-Availability LLM (Circuit Breaker)
I servizi esterni (come le API OpenAI/Azure) possono collassare o restituire un errore di "Rate Limit" (`HTTP 429 Resource Exhausted`). Per mantenere i sistemi distribuiti resilienti, abbiamo implementato un **Fallback Sequenziale**:
1. L'orchestratore tenta prima l'interrogazione ai modelli primari su **GitHub Models (Azure AI)** (es. `gpt-4o-mini`).
2. Se il nodo fallisce, scatta un'eccezione non bloccante e l'orchestratore ripiega su un provider secondario: **Google Gemini**.
3. Se anch'esso fallisce o è in blackout, interviene **Groq (Llama 3 Vision)**.

*Snippet (Backend Python) - Pattern Circuit Breaker & Fallback:*
```python
async def risk_engine_analysis(payload):
    # Lista di tuple (Nome Provider, Funzione AI)
    providers = [
        ("GitHub Models", query_github_models_api),
        ("Google Gemini", query_gemini_api),
        ("Groq Llama Vision", query_groq_api)
    ]
    
    for name, provider_func in providers:
        try:
            logger.info(f"Tentativo di generazione Audit con {name}...")
            return await provider_func(payload) # Se riesce, esce e ritorna lo score
        except Exception as e:
            # Fallback in caso di HTTP 429 o Service Unavailable
            logger.warning(f"Provider {name} fallito. Ripiego sul prossimo nodo...")
            
    # Se tutti i livelli High-Availability crollano
    raise Exception("Tutti i provider AI hanno fallito (High Availability exhausted).")
```

Questa resilienza assicura che il backend ritorni *sempre* un report analitico alla Dashboard React, indipendentemente dalle condizioni di rete verso le infrastrutture dei provider esterni.

---

## 6. L'Infrastruttura di Hosting su Microsoft Azure (Sistemi Distribuiti)

Il progetto è architettato per un provisioning distribuito nativo cloud (`Lift and Shift` / Cloud Native) affidandosi interamente all'ecosistema **Microsoft Azure**. Nessun componente risiede fisicamente in un ambiente monolitico On-Premise.

1. **Static Web App Hosting per Frontend React (Azure Storage Account - `socialexposure`)**
   Il Frontend è stato disaccoppiato in asset statici. Viene hostato nativamente all'interno di un contenitore Blob configurato per l'erogazione di Siti Web Statici. Questo garantisce scalabilità automatica per servire la UI, costi che rasentano lo zero (si paga al millesimo di centesimo per gigabyte in uscita) e tempi di latenza irrisori grazie alla CDN implicita.
2. **Azure App Service (Compute per il Backend - `social-exposure-backend`)**
   Tutta la potenza di calcolo (Worker, NLP, Scraper, FastAPI) è devoluta all'App Service per container Linux. Appoggia le sue regole di fatturazione e scalabilità a un **App Service Plan (`ASP-SocialExposureRG...`)**. A differenza di una Macchina Virtuale (IaaS) classica in cui avremmo dovuto installare il SO e patchare Python a mano, l'App Service astrae il sistema operativo gestendo unicamente il runtime.
3. **Azure Container Registry (`socialexposureregistry`)**
   Lo store privato delle immagini Docker aziendali. Il backend viene buildato in un container Docker multistage e parcheggiato in questa registry (ACR). All'avvio dell'App Service, esso attinge direttamente in modo sicuro dal registro interno, consentendo un flusso di Continuous Deployment e la certezza dell'immutabilità ambientale (il classico "Sul mio PC funzionava").
4. **Persistenza Dati: Azure Database for PostgreSQL Flexible Server (`social-exposure-db`)**
   Il database relazionale che raccoglie gli storici JSON dei Risk Engine e le configurazioni utente. Adottare il livello *Flexible Server* significa che Azure posiziona il cluster SQL all'interno della stessa subnet di rete dell'App Service per abbattere drasticamente la latenza (in ottica di sistemi vicini di Network Layer). Il DB ha politiche di Auto-Vacuuming e Backup automatizzati in Cloud (PaaS gestito).

---

## 6. Sicurezza, Privacy e Conformità Legale (GDPR)
Trattando Dati Personali Identificabili (PII) e valutando i rischi di Social Engineering, l'applicativo è stato sviluppato tenendo in forte considerazione l'etica professionale e i dettami del **GDPR (General Data Protection Regulation)**:

1. **Fonti Pubbliche (OSINT):** Tutti i moduli di scraping (Sherlock, DuckDuckGo, Holehe) interrogano esclusivamente fonti OSINT accessibili pubblicamente. Non vengono effettuate intrusioni informatiche né bypassati sistemi di autenticazione per sottrarre database privati (Data Exfiltration).
2. **Uso Etico e Self-Auditing:** L'architettura è intesa per scopi di *Self-Auditing* (valutazione della propria impronta digitale) o per Red Teaming/Penetration Testing sotto esplicita autorizzazione contrattuale (RoE - Rules of Engagement).
3. **Minimizzazione dei Dati e Transitorietà:** Durante le esecuzioni, le stringhe sensibili e le immagini scaricate vengono processate in memoria (RAM) tramite Tensor Stream o buffer asincroni, e rilasciate dal Garbage Collector a ciclo terminato, evitando ridondanza di persistenza non necessaria.

---

## 7. Sicurezza Architetturale (Cybersecurity)
Essendo un progetto a forte vocazione *Cybersecurity*, il backend FastAPI integra nativamente soluzioni di irrobustimento (Hardening):

1. **PII Masking e Redaction nei Log:** Per evitare la potenziale violazione dei log (Log Poisoning o data leak interni), l'architettura include un *Interceptor Custom* su `Loguru`. Prima di essere stampate a schermo o scritte su disco, le mail o i telefoni passano per un filtro Regex che li occulta in modo proattivo (es. restituendo `[EMAIL-MASKED]`), proteggendo la riservatezza anche a livello di infrastruttura di debug.
2. **Protezione da Denial of Service (DoS) e Denial of Wallet:** Il componente Orchestratore implementa un algoritmo di troncamento dinamico sul "Payload Text" passato ai modelli LLM (con un cap di `100.000` caratteri). Questo previene scenari in cui un target con una timeline enorme possa causare esplosioni computazionali o esaurire il budget API dei provider AI.
3. **Protezione SSRF (Server-Side Request Forgery):** I moduli di Scraping e i resolver URL gestiscono dinamicamente stringhe di input inserite dall'utente. È stato implementato un filtraggio nativo sugli input HTTP per evitare che un attaccante utilizzi il server Azure come proxy per scansionare reti private interne (es. `127.0.0.1` o `169.254.169.254`).

---

## 8. Appendice: Utilizzo di AI Generativa nello Sviluppo
Come previsto dalla traccia del progetto, si dichiara in modo trasparente l'utilizzo di strumenti di Intelligenza Artificiale Generativa come ausilio allo sviluppo del codice, alla stesura della documentazione e al debugging.

**Strumenti Utilizzati:**
- **Antigravity IDE (Powered by Gemini / Google DeepMind):** Utilizzato per il Pair-Programming asincrono, refactoring del codice e setup dell'infrastruttura.
- **ChatGPT (OpenAI GPT-4o):** Utilizzato sporadicamente per la ricerca di librerie OSINT compatibili e risoluzione di bug specifici di dipendenze Python.

**Parti Sviluppate con ausilio AI e Prompt di Esempio:**

1. **Frontend (Dashboard React e Animazioni Tremor):**
   - *Prompt Principale:* "Crea una dashboard in React utilizzando TailwindCSS (stile glassmorphism) e i componenti di Tremor. Implementa un componente `RadialProgress` animato per il Risk Score (da 0 a 100) e un componente `TerminalLoading` che faccia short-polling su un endpoint FastAPI per mostrare log asincroni simulando un terminale hacker."
2. **Backend (Orchestratore Asincrono FastAPI):**
   - *Prompt Principale:* "Scrivi il main.py di FastAPI implementando un'architettura asincrona. Prevedi un endpoint POST /analyze che generi un UUID e deleghi a `BackgroundTasks` l'esecuzione parallela di Sherlock, script di scraping e pipeline NLP (SpaCy). L'endpoint deve ritornare HTTP 202 Accepted."
3. **Infrastruttura e DevOps (Docker & Azure):**
   - *Prompt Principale:* "Scrivi un Dockerfile multistage ottimizzato per FastAPI. Successivamente, genera una guida o gli script necessari per effettuare il deploy del container su Azure App Service associandolo ad un Azure Container Registry e a un database PostgreSQL Flexible Server."
4. **Risk Engine (Ingegneria dei Prompt per Fallback LLM):**
   - *Prompt Principale:* "Implementa un modulo `risk_engine.py` in Python che utilizzi il pattern Circuit Breaker. Deve tentare di chiamare prima l'API di GitHub Models (Azure AI); se riceve un errore 429, deve fare fallback su Gemini, e poi su Groq. Assicurati che l'output sia forzato in un formato JSON rigoroso descrivente minacce di social engineering."

