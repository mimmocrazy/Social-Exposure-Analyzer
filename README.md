# Social Exposure Analyzer

## 📖 Descrizione del Progetto
**Social Exposure Analyzer** è un applicativo progettato per automatizzare la raccolta, l'analisi e la validazione di dati provenienti da fonti aperte (**OSINT - Open Source Intelligence**). L'obiettivo principale è quantificare e valutare l'esposizione al rischio di ingegneria sociale (Social Engineering) di un determinato bersaglio tramite intelligenza artificiale.

L'architettura si basa sul paradigma dei microservizi:
- **Backend (FastAPI in Python):** Orchestratore asincrono ad alte prestazioni. Disaccoppia la raccolta dati tramite un pattern produttore-consumatore. Integra pipeline OSINT complesse (Sherlock, Holehe, Dork Engine) e moduli di analisi NLP/OCR. Dispone di un "Risk Engine AI" coperto da pattern Circuit Breaker per garantire resilienza intercettando fallimenti tra modelli AI multipli (Azure, Google Gemini, Groq).
- **Frontend (React SPA):** Layer di presentazione interattivo basato su TailwindCSS e componenti analitici Tremor. Interroga il backend tramite polling per simulare un terminale hacker in tempo reale, per poi mostrare metriche aggregate sui dati sensibili trapelati (PII) e presentare una dashboard quantitativa e qualitativa globale di mitigazione.

---

## 🚀 Guida all'installazione locale

Il progetto è compatibile nativamente con **Windows**, **Linux** e **macOS**. 
*(Attenzione: non copiare mai la cartella dell'ambiente virtuale `venv` da un sistema operativo all'altro. Costruiscila sempre da zero sul nuovo sistema come descritto di seguito).*

### Prerequisiti
1. **Python 3.12+** installato e aggiunto al PATH del tuo sistema.
2. **Node.js (versione 18+)** e `npm` installati (necessari per compilare ed eseguire il frontend).

### 1. Inizializzazione dell'Ambiente
Apri il terminale nella cartella principale del progetto ed esegui i seguenti comandi per inizializzare l'applicazione da zero:

```bash
# 1. Crea un nuovo ambiente virtuale isolato (obbligatorio su ogni nuovo OS)
python -m venv venv     # (Su alcune distro Linux potrebbe essere necessario: python3 -m venv venv)

# 2. Attiva l'ambiente virtuale
# Su Windows:
venv\Scripts\activate
# Su Linux/macOS:
source venv/bin/activate

# 3. Scarica e installa tutte le librerie necessarie tramite il comando Make (installa sia pip che npm)
make install
```

### 2. Avvio dei Servizi (Sviluppo Locale)
L'architettura prevede due macro-servizi (Backend API e Frontend React) che devono essere mantenuti in esecuzione simultaneamente in due finestre di terminale separate.

**Terminale 1 (Backend FastAPI):**
```bash
# Assicurati che l'ambiente virtuale sia attivo (venv)
make b
```
*Il backend si avvierà in ascolto sulla porta locale http://localhost:8000*

**Terminale 2 (Frontend React):**
```bash
# Qui non serve l'ambiente virtuale Python
make f
```
*Il tool Vite avvierà l'interfaccia utente web (di default su http://localhost:5173).*

---

## ☁️ Checklist Riattivazione Ambiente Microsoft Azure

L'infrastruttura cloud di questo progetto (appoggiata ai servizi PaaS di Microsoft Azure) **è già stata interamente creata e configurata**. Tuttavia, alcune risorse potrebbero essere state **messe in pausa** per ottimizzare e contenere i costi durante i periodi di inattività. 

Prima di testare il software in produzione, verifica e riattiva questi componenti dal portale Azure:

1. **Azure Database for PostgreSQL (Flexible Server)**
   - Il database è spesso la prima risorsa ad essere spenta. Entra nel portale, cerca il tuo PostgreSQL Flexible Server.
   - Se lo stato risulta in *Stopped*, clicca su **Start** (Riprendi).
   - *Nota: Possono volerci un paio di minuti prima che il server torni a rispondere alle query.*

2. **Azure App Service (Backend FastAPI Linux)**
   - Anche l'App Service potrebbe essere stato fermato. Se risulta fermo, premi **Start**.
   - Assicurati nel pannello *Environment variables* che i Token AI e la stringa di connessione al Database siano ancora aggiornati.

3. **Azure Container Registry (ACR) e GitHub Actions**
   - Il registro immagini non prevede il concetto di "Pausa", è sempre attivo. Avendo configurato una pipeline di CI/CD, qualsiasi modifica locale al codice del backend verrà automaticamente testata, compilata in Docker e caricata sull'ACR non appena farai un `git push` sul branch `main`. L'App Service percepirà l'aggiornamento e si riavvierà da solo.

4. **Azure Storage Account (Frontend Static Web App)**
   - Similmente all'ACR, lo Storage rimane attivo e i file del sito statico React sono nel container `$web`. Qualora apportassi modifiche al frontend, esegui una nuova build locale (`npm run build`) e sovrascrivi i file nella cartella di Azure.

### 🔗 Come Trovare l'Indirizzo Pubblico (URL) del Sito
Una volta che tutto è attivo e funzionante, potrai visitare il tuo sito tramite i seguenti link forniti da Azure:

- **L'URL del Sito Web (Frontend):** 
  Vai nella pagina del tuo **Storage Account** sul portale Azure. Nel menu a sinistra clicca su **Static website**. Troverai un campo chiamato **Primary endpoint** (sarà simile a `https://<nome>.z6.web.core.windows.net/`). Clicca su questo link per accedere all'interfaccia utente.
- **L'URL del Backend (API):**
  Vai nella pagina del tuo **App Service**. Nella schermata principale (Overview), troverai la voce **Default domain** (es. `https://<nome>.azurewebsites.net`). 
  *(Ricorda: Se il frontend in cloud non riesce a connettersi al backend, assicurati che il codice React sia configurato per effettuare le chiamate API verso questo dominio "Default domain" anziché verso `localhost`).*

*Non appena Database e App Service saranno riportati nello stato "Running", l'intera infrastruttura cloud tornerà operativa al 100%!*
