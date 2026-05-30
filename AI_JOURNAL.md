# AI Development Journal

Tracciamento delle decisioni architetturali e dei macro-task per garantire trasparenza sull'uso dell'AI generativa (requisito di progetto).

---

### Data: 2026-05-30
- **Task Eseguito:** Inizializzazione struttura di progetto e documentazione architetturale.
- **File Modificati:** `.gitignore`, `ARCHITECTURE.md`, `AI_JOURNAL.md`
- **Sintesi Prompt:**
> Sei un Senior Software Architect e Lead Developer, integrato nell'IDE Antigravity. Il nostro obiettivo è sviluppare un'applicazione cloud-based per il Social Engineering Risk Assessment, destinata al deploy finale su Microsoft Azure App Service. Hai i permessi di lettura/scrittura diretti sul file system locale.
> 
> ### 1. Contesto e Obiettivo (Ottimizzazione per Valutazione)
> * **Azione preliminare obbligatoria:** Leggi il file `TRACCIA.pdf` nel workspace per assimilare requisiti e dominio.
> * **Progetto:** Il sistema analizzerà profili social, estrarrà PII tramite NLP/OCR, calcolerà un Risk Score e genererà un report descrittivo sui rischi di impersonificazione/phishing tramite LLM (Gemini Pro).
> * **Criteri di Valutazione Target:** Il progetto sarà valutato su: 1) Rispondenza ai requisiti; 2) Originalità; 3) Organizzazione del codice (leggibilità/modularità); 4) Completezza della relazione (trasparenza AI). Ottimizza ogni tua decisione architetturale per massimizzare questi 4 punti.
> 
> ### 2. Struttura del Codice e Compartimentazione
> La repository deve essere rigorosamente divisa in tre macro-ambienti isolati:
> * `/backend`: FastAPI, logica AI/NLP/OCR, database SQLite.
> * `/frontend`: UI reattiva (sviluppata successivamente).
> * `/tests`: Unit e integration tests (Pytest). Nessun modulo può considerarsi chiuso senza la relativa copertura di test.
> 
> ### 3. Tracciamento (AI_JOURNAL.md) e Sincronizzazione Git
> Devi gestire il file `AI_JOURNAL.md` in totale autonomia e allinearlo allo storico Git.
> * **Commit Threshold (Soglia di Rilevanza):** AGGIORNA il journal SOLO quando completi un macro-task, aggiungi una feature architetturale, o chiudi un modulo. IGNORA fix minori o typo. Il journal deve essere immacolato. Formato: Data, Task Eseguito, File Modificati, Sintesi Prompt, Spiegazione Tecnica.
> * **Integrazione Git (Conventional Commits):** Ogni volta che aggiorni il journal, devi ANCHE fornirmi nel tuo output i comandi Git esatti (`git add .`, `git commit -m "..."`, `git push`). Usa lo standard Conventional Commits. La history di Git deve essere lo specchio perfetto del journal.
> 
> ### 4. Documentazione di Progetto
> * Crea e mantieni aggiornato il file `ARCHITECTURE.md`. Conterrà la roadmap granulare in micro-task divisa chiaramente per compartimenti (Backend -> Test Backend -> AI/Core -> Test AI -> Frontend -> Deploy Azure), lo stack esatto e le specifiche API.
> 
> ### 5. Regole di Esecuzione e Stile di Comunicazione
> * **Problem Solving Proattivo:** Quando arriviamo a un bivio decisionale, NON farmi mai solo domande aperte. Proponimi sempre 2 o 3 opzioni, elencando Pro/Contro tecnici e suggerendomi esplicitamente la mossa più "astuta" per la demo.
> * **Role-Switching & Model Scaling:** Lavoreremo a compartimenti stagni (Architect -> Backend Dev -> QA Tester -> Frontend Dev). Ora sei il *System Architect*. Avendo quote limitate sui modelli avanzati e ampie sui modelli base (Flash), ricordami tu di abbassare il modello per task ripetitivi o di test, per poi chiedermi di rialzarlo sulle decisioni critiche.
> * **Qualità e Sicurezza:** Type hinting, docstrings (Google style). Zero gergo AI (vietato: "Certamente", "Immergiamoci"). Risposte dirette e codice blindato.
> 
> ### 6. Output Atteso (Fase 1 - Inizializzazione)
> NON scrivere codice Python in questa fase. Esegui queste operazioni nell'ordine esatto:
> 1.  **Genera un `.gitignore` blindato:** Configuralo per proteggere chiavi API, ambienti virtuali, cache Python e file di sistema.
> 2.  **Genera `ARCHITECTURE.md`:** Scrivi il documento di design e la roadmap a micro-task, evidenziando la divisione backend/frontend/tests.
> 3.  **Inizializza `AI_JOURNAL.md`:** Registra il primo log relativo al setup.
> 4.  **Primo Commit:** Forniscimi i comandi Git per fare la primissima commit (`chore: init project structure e documentation`).
> 5.  **Brainstorming Finale Proattivo:** Ponimi le prime questioni tecniche bloccanti per iniziare il Backend. Proponi opzioni strategiche e dimmi quale secondo te ha più senso. Attendi le mie istruzioni.
- **Spiegazione Tecnica:** Creata la baseline architetturale ottimizzata per il deploy su Azure App Service. Stabilito un `.gitignore` blindato per prevenire leak di secret. Redatto `ARCHITECTURE.md` con separazione netta dei moduli per massimizzare la modularità e la leggibilità del codice, facilitando la futura valutazione del progetto.

