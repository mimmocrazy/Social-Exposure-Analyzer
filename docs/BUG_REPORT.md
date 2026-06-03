# Bug Report and Fixes

Questo documento traccia i bug e le incoerenze scoperte durante l'audit profondo del progetto e documenta le relative correzioni.

## Anomalie Rilevate e Corrette

| ID | Data Scoperta | Componente | Descrizione Bug | Impatto | Soluzione Applicata |
|---|---|---|---|---|---|
| B01 | 2026-06-03 | `analyze.py` | Fallback errato: L'utilizzo di sequenze `if` separate per i provider (GitHub, Groq, Gemini) faceva scattare il fallback di Gemini anche quando l'estrazione andava a buon fine tramite gli altri provider. | Alto | Correzione logica del flusso di controllo passando a `if ... elif ... elif`. |
| B02 | 2026-06-03 | `risk_engine.py` | Loop infinito nella rotazione chiavi: In caso di errore 503, la funzione `rotate_gemini_key` entrava in ricorsione all'infinito causando un crash stack-overflow. | Critico | Implementato un tetto massimo di fallback (`len(GEMINI_KEYS)`) ed exit-condition sicure. |
| B03 | 2026-06-03 | `risk_engine.py` | Decommissioning di Llama3 su Groq: Il modello hardcodato `llama3-70b-8192` è stato deprecato dal provider, causando un errore 404/400 fisso. | Alto | Aggiornato il payload al modello `llama-3.3-70b-versatile` attualmente supportato e stabile. |

*Nota: Questo documento è mantenuto attivamente dall'agente durante le fasi di review e refactoring del codice per tracciare il technical debt risolto.*
