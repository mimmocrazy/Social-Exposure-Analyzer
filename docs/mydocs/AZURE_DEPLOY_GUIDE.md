# Guida Completa al Deploy su Microsoft Azure e Automazione CI/CD

Questa guida documenta l'architettura Cloud Native e il processo di deployment automatizzato del progetto **Social Exposure Analyzer**.
Tutta l'infrastruttura è ospitata su Microsoft Azure sfruttando il piano gratuito per studenti (Azure for Students).

## 🏗️ Panoramica dell'Architettura Cloud
- **Database:** Azure Database for PostgreSQL (Flexible Server, B1ms).
- **Backend:** Azure App Service (Linux, F1 Free Tier) in esecuzione tramite un'immagine Docker personalizzata.
- **Image Registry:** Azure Container Registry (Basic Tier) per archiviare le immagini Docker del backend.
- **Frontend:** Azure Storage Account (Static Website Hosting) per servire l'applicazione React SPA.
- **CI/CD Pipeline:** GitHub Actions con due workflow separati per la Continuous Integration e Continuous Deployment di Backend e Frontend.

---

## 🗄️ Passo 1: Creare il Database (PostgreSQL)
1. Cerca **Azure Database for PostgreSQL servers**.
2. Clicca su **+ Crea** -> **Flexible server**.
3. **Resource group:** `SocialExposure-RG`.
4. **Server name:** `social-exposure-db`.
5. **Region:** `Italy North` o `West Europe`.
6. **Workload type:** `Development` (Sviluppo).
7. **Compute + storage:** `Burstable` -> `B1ms`.
8. **Networking:** Spunta "Consenti l'accesso pubblico a questo server da qualsiasi servizio di Azure" e aggiungi il tuo IP corrente.
9. Rivedi e Crea. *(Salva la Connection String).*

---

## 📦 Passo 2: Creare il Registro Contenitori (Docker Registry)
1. Cerca **Registri contenitori** (Container registries) e clicca **+ Crea**.
2. **Nome registro:** es. `socialexposureregistry`.
3. **SKU:** `Basic`.
4. Crea la risorsa, poi vai in **Chiavi di accesso** (Access keys).
5. **Abilita "Utente amministratore"** e copia la **Password 1**. (Servirà per GitHub Actions).

---

## ⚙️ Passo 3: Creare il Backend (Azure App Service)
1. Cerca **App Services** -> **+ Crea -> Web App**.
2. **Publish:** `Docker Container` su OS `Linux`.
3. **Pricing Plan:** `F1 (Free)`.
4. Crea la risorsa. Poi dal menu a sinistra, vai in **Centro distribuzione** (Deployment Center).
5. **Origine immagine:** `Registro Azure Container`. Scegli il tuo registro e imposta l'immagine su `social-exposure-backend` con tag `latest`.
6. Salva e applica.
7. Vai in **Variabili d'ambiente** (Environment variables) e aggiungi:
   - `DATABASE_URL`: La connection string di PostgreSQL.
   - `GEMINI_API_KEY`: La tua chiave di Google Gemini.

---

## 🌐 Passo 4: Pubblicare il Frontend (Storage Account)
Per bypassare le restrizioni della policy universitaria sulle Static Web Apps globali, usiamo lo Storage Account.
1. Cerca **Account di archiviazione** e clicca **+ Crea**.
2. **Nome account:** es. `socialfrontend123` (solo lettere minuscole e numeri).
3. **Ridondanza:** `LRS` (Archiviazione con ridondanza locale).
4. Crea la risorsa. Nel menù a sinistra cerca **Gestione dei dati -> Sito Web statico**.
5. Clicca su **Abilitato**, scrivi `index.html` sia come "Documento di indice" che come "Documento di errore" (vitale per React).
6. Salva e copia l'**Endpoint primario** (questo sarà l'URL pubblico del tuo sito web).
7. Nel menù a sinistra vai su **Sicurezza e rete -> Chiavi di accesso** e copia la **Stringa di connessione** (Connection string).

---

## 🚀 Passo 5: Automazione CI/CD con GitHub Actions
Tutto il processo di caricamento (build e deploy) è completamente automatizzato. Non dovrai mai spostare file a mano, né collegarti via FTP.

### 5.1 Configurare i Segreti su GitHub
Vai sul repository GitHub in **Settings -> Secrets and variables -> Actions** e aggiungi questi tre "New repository secret":
1. `REGISTRY_USERNAME`: Il nome del tuo registro Docker (es. `socialexposureregistry`).
2. `REGISTRY_PASSWORD`: La password del registro (copiata al Passo 2).
3. `AZURE_STORAGE_CONNECTION_STRING`: La stringa di connessione dello Storage Account (copiata al Passo 4).

### 5.2 Come funziona l'automazione
Nel codice del progetto ci sono due file YAML che "ascoltano" i tuoi salvataggi:
- `.github/workflows/azure-deploy.yml`: Ogni volta che fai un `git push`, questo motore ricostruisce l'immagine Docker del backend in ambiente Linux, la invia ad Azure Container Registry e Azure aggiorna automaticamente l'App Service (azzerando il downtime).
- `.github/workflows/frontend-deploy.yml`: Questo motore controlla se hai fatto modifiche alla cartella `/frontend`. Se sì, avvia Node.js, compila il sito React (`npm run build`) e lo inietta automaticamente nel tuo Storage Account Azure nella cartella speciale `$web`.

*Basta un singolo `git push` e l'intera infrastruttura Cloud si aggiornerà da sola in pochi minuti.*
