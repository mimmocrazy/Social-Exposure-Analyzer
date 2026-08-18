# Social-Exposure-Analyzer

> Cloud-native OSINT framework & cyber intelligence engine for automated PII extraction and social engineering risk scoring.

`Social-Exposure-Analyzer` è un applicativo web full-stack progettato per l'Ethical Hacking e la Cyber Intelligence. Automatizza la raccolta, l'analisi e la validazione di dati provenienti da fonti aperte (**OSINT - Open Source Intelligence**), quantificando deterministicamente l'esposizione al rischio di *Social Engineering* di un bersaglio tramite Reti Neurali, OCR e Modelli LLM Multimodali.

---

## Highlights

| Feature | Details |
| :--- | :--- |
| **OSINT Target Deduction** | Deduce probabilisticamente il nome reale partendo dal nickname prima dello scraping, potenziando l'ispezione |
| **Vision AI & Multimodal OCR** | Estrazione testo da immagini (EasyOCR) e deduzione contestuale di relazioni invisibili (*Vision Context*) via LLM multimodali |
| **Asynchronous Concurrency** | Fino a **120 attacchi enumerativi paralleli** via `asyncio` (modulo Holehe) con bypass Login Wall (*Impersonation* & *Graceful Degradation*) |
| **Data Breach Detection** | Rilevamento in tempo reale di password ed esposizioni interrogando l'API pubblica di **XposedOrNot** |
| **Privacy by Design** | Algoritmo di *Data Stripping* che rimuove le immagini (Base64) prima delle chiamate AI in Cloud, azzerando colli di bottiglia sui token |
| **Fault Tolerance** | Pattern Produttore-Consumatore e **Circuit Breaker** per garantire resilienza operativa e tolleranza ai guasti |

---

## System Architecture

Architettura distribuita a microservizi (3-Tier):

| Tier | Component | Technology & Cloud Deployment |
| :--- | :--- | :--- |
| **Frontend** | React SPA (Interfaccia Terminale Hacker in *Short Polling*) | Hostato su **Azure Storage Account** (Static website `$web`) |
| **Backend** | Orchestratore asincrono & Risk Engine | **FastAPI** containerizzato su **Azure App Service** (Linux) |
| **Database** | Persistenza isolata (senza esposizione pubblica) | **PostgreSQL Flexible Server** deployato su *Virtual Network privata* |
| **CI/CD & Registry** | Container Image Management & Delivery | **Azure Container Registry (ACR)** + **GitHub Actions** |

---

## Quick Start

Compatibile nativamente con **Linux**, **macOS** e **Windows** *(Prerequisiti: Python 3.12+, Node.js 18+ e npm)*.

```bash
# 1. Clone repository
git clone https://github.com/mimmocrazy/Social-Exposure-Analyzer.git ~/Projects/Social-Exposure-Analyzer
cd ~/Projects/Social-Exposure-Analyzer

# 2. Setup isolated virtual environment & dependencies
python3 -m venv venv
source venv/bin/activate   # Su Windows: venv\Scripts\activate
make install

# 3. Launch Backend API (Terminal 1 - http://localhost:8000)
source venv/bin/activate
make b

# 4. Launch Frontend Web UI (Terminal 2 - http://localhost:5173)
make f
```

> [!WARNING]
> Non copiare mai la cartella dell'ambiente virtuale `venv` da un sistema operativo all'altro. Costruiscila sempre da zero sul nuovo sistema.

---

## Microsoft Azure Deployment

L'infrastruttura cloud PaaS su Microsoft Azure è interamente configurata e pronta all'uso. Per contenere i costi di esercizio, i servizi possono essere riattivati a richiesta dal portale Azure:

| Resource | Service | Activation / Notes |
| :--- | :--- | :--- |
| **PostgreSQL DB** | Azure Database Flexible Server | Portale Azure > Flexible Server > **Start** *(~2 min di ripristino)* |
| **Backend API** | Azure App Service (FastAPI Linux) | Portale Azure > App Service > **Start** *(Upgrade a piano Premium V4 per benchmark)* |
| **Container Registry** | Azure Container Registry (ACR) | Sempre attivo; CI/CD automatica su `git push` via GitHub Actions |
| **Frontend Static** | Azure Storage Account | Sempre attivo; interfaccia statica nel container `$web` |

### Production Endpoints

| Endpoint | Location |
| :--- | :--- |
| **Frontend URL** | Storage Account > *Static website* > **Primary endpoint** |
| **Backend URL** | App Service > *Overview* > **Default domain** |

---

## Gallery

<div align="center">
  <img src="docs/images/home.png" alt="Homepage" width="800">
  <p><em><strong>Figura 1: Interfaccia di Benvenuto e Avvio Scansione.</strong> Inserimento username o URL diretto del target, con abilitazione selettiva dei moduli (Dork Engine, Holehe, Facebook Scan) e profondità di analisi.</em></p>
  <br/>

  <img src="docs/images/loading.png" alt="Terminale Hacker" width="800">
  <p><em><strong>Figura 2: Terminale Simulato e Feedback in Tempo Reale.</strong> Polling asincrono per monitorare discovery, estrazione media e analisi NLP durante l'esecuzione del processo OSINT.</em></p>
  <br/>

  <img src="docs/images/score.png" alt="Score" width="800">
  <p><em><strong>Figura 3: Sezione Indice di Rischio e Breakdown Matematico.</strong> Score complessivo, barre di esposizione per aree tematiche (Identità, Network, Routine) e scoring deterministico.</em></p>
  <br/>

  <img src="docs/images/dati_sensibili.png" alt="Dati Sensibili" width="800">
  <p><em><strong>Figura 4: Grid dei Dati Sensibili Estrapolati (PII).</strong> Informazioni anagrafiche, di contatto, geografiche e aziendali identificate da NLP e OCR con sorgente e livello di confidenza.</em></p>
  <br/>

  <img src="docs/images/post_analysis.png" alt="Dashboard" width="800">
  <p><em><strong>Figura 5: Dashboard Globale dell'Audit OSINT completato.</strong> Vista d'insieme degli indici aggregati, telemetria di esecuzione dei moduli OSINT (Sherlock, Holehe, Dork Engine) e carosello OCR nativo.</em></p>
  <br/>

  <img src="docs/images/audit_ai.png" alt="Rapporto AI" width="800">
  <p><em><strong>Figura 6: Valutazione AI e Piano di Mitigazione delle Minacce.</strong> Analisi qualitativa redatta dal Risk Engine AI ed elenco atomico delle azioni di mitigazione protette da Circuit Breaker.</em></p>
</div>

---

## License

Distributed under the [MIT License](LICENSE). Copyright © 2026 Mimmo.
