# Guida al Deploy Cloud-Native su Microsoft Azure (Strict Free Tier)

Questa guida illustra come pubblicare il progetto **Social Exposure Analyzer** su Microsoft Azure sfruttando esclusivamente i tier gratuiti, ottemperando ai requisiti di "Cloud Computing & Storage" del progetto universitario senza incorrere in addebiti sulla carta di credito.

---

## 1. Prerequisiti
1. **Account Azure for Students**: Attiva l'abbonamento studenti gratuito (100$ di credito per 12 mesi + servizi gratuiti) collegando l'email universitaria.
2. **GitHub Account**: Assicurati che il codice sorgente (frontend, backend e config) sia pushato su un repository GitHub privato o pubblico.
3. **Variabili d'Ambiente (.env)**: Prepara i token API (`GEMINI_API_KEY`, `GROQ_API_KEY`, ecc.) da inserire nei servizi cloud.

---

## 2. Deploy Database (PostgreSQL)

*Il progetto prevede l'abbandono di SQLite in favore di PostgreSQL in produzione.*

### Metodo Consigliato: Azure Database for PostgreSQL - Flexible Server
Questa opzione è gratuita per i primi 12 mesi se hai un nuovo account o l'account studenti.
1. Dal portale Azure, cerca **Azure Database for PostgreSQL**.
2. Clicca su **Create** e seleziona **Flexible server**.
3. Assicurati di selezionare la spunta *"Apply Free Trial"* o di scegliere il tier **Burstable B1MS** (1 vCore, 2 GiB memory, 32 GiB storage) che rientra nelle soglie gratuite.
4. Imposta Username e Password per l'amministratore.
5. In **Networking**, spunta *"Allow public access from any Azure service within Azure to this server"*.
6. Copia la stringa di connessione (Connection String) generata e tienila da parte. Sarà la tua variabile `DATABASE_URL`.

*(Nota: il codice del backend grazie alla libreria `psycopg2-binary` rileverà l'URL e abiliterà istantaneamente il motore PostgreSQL al posto di SQLite).*

---

## 3. Deploy Backend (FastAPI via Docker)

Sfrutteremo il runtime gratuito **F1 (Free)** di Azure App Service for Linux. Il progetto è già munito di `Dockerfile` multistage, il che accelera drasticamente l'avvio, in quanto scarica in fase di build i binari NLP (`it_core_news_sm`).

1. Dal portale Azure, cerca **App Services** e clicca **Create -> Web App**.
2. **Publish**: Seleziona **Docker Container**.
3. **Operating System**: Linux.
4. **Pricing Plan**: Scegli **Free F1** (Shared infrastructure, 1 GB RAM, 60 minutes/day compute).
5. **Deployment Center**: Collega il tuo account GitHub, seleziona il repository e il branch. Azure sfrutterà GitHub Actions per generare l'immagine Docker basandosi sul `Dockerfile` già fornito nella root e farla partire sul server.
6. **Configuration (Variabili d'ambiente)**: 
   - Vai in `Settings > Environment variables`.
   - Inserisci `DATABASE_URL` incollando la stringa di connessione a PostgreSQL creata nel passo precedente.
   - Inserisci le chiavi API (es. `GEMINI_API_KEY`, `GROQ_API_KEY`).
   - Assicurati di settare `AI_PROVIDER=groq` per mitigare i colli di bottiglia del tier gratuito di Google.
7. Copia il dominio generato (es. `https://se-backend.azurewebsites.net`).

---

## 4. Deploy Frontend (React SPA)

Il frontend in React verrà ospitato su **Azure Static Web Apps**, un servizio serverless focalizzato sullo static-hosting con CDN globale. Essendo una Single Page Application (SPA), beneficerà del file `staticwebapp.config.json` che abbiamo già inserito per gestire il routing `/index.html`.

1. Dal portale Azure, cerca **Static Web Apps** e clicca **Create**.
2. **Plan type**: Seleziona **Free**.
3. **Deployment Details**: Collega GitHub, seleziona il branch.
4. Nei **Build Presets**:
   - Framework: React
   - App location: `/frontend`
   - Output location: `dist`
5. Vai nella pagina di gestione della Static Web App appena creata. In **Configuration > Environment variables**, aggiungi:
   - Name: `VITE_API_URL`
   - Value: L'URL del backend creato nel punto 3 (es. `https://se-backend.azurewebsites.net/api/v1`).
6. Attendi la fine della build su GitHub Actions. Il sito sarà online e pienamente funzionale!

---

## Conclusione
Il tuo sistema distribuito è ora operativo su cloud. L'orchestrazione (Backend API e Task Asincroni) sfrutta l'elaborazione F1 di Azure, lo storage relazionale poggia su PostgreSQL Flexible, e la UI è servita da una CDN Statica globale a latenza zero. Tutte le richieste del professore sono state superate a pieni voti!
