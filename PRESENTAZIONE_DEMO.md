# Script Presentazione Demo: Social Exposure Analyzer

Questo documento è pensato come un "canovaccio" discorsivo da seguire durante la presentazione live del progetto. Segue il flusso logico della demo (quello che l'esaminatore vede a schermo) e spiega in modo naturale le tecnologie sottostanti e l'infrastruttura Azure.

---

## 1. Introduzione (Schermata Home)
**Cosa fare:** Mostrare la Home Page pulita dell'applicativo web.

"Buongiorno a tutti. Oggi vi presento **Social Exposure Analyzer**.
Vorrei partire dal contesto in cui ci muoviamo: oggi la vera vulnerabilità informatica non è quasi mai legata a falle nel codice o a firewall bucati, ma all'anello più debole della catena di sicurezza: l'essere umano. Lasciamo ogni giorno una scia digitale enorme sui social network (nomi di parenti, abitudini, luoghi di lavoro, foto di viaggi). Tutte queste informazioni, seppur apparentemente innocue, una volta aggregate permettono a un attaccante di costruire profili psicologici precisi e sferrare attacchi di *Social Engineering* (Ingegneria Sociale) devastanti, come lo Spear Phishing.

L'obiettivo di questo strumento è proprio difenderci mettendo in luce i nostri punti ciechi. L'applicativo automatizza il lavoro certosino che farebbe un analista di cyber intelligence: raccoglie, correla e valuta enormi volumi di dati di pubblico dominio (una pratica nota come OSINT - Open Source Intelligence) per restituirci una reale metrica di esposizione al rischio.

Dal punto di vista tecnico, come potete vedere, l'interfaccia web è sviluppata in **React** come Single Page Application (SPA). Questo ci garantisce una navigazione fluida, senza ricaricamenti di pagina, con un design reattivo curato tramite TailwindCSS e la libreria Tremor per i futuri grafici."

---

## 2. L'Inserimento e l'Architettura Asincrona (Schermata "Hacker Terminal")
**Cosa fare:** Inserire l'utente di test (`marco_rossi_sec_99`) e avviare l'analisi. A schermo apparirà il terminale stile hacker che si aggiorna in tempo reale.

**Cosa dire:**
"Inserisco il nostro target di test. Qui è fondamentale fare una **precisazione etica**.
Le policy sulla privacy (come il GDPR) vietano lo scraping massivo e l'analisi non autorizzata di persone reali, persino per dati resi originariamente pubblici. Per rispettare rigorosamente il perimetro legale dell'Ethical Hacking, il sistema analizza solo ciò per cui siamo autorizzati. Il profilo che sto inserendo, `marco_rossi_sec_99`, è un'identità sintetica (un *dummy account* controllato) creato appositamente con vulnerabilità "finte" iniettate ad arte per dimostrarvi il funzionamento senza ledere la privacy di alcun utente reale.

Non appena premo 'Analizza', voglio soffermarmi su cosa succede *esattamente in questo momento* dietro le quinte.
Un'analisi OSINT profonda richiede svariati minuti per il completamento. Se avessimo usato un web server sincrono tradizionale, l'infrastruttura si sarebbe bloccata in attesa della risposta dai social, paralizzando l'applicativo per tutti gli altri utenti connessi.

Per evitare questo collo di bottiglia, il nostro backend in **FastAPI** implementa un pattern architetturale **Produttore-Consumatore asincrono**. Non appena ho lanciato la richiesta, il server ha restituito istantaneamente un codice HTTP `202 Accepted` al client e ha delegato il lavoro pesante a un Pool di Worker in background.

Quello che state vedendo a schermo è un terminale simulato gestito da **React Query** tramite **Short Polling intelligente**. Il frontend sta interrogando il server ogni 800 millisecondi per farsi inviare i log. L'ottimizzazione è che, per risparmiare banda e risorse di calcolo, questo ping martellante si spegne in automatico (restituendo `false`) non appena il server dichiara concluso il task."

---

## 3. Il Motore OSINT e l'Anti-Bot (Durante il caricamento)
**Cosa fare:** Mentre il terminale avanza, spiegare come vengono recuperati i dati.

**Cosa dire:**
"Mentre l'interfaccia attende, vi racconto cosa fa materialmente il worker in background.
Il sistema orchestra svariate pipeline in parallelo. Ad esempio, per scoprire a quali piattaforme è iscritto il bersaglio, usa un attacco laterale (*Side-Channel*): invia false richieste di recupero password a oltre 120 domini web. Sfruttando la reazione dei server, deduce l'esistenza dell'account senza mai allertare l'utente finale.

Poi passa ai social, come Instagram. I social moderni hanno difese anti-bot spietate basate sull'IA che impediscono la navigazione a chi non è loggato (il cosiddetto "Login Wall").
Per aggirare il muro usiamo una tecnica di *Impersonation*: preleviamo dal frontend il cookie `sessionid` di un nostro account fittizio e lo iniettiamo negli header delle richieste HTTP in Python. Così facendo Meta crede di parlare con un browser umano autenticato. La differenza nell'estrazione è abissale: con il `sessionid` possiamo scavare a fondo nello storico del target, estrarre mesi di post, coordinate GPS e mappare l'albero completo delle interazioni.

Tuttavia, le API possono fiutare l'inganno del bot. Se Meta ci blocca restituendo un errore `403 Forbidden`, la nostra infrastruttura non va mai in *Hard Crash*. Subentra il pattern di **Graceful Degradation** (Degrado Controllato): il sistema intercetta l'errore, elimina preventivamente il cookie `sessionid` "bruciato" e riesegue l'attacco in modalità 'Ospite Pubblico Non Autenticato'. Senza cookie torniamo ad essere visitatori anonimi: Instagram ci sbatte in faccia il Login Wall quasi subito bloccandoci foto e amicizie, ma il nostro sistema fa in tempo a estrarre i dati di superficie (come la Biografia pubblica e il nome reale) salvando comunque la pipeline dall'interruzione."

---

## 4. Analisi Dati: NLP e OCR
**Cosa fare:** Quando l'analisi finisce e appare il report coi dati estratti.

**Cosa dire:**
"L'estrazione è terminata. Abbiamo raccolto enormi volumi di testi e immagini, ma i dati grezzi non servono a nulla se non ne estraiamo il significato. È qui che avviene la vera magia.

Invece di usare semplici espressioni regolari (Regex) che cercano parole fisse, passiamo tutto il testo a un engine di **NLP (Natural Language Processing)** basato sulla rete neurale **SpaCy**. SpaCy analizza la grammatica e il contesto: se legge 'Ieri a Milano con Luca', capisce matematicamente che 'Milano' è un'entità geopolitica e 'Luca' è una persona, trasformandoli in PII (Personally Identifiable Information).

Ma le persone spesso fotografano badge aziendali o biglietti aerei, credendo che il testo nelle immagini sia invisibile agli scraper. Per colmare questa grave vulnerabilità, usiamo una rete neurale di visione artificiale (**EasyOCR**). L'algoritmo cerca i *Bounding Box* nell'immagine, legge i pixel, li traduce in testo digitale e li rigetta nel motore NLP. Nessun dato sfugge all'analisi."

---

## 5. Risk Engine e Circuit Breaker (Il Report Finale)
**Cosa fare:** Mostrare lo score finale (es. Rischio 85/100) e il JSON.

**Cosa dire:**
"Arriviamo al verdetto finale. Tutti i PII estratti vengono compressi e inviati a un LLM Generativo per una valutazione probabilistica. 
In un sistema distribuito non possiamo accettare risposte discorsive ("Ciao, ecco i tuoi dati..."). Abbiamo applicato un'*Ingegneria del Prompt* severissima: imponiamo al modello di rispondere **esclusivamente** in un formato JSON strutturato. Questo ci permette di mappare direttamente la risposta sui componenti React per disegnare i grafici che vedete a schermo, senza far crashare l'app.

Un dettaglio architetturale di livello enterprise di cui vado fiero è l'Affidabilità (*High-Availability*). Cosa succede se i server mondiali vanno giù o se esauriamo il budget API (Errore 429)?
Non dipendiamo da un singolo fornitore. Abbiamo implementato un **Circuit Breaker Sequenziale dinamico**. Il backend legge il provider primario dalle variabili d'ambiente; se la rete fallisce, l'eccezione viene soppressa in una frazione di secondo e il carico viene deviato istantaneamente su un nodo di fallback (da GitHub Models, a Gemini, a Groq). L'utente non si accorge di nulla e riceve sempre il suo report."

---

## 6. L'Infrastruttura Cloud: Microsoft Azure e CI/CD
**Cosa fare:** Aprire per un attimo la schermata del Resource Group sul portale Azure, oppure lo screen delle GitHub Actions.

**Cosa dire:**
"Infine, un rapido sguardo a dove 'gira' tutto questo. Abbiamo scartato le macchine virtuali classiche a favore di un approccio 100% Cloud-Native basato su servizi gestiti (PaaS) su **Microsoft Azure**.

1. Il **Frontend** è un sito statico su *Azure Storage Account*. Zero server fisici, scala all'infinito e sfrutta la rete CDN mondiale per una latenza nulla.
2. Il **Backend** FastAPI è racchiuso in un'immagine *Docker* immutabile, ospitata su *Azure App Service*.
3. Il **Database** PostgreSQL è un *Flexible Server*. E qui c'è una finezza: è confinato all'interno di una *Virtual Network (VNet) privata*. Parla con il backend in locale abbattendo i tempi del TCP Handshake e isolandosi totalmente da internet.

Tutta l'infrastruttura è governata da una pipeline DevOps. Non c'è alcun caricamento manuale. Grazie a **GitHub Actions**, mi basta lanciare un comando `git push`: i server compilano il codice, costruiscono i container e li iniettano nell'Azure Container Registry. Tramite Webhook, l'App Service avvia i nuovi container e spegne i vecchi solo quando sono pronti, garantendo un vero *Zero-Downtime Deployment*."

---

## 7. Conclusione: Sicurezza (Hardening & Privacy)
**Cosa dire a chiusura:**
"L'ultimo pilastro è la Cybersecurity dell'infrastruttura stessa. In ambiente cloud, caricare i file `.env` contenenti le password è un rischio gravissimo. Abbiamo optato per gli *OS-Level Secrets*: le chiavi crittografiche vengono lette e iniettate in memoria direttamente dalle Environment Variables del portale Azure.
Inoltre, per prevenire il 'Log Poisoning' (ovvero il rischio che i file diagnostici si riempiano di password o passaporti finendo nelle mani sbagliate dei DevOps), il sistema implementa un *PII Masking* automatico: oscura mail e numeri di telefono a monte, prima ancora che vengano trascritti su disco.

Vi ringrazio per l'attenzione. Se ci sono domande, sono a vostra disposizione."

---

## 8. FAQ: Difesa del "Sistema Distribuito" (Da tenere a mente)
**Se un professore chiede:** *"Perché questo è un sistema distribuito e non un semplice sito web caricato online?"*

**Cosa rispondere con sicurezza:**
"Questo progetto rispetta i tre canoni fondamentali di un sistema distribuito: l'assenza di memoria globale condivisa, la concorrenza e la tolleranza ai fallimenti parziali. 
Non è un monolite eseguito su una singola macchina, ma un'architettura 3-Tier profondamente disaccoppiata. 

Il client React sul browser dell'utente (Nodo 1), il container FastAPI su App Service (Nodo 2), il Database PostgreSQL isolato in VNet (Nodo 3) e i Nodi di Intelligenza Artificiale esterni (Nodo 4, 5, 6) non condividono la stessa CPU o memoria fisica. Coordinano le loro azioni *esclusivamente* scambiandosi messaggi su reti eterogenee (tramite API REST, Short Polling e chiamate RPC). 
Inoltre, il progetto implementa pattern tipici del calcolo distribuito per governare l'inaffidabilità della rete, come l'esecuzione asincrona Produttore-Consumatore e il Circuit Breaker per deviare il traffico quando un nodo remoto collassa, garantendo la Fault Tolerance."
