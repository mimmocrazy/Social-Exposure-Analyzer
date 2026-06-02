# Guida Completa e Dettagliata al Deploy su Microsoft Azure (Free Tier)

Questa guida è pensata per accompagnarti passo-passo nella pubblicazione del tuo progetto **Social Exposure Analyzer** su Microsoft Azure, usando l'interfaccia aggiornata del portale. 

Tutto il processo sfrutta il **piano gratuito per studenti (Azure for Students)** o i tier gratuiti standard.

---

## 🗄️ Passo 1: Creare il Database (PostgreSQL)

1. Accedi al portale Azure e cerca **"Azure Database for PostgreSQL servers"**.
2. Clicca su **+ Crea** e scegli la scheda **Flexible server**.
3. Compila la sezione *Basics*:
   - **Resource group:** Crea nuovo (es. `SocialExposure-RG`).
   - **Server name:** Scegli un nome (es. `social-exposure-db`).
   - **Region:** `Italy North` o `West Europe`.
   - **Workload type:** Seleziona **Development** (Sviluppo).
   - **Compute + storage:** Clicca su *Configure server*, scegli la scheda **Burstable** e l'opzione **B1ms**.
   - **Administrator account:** Scegli un *Admin username* e una *Password*. **Segnateli!**
4. Clicca sul tab **Networking** in alto:
   - Spunta **"Consenti l'accesso pubblico a questo server da qualsiasi servizio di Azure in Azure"** (vitale).
   - Clicca sulla scritta blu **"+ Aggiungere l'indirizzo IP client corrente"** per poter usare il DB da casa.
   - *Non* spuntare la disponibilità elevata e lascia l'autenticazione su "Solo PostgreSQL".
5. Clicca su **Rivedi e crea** e poi su **Crea**. 

*(La tua Connection String finale sarà simile a: `postgresql://<USERNAME>:<PASSWORD>@social-exposure-db.postgres.database.azure.com:5432/postgres?sslmode=require`)*

---

## 📦 Passo 2: Creare il Registro Contenitori (Il "Disco" per Docker)

Poiché il nostro codice richiede l'installazione di pacchetti di sistema (come Tesseract-OCR), Azure ha bisogno di un'immagine Docker pre-compilata. Creeremo un registro privato per ospitarla.

1. Cerca **Registri contenitori** (Container registries) nella barra in alto.
2. Clicca su **+ Crea**.
3. Scegli il tuo Gruppo di Risorse (`SocialExposure-RG`).
4. **Nome registro:** Inventa un nome tutto minuscolo (es. `socialexposureregistry`).
5. **Località:** La stessa di prima (`Italy North`).
6. **SKU:** Seleziona **Basic** (Fondamentale). Costa pochi spiccioli scalati dai 100$ gratuiti.
7. Clicca su **Rivedi e crea** e **Crea**.
8. Quando ha finito, vai alla risorsa. Nel menu a sinistra cerca **Chiavi di accesso** (Access keys).
9. Spunta la voce **Utente amministratore** (Admin user). Azure genererà due password. **Copia la password 1 e tienila da parte**, ci servirà a breve su GitHub!

---

## ⚙️ Passo 3: Creare il Backend (App Service)

1. Cerca **App Services** in alto e clicca su **+ Crea -> Web App**.
2. Compila la scheda *Basics*:
   - **Resource Group:** Il solito (`SocialExposure-RG`).
   - **Name:** Scegli un nome (es. `social-exposure-backend`).
   - **Publish:** Scegli **Docker Container**.
   - **Operating System:** **Linux**.
   - **Pricing Plan:** Vai in *Explore pricing plans*, scheda *Free/Shared*, scegli **F1 (Free)** e selezionalo.
3. Clicca sulla scheda **Contenitore** in alto:
   - Sotto *Origine immagine*, seleziona **Avvio rapido** (Quickstart).
   - In *Opzioni di avvio rapido*, lascia **NGINX**.
4. Clicca su **Rivedi e crea** e poi **Crea**. Attendi la fine e clicca su **Vai alla risorsa**.

### 3.1 Collegare il Backend al Registro Contenitori
Ora diciamo all'App Service di abbandonare NGINX e prepararsi a ricevere la vera app dal Registro creato al Passo 2:
1. Dal menu a sinistra dell'App Service, clicca su **Centro distribuzione** (Deployment Center).
2. Clicca sulla scritta blu **`main`** nella tabella in basso (sotto *Nome*).
3. Nel pannello laterale, alla voce **Origine immagine**, scegli **Registro Azure Container**.
4. Seleziona il tuo registro (es. `socialexposureregistry`).
5. **Autenticazione:** Scegli **Identità gestita** e seleziona **Assegnata dal sistema**.
6. **Immagine:** Scrivi a mano `social-backend`
7. **Tag dell'immagine:** Scrivi a mano `latest`
8. Clicca su **Applica**.

### 3.2 Inserire le Chiavi (Variabili d'ambiente)
1. Nel menu laterale a sinistra dell'App Service, scorri giù fino a **Variabili d'ambiente** (Environment variables).
2. Clicca su **+ Aggiungi**.
   - Nome: `DATABASE_URL` | Valore: *la connection string di PostgreSQL creata al passo 1*.
   - Nome: `GEMINI_API_KEY` | Valore: *la tua chiave di Google Gemini*.
3. Clicca **Applica** e poi **Conferma**.

---

## 🤖 Passo 4: GitHub Actions (Automazione CI/CD)

Il file di automazione per GitHub (`.github/workflows/azure-deploy.yml`) è **già presente nel codice**. Tu devi solo inserire la password del Registro su GitHub per autorizzarlo.

1. Vai sul tuo repository su GitHub.
2. Clicca su **Settings** -> **Secrets and variables** -> **Actions**.
3. Clicca su **New repository secret**.
   - Nome: `REGISTRY_USERNAME`
   - Secret: *Il nome esatto del tuo registro (es. `socialexposureregistry`)*
4. Clicca di nuovo su **New repository secret**.
   - Nome: `REGISTRY_PASSWORD`
   - Secret: *La password copiata al Passo 2, punto 9*.
5. Fatto! Al prossimo push su GitHub, la tab *Actions* si illuminerà e il codice verrà inviato automaticamente ad Azure.

---

## 🎨 Passo 5: Pubblicare il Frontend (Static Web Apps)

1. Cerca **Static Web Apps** su Azure e clicca **+ Crea**.
2. **Resource Group:** `SocialExposure-RG`.
3. **Name:** es. `social-frontend`.
4. **Plan type:** **Free** (Gratuito per sempre).
5. **Source:** **GitHub**. Collega il tuo account e scegli repo e branch `main`.
6. **Build Presets:** Scegli **React**.
   - **App location:** `/frontend`
   - **Output location:** `dist`
7. Clicca su **Rivedi e crea** e **Crea**.
8. Una volta creato, vai su **Environment variables** (nel menu a sinistra della Static Web App).
   - Nome: `VITE_API_URL`
   - Valore: L'indirizzo del tuo backend con `/api/v1` alla fine (es. `https://social-exposure-backend.azurewebsites.net/api/v1`).
   - Applica e salva.

**Fine! Il sito è interamente nel cloud.**
