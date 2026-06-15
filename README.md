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
  <p><em>Figura 4: Interfaccia di Benvenuto e Avvio Scansione. L'invio del modulo innesca l'endpoint asincrono.</em></p>
</div>

<div align="center">
  <img src="docs/images/loading.png" alt="Terminale Hacker" width="800">
  <p><em>Figura 5: Terminale simulato e Feedback in tempo reale (Short Polling asincrono).</em></p>
</div>

<div align="center">
  <img src="docs/images/score.png" alt="Score" width="800">
  <p><em>Figura 6: Indice di Rischio e Breakdown Matematico deterministico basato su vulnerabilità.</em></p>
</div>

<div align="center">
  <img src="docs/images/dati_sensibili.png" alt="Dati Sensibili" width="800">
  <p><em>Figura 7: Grid dei Dati Sensibili Estrapolati (PII) tramite reti neurali NLP e OCR.</em></p>
</div>

<div align="center">
  <img src="docs/images/post_analysis.png" alt="Dashboard" width="800">
  <p><em>Figura 8: Dashboard Globale dell'Audit OSINT completato con feed OCR e telemetria.</em></p>
</div>

<div align="center">
  <img src="docs/images/audit_ai.png" alt="Rapporto AI" width="800">
  <p><em>Figura 9: Valutazione AI qualitativa e Piani di Mitigazione delle Minacce.</em></p>
</div>
