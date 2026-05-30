# Architettura del Sistema - Social Exposure Analyzer

## Panoramica
L'architettura è stata progettata seguendo il paradigma **Event-Driven / Asynchronous** per garantire scalabilità e resilienza, caratteristiche fondamentali per il deploy su piattaforme Cloud come Microsoft Azure App Service.

## Disaccoppiamento Ingestion / Processing
1. **API Ingestion**: Il router di FastAPI espone l'endpoint `/api/v1/analyze` (Rest API) in modalità "fire-and-forget" (HTTP 202 Accepted). Risponde in pochissimi millisecondi per massimizzare il throughput.
2. **Worker in Background**: L'analisi vera e propria (Discovery -> Scraping -> OCR -> NLP -> Risk Engine) è pesantemente I/O e CPU-bound. Utilizziamo i `BackgroundTasks` nativi di FastAPI per disaccoppiare l'esecuzione dal ciclo di vita della richiesta HTTP principale. Questo previene timeout (tipicamente 230 secondi su Azure App Service) per analisi di profili complessi.

## Sicurezza: Anti-DoS e Rate Limiting
Per proteggere il sistema da flood e payload malevoli:
- **Middleware 413 Payload Too Large**: Qualsiasi richiesta che dichiari un `Content-Length > 10.000 byte` viene respinta istantaneamente (Autonomous Optimization introdotta nella Fase 5).
- **Hard Limit NLP**: Truncating a 10.000 caratteri in ingresso a spaCy.

## Roadmap Scalabilità (Azure)
Attualmente il sistema poggia su uno stack single-node ideale per la fase sperimentale:
- **Database**: SQLite in locale.
- **Worker**: `BackgroundTasks` asincroni in-process.

**Evoluzione Cloud Native (Next Steps):**
1. **Migration a CosmosDB o Azure SQL**: Sostituzione di SQLite per gestire transazioni multi-nodo (Azure Web App Scale-Out).
2. **Azure Service Bus**: Sostituzione dei `BackgroundTasks` con una message queue distribuita per inoltrare i task a un pool di `Azure Functions` dedicate.
3. **Auto-Scaling Rules**: Le App Service plan saranno configurate per scalare orizzontalmente basandosi sull'utilizzo CPU (superando l'80%).
