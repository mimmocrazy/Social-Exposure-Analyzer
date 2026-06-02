# Guida Completa e Dettagliata al Deploy su Microsoft Azure (Free Tier)

Questa guida è pensata per accompagnarti passo-passo nella pubblicazione del tuo progetto **Social Exposure Analyzer** su Microsoft Azure. 
Se è la prima volta che usi il cloud, non preoccuparti: ogni passaggio è spiegato nel dettaglio, indicando esattamente dove cliccare e perché stiamo facendo una determinata operazione.

Tutto il processo è pensato per sfruttare il **piano gratuito per studenti (Azure for Students)**, garantendo che tu non spenda nemmeno un centesimo.

---

## 📚 Introduzione: Cosa stiamo per costruire?
Il nostro progetto è diviso in tre "pezzi" fondamentali (architettura a tre livelli). Su Azure, creeremo un servizio specifico per ciascun pezzo:

1. **Il Database (PostgreSQL):** È l'archivio dove verranno salvate le analisi passate in modo che tu possa rivederle dalla cronologia. Su Azure useremo un servizio chiamato *Azure Database for PostgreSQL*.
2. **Il Backend (Python/FastAPI):** È il "motore" dell'applicazione. È il programma che contatta Instagram, scarica le foto, usa l'intelligenza artificiale (Gemini/Groq) per fare i calcoli e valuta il rischio. Lo ospiteremo su un server cloud chiamato *Azure App Service*.
3. **Il Frontend (React):** È l'interfaccia grafica bella, quella con il terminale hacker e il carosello delle immagini. È il sito web vero e proprio con cui tu e il professore interagirete. Lo caricheremo su *Azure Static Web Apps*.

---

## 🛠️ Passo 0: Prerequisiti Fondamentali

Prima di toccare Azure, devi avere queste due cose pronte:
1. **Un account GitHub con il tuo codice:** Tutto il codice del progetto (la cartella `frontend`, `backend`, i file `.gitignore`, `Dockerfile`, ecc.) deve essere caricato ("pushato") su un repository sul tuo account GitHub (può essere privato o pubblico). Azure andrà a pescare il codice direttamente da lì in modo automatico.
2. **Account Azure for Students:** Vai su *azure.microsoft.com/free/students* e accedi con la tua email universitaria per attivare i 100$ di credito gratuiti e i servizi gratuiti per 12 mesi senza dover inserire la carta di credito.

---

## 🗄️ Passo 1: Creare il Database (PostgreSQL)

*Perché lo facciamo?* In locale sul tuo computer il progetto usava SQLite (un semplice file `.db`), ma nel cloud professionale si usano database dedicati e robusti. Il nostro codice è intelligente: capirà automaticamente che siamo nel cloud e passerà a PostgreSQL da solo.

**Come fare sul portale Azure:**
1. Accedi al portale Azure (`portal.azure.com`).
2. Nella barra di ricerca in alto, scrivi **"Azure Database for PostgreSQL servers"** e cliccaci sopra.
3. Clicca sul bottone blu **+ Create** (Crea) in alto a sinistra.
4. Ti verrà chiesto che tipo di server vuoi. Scegli la scheda **Flexible server** cliccando sul bottone *Create* in basso.
5. Compila la sezione *Basics* (Informazioni di base):
   - **Subscription:** Lascia "Azure for Students".
   - **Resource group:** Clicca sul link "Create new" sotto la tendina e chiamalo ad esempio `SocialExposure-RG` (RG sta per Resource Group, è come una cartella logica che conterrà tutto il tuo progetto per tenerlo ordinato).
   - **Server name:** Scegli un nome unico in tutto il mondo, tutto minuscolo (es. `social-db-tuonome`).
   - **Region:** Scegli una regione geografica vicina a te (es. `Italy North`, `West Europe` o `North Europe`).
   - **Workload type:** Seleziona **Development** (Sviluppo).
   - **Compute + storage:** Questo è **vitale per non pagare**! Clicca su *Configure server* e assicurati di selezionare il tab **Burstable** e dal menu a tendina l'opzione **B1ms** (1 vCore, 2 GiB RAM, 32 GiB storage). Rientra nei limiti gratuiti per gli studenti per i primi 12 mesi. Clicca su *Save*.
   - **Administrator account:** Scegli un *Admin username* (es. `admin_db`) e una *Password* sicura a tua scelta. **Segnateli su un blocco note, ti serviranno a breve!**
6. Clicca sul tab **Networking** in alto:
   - Cerca la spunta **"Allow public access from any Azure service within Azure to this server"** e attivala. Questo è fondamentale, altrimenti il tuo Backend (che creeremo tra poco) verrà bloccato dal firewall e non potrà salvare i dati.
7. Clicca sul pulsante azzurro in basso **Review + create** e poi su **Create**.
8. Azure impiegherà qualche minuto (di solito 3-5) per creare il server. Quando ha finito, vedrai un bottone blu con scritto **Go to resource**. Cliccaci.

