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
"Mentre attendiamo, vi spiego come il worker in background sta recuperando i dati:
Esegue pipeline parallele. Ad esempio usa tecniche di side-channel (Holehe) per indovinare gli account legati alle email, e naviga i profili social (come Instagram).

I social moderni hanno fortissime difese anti-bot. Noi le aggiriamo tramite *Impersonation*, iniettando nei pacchetti Python le sessioni crittografate di un browser reale.
Ma se Meta dovesse bloccare il nostro cookie? L'infrastruttura non va mai in crash: entra in gioco il pattern di **Graceful Degradation** (Degrado Controllato). Il sistema capta l'errore `403 Forbidden`, getta via il cookie bannato e ripiega in tempo reale in una modalità 'Ospite Pubblico', assicurandosi di portare a casa almeno i dati basilari per l'audit."

---

## 4. Analisi Dati: NLP e OCR
**Cosa fare:** Quando l'analisi finisce e appare il report coi dati estratti.

**Cosa dire:**
"L'estrazione è completata. Abbiamo raccolto testo e immagini, ma il testo grezzo non serve a nulla se non ne capiamo il significato.
È qui che entra in gioco l'Intelligenza Artificiale.

Passiamo tutti i testi al nostro layer **NLP (Natural Language Processing)** basato sulla rete neurale **SpaCy**. Lei non cerca parole chiave con regole matematiche fisse, ma comprende la semantica del discorso per estrarre i PII (Dati Personali Identificabili come Luoghi, Nomi o Aziende).

Inoltre, se il target ha postato una foto (magari del suo biglietto aereo), una seconda rete neurale di Computer Vision (**EasyOCR**) analizza i pixel, legge il testo nella foto, e lo rigetta nel motore NLP per trovare vulnerabilità nascoste."

---

## 5. Risk Engine e Circuit Breaker (Il Report Finale)
**Cosa fare:** Mostrare lo score finale (es. Rischio 85/100) e il JSON.

**Cosa dire:**
"Arriviamo al verdetto. Abbiamo demandato la stesura dell'Audit finale a un LLM Generativo (come ChatGPT). 
Tramite un'Ingegneria del Prompt rigorosa, costringiamo il modello a rispondere *esclusivamente* in un formato JSON strutturato, essenziale per disegnare questi grafici in React senza far crashare l'app.

Un dettaglio architetturale di cui vado molto fiero è l'Affidabilità. Cosa succede se i server mondiali di Google Gemini vanno giù o esauriamo il budget API?
Abbiamo implementato un **Circuit Breaker Sequenziale**. Il backend cerca di usare il provider primario (letto in modo sicuro dalle variabili del server). Se la chiamata fallisce, intercetta l'errore e devia istantaneamente il traffico di fallback verso Gemini, per poi scalare su Groq. Il risultato è che l'utente non sperimenta mai un disservizio."

---

## 6. L'Infrastruttura Cloud: Microsoft Azure e CI/CD
**Cosa fare:** Aprire per un attimo la schermata del Resource Group sul portale Azure, oppure lo screen delle GitHub Actions.

**Cosa dire:**
"Infine, dove 'gira' tutto questo? L'intera infrastruttura ha subìto un *Lift & Shift* diventando 100% Cloud-Native su **Microsoft Azure** tramite servizi gestiti (PaaS).

1. Il **Frontend** è ospitato su uno *Storage Account* come sito statico. Avendo zero server fisici, scala all'infinito e sfrutta la rete mondiale CDN di Azure per una latenza istantanea.
2. Il **Backend** FastAPI è incapsulato in un'immagine *Docker*, isolata e immutabile, in esecuzione su un *Azure App Service Linux*.
3. Il **Database** (dove salviamo i log) è un *PostgreSQL Flexible Server* confinato in una VNet privata per massima sicurezza e prossimità di rete.

Tutto questo è governato da pura automazione (DevOps). Non copio più file a mano: grazie alle **GitHub Actions**, mi basta un comando `git push` dal computer. I server di GitHub intercettano il codice, compilano l'app, buildano il Docker e aggiornano Azure in *Zero-Downtime Deployment*. Nessuna interruzione, l'applicazione si aggiorna da sola."

---

## 7. Conclusione: Sicurezza
"L'ultimo pilastro è la Cybersecurity. Non abbiamo nessun file testuale `.env` esposto in produzione. Le chiavi crittografiche (API Key e Database) ci vengono iniettate in modo cifrato direttamente dal sistema operativo (*OS-Level Secrets*). Inoltre, i nostri log server sono progettati per oscurare automaticamente mail e numeri di telefono prima di scriverli su disco, neutralizzando i rischi di esfiltrazione collaterale."
