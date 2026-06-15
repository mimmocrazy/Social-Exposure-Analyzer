# 🛡️ Social Exposure Analyzer

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.0%2B-61DAFB?logo=react&logoColor=white)
![Azure](https://img.shields.io/badge/Microsoft_Azure-0089D6?logo=microsoft-azure&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)

**Social Exposure Analyzer** è un applicativo web progettato per l'Ethical Hacking e la Cyber Intelligence. Automatizza la raccolta, l'analisi e la validazione di dati provenienti da fonti aperte (**OSINT - Open Source Intelligence**), quantificando l'esposizione al rischio di *Social Engineering* di un bersaglio tramite l'uso di Reti Neurali e LLM.

---

## ✨ Funzionalità Principali (Engineering Highlights)
- **🧠 OSINT Target Deduction:** Deduce probabilisticamente il nome reale partendo da un nickname prima dello scraping, potenziando le ispezioni.
- **👁️ Vision AI & OCR:** Traduce immagini (badge, biglietti) in testo tramite EasyOCR e deduce relazioni familiari/lavorative invisibili ("Vision Context") usando modelli LLM multimodali.
- **⚡ Concorrenza Asincrona:** Sfrutta `asyncio` per lanciare fino a 120 attacchi enumerativi Side-Channel in parallelo (modulo Holehe) e aggirare i Login Wall tramite *Impersonation* e *Graceful Degradation*.
- **🔐 Data Breach Detection:** Rileva dinamicamente esposizioni password interrogando in tempo reale l'API pubblica di XposedOrNot.
- **🛡️ Privacy by Design:** L'algoritmo di *Data Stripping* rimuove rigorosamente le foto (Base64) prima di interpellare l'Intelligenza Artificiale in Cloud, massimizzando la privacy e azzerando i colli di bottiglia sui Token.

---

## 🏗️ Architettura di Sistema (3-Tier)
Il progetto rispetta i paradigmi dei sistemi distribuiti ed è strutturato a microservizi:
1. **Frontend (React SPA):** Interfaccia interattiva con simulazione "Terminale Hacker" in *Short Polling*. (Ospitata su *Azure Storage Account*).
2. **Backend (FastAPI):** Orchestratore asincrono basato su pattern Produttore-Consumatore e Circuit Breaker per tolleranza ai guasti. (Containerizzato su *Azure App Service*).
3. **Database (PostgreSQL):** Persistenza dei dati isolata senza esposizione pubblica. (Deployato in *Virtual Network privata* su Azure Flexible Server).

---

## 🚀 Guida all'Installazione Locale

Il progetto è compatibile nativamente con **Windows**, **Linux** e **macOS**. 

> [!WARNING]
> Non copiare mai la cartella dell'ambiente virtuale `venv` da un sistema operativo all'altro. Costruiscila sempre da zero sul nuovo sistema.

### Prerequisiti
- **Python 3.12+** aggiunto al PATH del sistema.
- **Node.js (versione 18+)** e `npm`.

### 1. Inizializzazione dell'Ambiente
Apri il terminale nella root del progetto ed esegui:
```bash
# 1. Crea un nuovo ambiente virtuale isolato
python -m venv venv     

# 2. Attiva l'ambiente virtuale
venv\Scripts\activate      # Su Windows
source venv/bin/activate   # Su Linux/macOS

# 3. Scarica e installa tutte le dipendenze (Backend e Frontend)
make install
```

### 2. Avvio dei Servizi (Sviluppo Locale)
Mantieni aperti due terminali separati per avviare i servizi in parallelo.

**Terminale 1 (Backend FastAPI):**
```bash
# Assicurati che l'ambiente virtuale sia attivo
make b
```
*In ascolto su: `http://localhost:8000`*

**Terminale 2 (Frontend React):**
```bash
# Qui non serve l'ambiente virtuale Python
make f
```
*In ascolto su: `http://localhost:5173`*

---

## ☁️ Checklist Riattivazione Ambiente Microsoft Azure

L'infrastruttura cloud PaaS su Microsoft Azure **è già interamente configurata e pronta all'uso**. Tuttavia, per contenere i costi, alcune risorse (come i server) potrebbero essere state messe in pausa. Prima di avviare una presentazione, riattiva i seguenti componenti dal portale Azure:

1. **🗄️ Azure Database for PostgreSQL (Flexible Server)**
   - Cerca il Flexible Server e se lo stato è *Stopped*, clicca su **Start**. *(Attendi ~2 minuti per il ripristino).*
2. **⚙️ Azure App Service (Backend FastAPI Linux)**
   - Se l'App Service risulta fermo, assicurati di avviarlo o di fare un Upgrade del piano tariffario (es. *Premium V4*) per massimizzare la velocità RAM/CPU durante i test. 
3. **📦 Azure Container Registry (ACR) e GitHub Actions**
   - Sempre attivo. La CI/CD aggiorna automaticamente i container in cloud al comando `git push`.
4. **🌐 Azure Storage Account (Frontend)**
   - Sempre attivo. L'interfaccia statica risiede nel container `$web`.

### 🔗 Indirizzi Pubblici (Produzione)
- **Frontend URL:** Nella pagina dello Storage Account > *Static website* > **Primary endpoint**.
- **Backend URL:** Nella pagina dell'App Service > *Overview* > **Default domain**.

---

## 🖼️ Galleria Applicativo

<div align="center">
  <img src="docs/images/home.png" alt="Homepage" width="800">
  <p><em><strong>Figura 1: Interfaccia di Benvenuto e Avvio Scansione.</strong> La schermata iniziale offre all'utente la possibilità di inserire lo username o l'URL diretto del target, consentendo l'abilitazione selettiva dei moduli di scansione (Dork Engine, Holehe, Facebook Scan) e la scelta della profondità di analisi. L'invio del modulo innesca l'orchestrazione asincrona in background.</em></p>
</div>

<div align="center">
  <img src="docs/images/loading.png" alt="Terminale Hacker" width="800">
  <p><em><strong>Figura 2: Terminale simulato e Feedback in tempo reale.</strong> Durante il processo OSINT, il frontend interroga il backend tramite polling asincrono per restituire all'utente un output visuale istantaneo del processo d'indagine in corso (discovery, estrazione media, analisi NLP).</em></p>
</div>

<div align="center">
  <img src="docs/images/score.png" alt="Score" width="800">
  <p><em><strong>Figura 3: Sezione Indice di Rischio e Breakdown Matematico.</strong> Il widget illustra lo Score di Rischio complessivo, le barre di esposizione per aree tematiche (Identità, Network, Routine) e il breakdown analitico dei punti assegnati deterministicamente in base alle vulnerabilità riscontrate.</em></p>
</div>

<div align="center">
  <img src="docs/images/dati_sensibili.png" alt="Dati Sensibili" width="800">
  <p><em><strong>Figura 4: Grid dei Dati Sensibili Estrapolati (PII).</strong> Ciascuna card raggruppa le informazioni anagrafiche, di contatto, geografiche o aziendali identificate tramite NLP neurale e OCR visivo, arricchite con dettagli sulla sorgente del dato e sul livello di confidenza associato.</em></p>
</div>

<div align="center">
  <img src="docs/images/post_analysis.png" alt="Dashboard" width="800">
  <p><em><strong>Figura 5: Dashboard Globale dell'Audit OSINT completato.</strong> La vista d'insieme raccoglie gli indici aggregati di esposizione, la telemetria di esecuzione dei singoli moduli OSINT (Sherlock, Holehe, Dork Engine) e il feed OCR nativo con carosello interattivo.</em></p>
</div>

<div align="center">
  <img src="docs/images/audit_ai.png" alt="Rapporto AI" width="800">
  <p><em><strong>Figura 6: Valutazione AI e Piano di Mitigazione delle Minacce.</strong> Questa sezione raccoglie l'analisi qualitativa discorsiva redatta dal Risk Engine AI e l'elenco atomico dei piani di mitigazione proposti per contenere l'esposizione sui singoli vettori d'attacco, il tutto processato con un meccanismo di tolleranza ai guasti (Circuit Breaker).</em></p>
</div>