**Componi la tua "Chiave Magica" (Connection String):**
Ora devi creare l'URL segreto che il backend userà per connettersi. Prendi il blocco note dove hai salvato username e password e scrivi questo formato, sostituendo i tuoi dati reali:
`postgresql://<USERNAME_ADMIN>:<PASSWORD>@<SERVER_NAME>.postgres.database.azure.com:5432/postgres?sslmode=require`

*Esempio concreto: se l'user è `admin_db`, la password è `Segreta123!` e il nome del server era `social-db-mario`, la stringa esatta sarà:*
`postgresql://admin_db:Segreta123!@social-db-mario.postgres.database.azure.com:5432/postgres?sslmode=require`

Tieni questa lunghissima stringa da parte, la useremo nel prossimo step.

---

## ⚙️ Passo 2: Pubblicare il Backend (Il Motore Python)

*Perché lo facciamo?* Dobbiamo mettere il codice Python del backend su un computer nel cloud in modo che sia sempre acceso e pronto a ricevere richieste di analisi. Useremo un servizio gratuito chiamato **App Service** e sfrutteremo **Docker** (il file `Dockerfile` che hai nel progetto spiega ad Azure come installare Python e le librerie in modo completamente automatico).

**Come fare sul portale Azure:**
1. Nella barra di ricerca in alto, cerca **App Services** e cliccaci.
2. Clicca su **+ Create** e scegli **Web App**.
3. Compila la scheda *Basics*:
   - **Subscription:** Azure for Students.
   - **Resource Group:** Seleziona quello creato prima dal menu a tendina (`SocialExposure-RG`).
   - **Name:** Scegli un nome unico (es. `social-backend-tuonome`). Questo nome diventerà il link del tuo backend (es. `social-backend-tuonome.azurewebsites.net`).
   - **Publish:** Scegli **Docker Container** (così Azure leggerà il nostro `Dockerfile` senza che dobbiamo configurare Python a mano).
   - **Operating System:** Seleziona **Linux**.
   - **Region:** Usa la stessa scelta per il database (es. `Italy North`).
   - **Pricing Plan:** Questa è la parte per non pagare! Clicca su *Explore pricing plans*, vai sulla scheda in alto *Free/Shared* e clicca sulla mattonella blu **F1 (Free)**. Infine clicca sul bottone blu in basso *Select*.