---

### Data: 2026-05-30
- **Task Eseguito:** Configurazione Database e modelli ORM (Fase 1).
- **File Modificati:** `/backend/models.py`, `/backend/database.py`, `AI_JOURNAL.md`
- **Sintesi Prompt:**
> Confermo l'Opzione B per le scelte architetturali: SQLModel e BackgroundTasks. Procediamo con il primo sviluppo.
> 
> Esegui il task "Configurazione Database e modelli ORM" (Fase 1).
> Crea il file `/backend/models.py` implementando il modello SQLModel `ProfileAnalysis` con questi esatti campi per gestire sia i dati che lo stato del background task:
> - `id`: UUID (Primary Key, default uuid4).
> - `target_url`: String (index=True).
> - `platform`: String (es. "instagram", "linkedin", nullable).
> - `status`: String (default "PENDING", Enum o vincolato a PENDING, COMPLETED, FAILED).
> - `scan_date`: DateTime (default timezone UTC).
> - `raw_data_dump`: JSON (nullable, popolato a scraping finito).
> - `pii_extracted`: JSON (nullable, popolato a NLP concluso).
> - `has_images_analyzed`: Boolean (default False).
> - `risk_score`: Integer (0-100, nullable).
> - `risk_level`: String ("Basso", "Medio", "Alto", nullable).
> - `llm_report`: Text/String (nullable).
> - `error_message`: Text/String (nullable, popolato se status va in FAILED).
> 
> Crea il file `/backend/database.py` impostando l'engine per SQLite locale (es. `sqlite:///./sera_database.db`) e la funzione generatore `get_session`.
> 
> Al termine:
> 1. Registra questa interazione in `AI_JOURNAL.md`, copiando il testo ESATTO di questo prompt come pattuito.
> 2. Forniscimi i comandi Git per il commit.
- **Spiegazione Tecnica:** Creato il modello dati `ProfileAnalysis` sfruttando SQLModel. L'uso di SQLModel permette di avere sia i modelli validati da Pydantic che la persistenza SQLAlchemy in un'unica classe, riducendo drasticamente il codice e migliorando la leggibilità. Creato il file `database.py` con un SQLite engine per lo sviluppo e l'implementazione del pattern di Dependency Injection per le sessioni del database (`get_session`).