4. Clicca sulla scheda **Contenitore** (o Docker) in alto:
   - Sotto *Origine immagine*, Azure ti chiederà da dove prendere il codice. Visto che GitHub non lo ha ancora "costruito", usa un rimpiazzo temporaneo: scegli **Avvio rapido** (Quickstart).
   - In *Opzioni di avvio rapido*, lascia pure **NGINX**. (È solo un'immagine segnaposto che sostituiremo tra poco).
5. Clicca in basso su **Rivedi e crea** e poi su **Crea**.
6. Quando ha finito (1-2 minuti), clicca su **Vai alla risorsa** (Go to resource). Il tuo server backend è stato creato, ma per ora mostra solo una pagina di base NGINX.
7. **Collegare GitHub (La Magia):**
   Ora diciamo ad Azure di andare su GitHub, prendere il nostro `Dockerfile`, costruire il codice Python e sostituire NGINX.
   - Nel menù a sinistra della tua Web App appena creata, cerca la voce **Centro di distribuzione** (Deployment Center) e cliccaci.
   - Sotto *Origine* (Source), seleziona **GitHub**.
   - Clicca su *Autorizza* se ti chiede di collegare l'account.
   - Compila le tendine che appaiono: `Organizzazione` (il tuo utente), `Repository` (il nome del progetto) e `Ramo/Branch` (`main`).
   - Sotto *Impostazioni del registro contenitori*, dovrebbe auto-configurarsi su "Container Registry".
   - Clicca in alto su **Salva**. In questo esatto momento, Azure sta inviando un file a GitHub per far partire la costruzione (build) del tuo codice. Ci vorranno 5-10 minuti!
8. **Inserire le password segrete (Variabili d'ambiente):**
   Mentre GitHub compila, dobbiamo dare al backend le chiavi per funzionare.
   - Nel menu laterale a sinistra, scorri giù fino a **Variabili d'ambiente** (Environment variables) o *Configurazione*.
   - Clicca su **+ Aggiungi** per aggiungere una variabile.
   - Aggiungi il database: 
     - Nome: `DATABASE_URL`
     - Valore: *incolla la lunga stringa di connessione a PostgreSQL che hai creato alla fine del Passo 1*.
   - Aggiungi Gemini:
     - Nome: `GEMINI_API_KEY`
     - Valore: *incolla la tua chiave API di Google Gemini*.
   - Una volta aggiunte tutte, clicca sul bottone **Applica** e poi **Conferma**.
9. Salva il link del tuo backend. Lo trovi nella pagina "Panoramica" (Overview) sotto la voce "Dominio predefinito" (sarà simile a `https://social-backend-tuonome.azurewebsites.net`). Tientelo segnato.

---

## 🎨 Passo 3: Pubblicare il Frontend (L'Interfaccia React)

*Perché lo facciamo?* Il frontend è solo un insieme di file visivi e script (HTML, CSS, React). Non ha bisogno di un computer "pesante" come il backend, ma di un servizio rapido per consegnare le pagine web. Azure ha un servizio perfetto e 100% gratuito per questo: **Static Web Apps**.

**Come fare sul portale Azure:**
1. Nella barra di ricerca in alto, cerca **Static Web Apps** e cliccaci.
2. Clicca su **+ Create**.
3. Compila la scheda *Basics*:
   - **Resource Group:** Sempre il solito (`SocialExposure-RG`).
   - **Name:** Scegli un nome (es. `social-frontend-tuonome`).
   - **Plan type:** Assicurati che sia su **Free** (è gratuito a vita per progetti personali).
   - **Region:** Una qualsiasi in Europa (es. `West Europe`).
   - **Source:** Seleziona **GitHub**.
   - Scegli dal menu a tendina il tuo utente GitHub, il tuo repository e il branch `main`.
4. **Build Details (Dettagli di compilazione):** 
   Qui stiamo dicendo ad Azure in quale cartella andare a cercare i file dell'interfaccia grafica.
   - **Build Presets:** Scegli **React**.
   - **App location:** Scrivi `/frontend` (con lo slash davanti).
   - **Api location:** Lascialo vuoto (cancellalo se c'è scritto qualcosa).
   - **Output location:** Scrivi `dist` (è il nome della cartella dove React crea il pacchetto finale ottimizzato).
5. Clicca su **Review + create** e poi su **Create**.
6. Quando ha finito, clicca su **Go to resource**.
7. **Collegare il Frontend al Backend:** 
   Adesso il sito web è online, ma non sa a chi inviare le analisi. Dobbiamo dirgli qual è l'indirizzo del Backend che abbiamo creato nel Passo 2.
   - Nel menu a sinistra della tua Static Web App, clicca su **Environment variables**.
   - Clicca su **+ Add**.
   - Name: `VITE_API_URL`
   - Value: L'indirizzo del tuo backend con l'aggiunta di `/api/v1` alla fine. (Esempio: se il backend era `https://social-backend-tuonome.azurewebsites.net`, scrivi `https://social-backend-tuonome.azurewebsites.net/api/v1`).
   - Clicca su **Apply** nella finestrella laterale e poi su **Save** in alto, confermando.
8. Fatto! Clicca su **Overview** nel menu di sinistra. Troverai un link chiamato "URL" (sarà un nome generato casualmente, tipo `https://calm-ocean-1234.azurestaticapps.net`). Cliccandoci, si aprirà il tuo meraviglioso sito web funzionante!

*(Nota: Quando arrivi allo step 8, potresti trovare una pagina bianca o d'errore di GitHub. È normale! Significa che dietro le quinte GitHub Actions sta ancora installando e caricando il codice. Aspetta 3 o 4 minuti, ricarica la pagina e apparirà la dashboard hacker).*

---

## 💡 Consigli d'Oro per l'Esame (Come gestire i costi nel mese di attesa)

Visto che manca un mese e mezzo all'esame, devi sapere un paio di cose su come gestire questi servizi appena creati per evitare di consumare crediti a vuoto:

1. **Il Frontend è immortale e gratis:** La Static Web App che abbiamo creato al Passo 3 è gratuita per sempre. Lasciala online, non toccherà i tuoi crediti e non si spegnerà mai.
2. **Il Backend "si addormenta":** Poiché stiamo usando un backend gratuito (Piano F1), Azure lo "mette a dormire" se nessuno lo usa per 20 minuti per non sprecare risorse. Se apri il sito dopo due giorni che non lo usi e premi "Analizza", il server ci metterà circa 20-30 secondi per riaccendersi (si chiama *Cold Start*). Non ti preoccupare, è normale. **Il giorno dell'esame**, fai un'analisi finta 5 minuti prima di condividere lo schermo col professore, così il server sarà già sveglio e l'analisi partirà istantaneamente!
3. **Il Database e il limite delle ore:** Un mese ha massimo 744 ore in totale. Il database flessibile gratuito per studenti ti regala **750 ore al mese**. Questo significa che un (solo 1!) database può stare acceso 24 ore al giorno ininterrottamente gratis. Quindi puoi tecnicamente lasciarlo acceso senza pensieri.
4. **Spegnere il Database (Livello Paranoia):** Se vuoi essere *matematicamente certo* di non sprecare nemmeno un'ora del tuo database mentre non ci lavori, vai nella pagina Overview del tuo Database PostgreSQL sul portale Azure e clicca sul pulsante **Stop**. Il server si spegnerà e smetterà di contare le ore di utilizzo. Il sito smetterà di funzionare temporaneamente. Quando vuoi usarlo per fare dei test, o due giorni prima dell'esame, torna lì e clicca su **Start**. *(Attenzione: Azure riaccende automaticamente i server fermi dopo 7 giorni, quindi ogni tanto dacci un'occhiata).*

Con questa guida, avrai un'architettura professionale, complessa e cloud-native, a costo assolutamente ZERO. In bocca al lupo per l'esame!
