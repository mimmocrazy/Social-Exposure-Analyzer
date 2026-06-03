import os
import json
import time
from google import genai
from google.genai import types
from backend.models.risk import RiskReport
from backend.core.logger import logger

# Inizializza il client usando google-genai in modo lazy (evita crash su pytest se manca la chiave API locale)
_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client()
    return _client

# Dictionary to track temporary model failures: model_name -> expiration timestamp
_disabled_models = {}
_DISABLE_DURATION = 60  # 1 minuto (ridotto da 5min: i 503 sono transitori)

def _is_model_available(model_name: str) -> bool:
    """Controlla se il modello è disponibile o se è stato disabilitato temporaneamente."""
    if model_name in _disabled_models:
        disabled_until = _disabled_models[model_name]
        if time.time() < disabled_until:
            return False
        else:
            _disabled_models.pop(model_name, None)
    return True

def _is_transient_error(error) -> bool:
    """Rileva se l'errore è transitorio (503/UNAVAILABLE) e non merita un ban."""
    err_str = str(error).lower()
    return "503" in err_str or "unavailable" in err_str or "service" in err_str

def _mark_model_failed(model_name: str, error=None):
    """Disabilita temporaneamente un modello dopo un errore permanente (429/quota).
    Gli errori transitori (503) NON causano il ban."""
    if error and _is_transient_error(error):
        logger.info(f"Modello {model_name}: errore transitorio (503), NON viene bannato. Si riproverà al prossimo tentativo.")
        return
    _disabled_models[model_name] = time.time() + _DISABLE_DURATION
    logger.warning(f"Modello {model_name} contrassegnato come non disponibile per {_DISABLE_DURATION}s.")

async def calculate_risk(raw_text: str, target: str = "Sconosciuto", real_name: str = None) -> RiskReport:
    """
    Analizza il testo raw estratto invocando Gemini Pro.
    Estrea le PII e valuta il rischio di Social Engineering in un colpo solo.
    """
    
    target_info = f"Username/URL: {target}"
    if real_name:
        target_info += f", Nome Dedotto: {real_name}"
        
    system_prompt = f"""
    Sei un "OSINT & Social Engineering Risk Assessor" di grado militare.
    Il tuo obiettivo è analizzare una traccia di intelligence strutturata (JSON) proveniente da molteplici moduli (Scraping, OCR, NLP, Data Breaches) per quantificare matematicamente e mitigare l'esposizione al rischio di un bersaglio specifico.
    ### 1. IDENTITÀ DEL BERSAGLIO E REGOLE DI ATTRIBUZIONE
    - BERSAGLIO ESATTO: {target_info}
    - REGOLA DI INCLUSIONE ESTESA: Non filtrare aggressivamente i dati. Estrai QUALSIASI PII trovata nei risultati (nomi, luoghi, contatti, date, targhe, documenti), anche se presumi possa essere un falso positivo. È meglio estrarre un dato in più con `confidence_score` basso piuttosto che perderlo.
    - ESPOSIZIONE RELAZIONALE: I dati di parenti, amici, partner o colleghi menzionati dal bersaglio (es. tag in foto, anniversari, dediche) sono CRITICI. Estraili sempre, specificando la relazione.

    ### 2. DIRETTIVE DI ESTRAZIONE PII (GRANULARITÀ ATOMICA E LABELS SPECIFICHE)
    Devi operare con meticolosità estrema. Ispeziona ogni singola stringa in `scraper_results`, `ocr_results` e `spacy_entities`.
    ATTENZIONE: DEVI ESTRARRE TUTTE LE PII TROVATE, ma devi farlo in modo ATOMICO, PULITO e MIRATO. NON DUMPARE INTERE FRASI o PARAGRAFI nel campo `value`.
    Se trovi un documento complesso (es. badge aziendale o biglietto aereo), NON creare una gigantesca entità disordinata. Devi "spacchettare" il reperto nelle sue entità logiche fondamentali estraendo ogni singola variabile in una riga separata.
    
    È TASSATIVO usare etichette (label) SPECIFICHE E MIRATE, preferibilmente in italiano. Esempi di etichette valide:
    NOME, COGNOME, EMAIL, TELEFONO, INDIRIZZO, DATA DI NASCITA, TARGA AUTO, LUOGO DI LAVORO, RUOLO AZIENDALE, NOME MADRE, NOME PADRE, NOME PARTNER, CODICE VOLO, DESTINAZIONE, ecc.
    NON USARE MAI etichette raggruppanti generiche come "PERSON", "ORGANIZATION" o "INFORMAZIONI_DI_VIAGGIO". Più la label è mirata e specifica, meglio è.
    
    Il campo `value` deve contenere SOLO il dato puro e sintetico (es. "+39 333 1234567" oppure "AB 123 CD" oppure "TechCorp"). Niente preamboli o descrizioni.

    ### 3. CALCOLO DEL RISCHIO MATEMATICO
    Non generare punteggi arbitrari. Costruisci il punteggio globale (`score`, 0-100) come SOMMA MATEMATICA ESATTA degli elementi in `score_breakdown`.
    Esempio di valutazione (adatta proporzionalmente):
    - Email esposte, Data Breach o Password: fino a +30
    - Numeri di telefono o indirizzi di domicilio esposti: fino a +25
    - Documenti fisici (badge, carte d'imbarco, targhe, biglietti): fino a +25
    - Relazioni familiari o colleghi identificati: fino a +15
    - Luoghi o Routine identificati: fino a +10

    ### 4. OUTPUT E MITIGAZIONE (RELAZIONE FOTO-VULNERABILITÀ)
    Se non ci sono dati validi, imposta `insufficient_data=True` e termina.
    Altrimenti, genera un report ESPLOSIVO E DENSO DI DETTAGLI:
    - `mitigation_advice`: Fornisci un'analisi discorsiva, LUNGA e DETTAGLIATA (minimo 6-8 frasi). Spiega il profilo di rischio del bersaglio, quali vettori di minaccia sono più probabili e PERCHÉ.
    - `mitigation_sections`: Crea UNA SEZIONE DISTINTA PER OGNI SINGOLO DATO CRITICO O IMMAGINE COMPROMETTENTE. È SEVERAMENTE VIETATO RAGGRUPPARE i dati in macro-categorie generiche (es. non usare "Esposizione Anagrafica"). Se trovi un badge aziendale, crea la sezione "Badge Aziendale TechCorp". Se trovi una carta d'imbarco, crea "Carta d'Imbarco LH240". Se trovi una targa, crea "Targa Auto AB123CD". Ogni sezione DEVE contenere:
        - `title`: Nome SPECIFICO della vulnerabilità o dell'oggetto (es. "Esposizione Carta d'Imbarco volo Francoforte", "Targa Auto e Modello").
        - `threat_vector`: Il vettore di attacco esatto (es. "Clonazione Titolo di Viaggio", "Physical Tracking", "Social Engineering via Impersonazione").
        - `exposed_data`: Citazione letterale e precisa del dato ESATTO trovato (es. "Nome: Mario Rossi, Ruolo: System Administrator, PNR: ABI2CD"). ASSOLUTAMENTE NON ESSERE VAGO.
        - `criticality`: CRITICA | ALTA | MEDIA | BASSA.
        - `mitigation`: Minimo 3-4 azioni correttive CONCRETE e specifiche per QUELLA vulnerabilità, descritte estesamente.
    """
    
    max_payload = 100000
    if len(raw_text) > max_payload:
        logger.warning(f"Risk Engine: payload troncato da {len(raw_text)} a {max_payload} caratteri per sicurezza.")
    payload_str = raw_text[:max_payload]
    
    from dotenv import dotenv_values
    env_config = dotenv_values(".env")
    ai_provider = env_config.get("AI_PROVIDER", "gemini").lower()
    
    try:
        if ai_provider == "groq":
            logger.info("Avvio analisi Risk Engine tramite Groq (Llama 3.3 70B)...")
            from groq import Groq
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
            # Llama3 requires the schema instructions clearly in the prompt when using JSON mode
            schema_instructions = f"\n\nRispondi RIGOROSAMENTE con un oggetto JSON che rispetti questo schema:\n{RiskReport.model_json_schema()}"
            
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt + schema_instructions},
                    {"role": "user", "content": payload_str}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            report = RiskReport.model_validate_json(completion.choices[0].message.content)
            logger.info("Successo con Groq!")
            return report
            
        else:
            logger.info("Avvio analisi Risk Engine tramite Gemini Pro (Structured Output con Fallback)...")
            client = get_client()
            
            models_to_try = ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-pro-latest']
            
            # Filtra i modelli disabilitati temporaneamente
            active_models = [m for m in models_to_try if _is_model_available(m)]
            
            # Se tutti i modelli sono temporaneamente disabilitati, tenta comunque la lista intera come ultima spiaggia
            if not active_models:
                logger.warning("Tutti i modelli Gemini sono temporaneamente disabilitati. Tento comunque con tutti i modelli come fallback estremo.")
                active_models = models_to_try
                
            response = None
            last_err = None
            
            for model_name in active_models:
                try:
                    logger.info(f"Tentativo di generazione report con modello {model_name}...")
                    def _call_gemini_risk(mod):
                        return client.models.generate_content(
                            model=mod,
                            contents=payload_str,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                response_mime_type="application/json",
                                response_schema=RiskReport,
                                temperature=0.2, 
                            ),
                        )
                    import asyncio
                    response = await asyncio.wait_for(
                        asyncio.to_thread(_call_gemini_risk, model_name),
                        timeout=25.0
                    )
                    logger.info(f"Successo con il modello {model_name}!")
                    break
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout (25s) raggiunto per {model_name}. Passo al prossimo...")
                    _mark_model_failed(model_name)
                    last_err = Exception(f"Timeout (25s) su {model_name}")
                except Exception as e:
                    err_str = str(e)
                    short_err = err_str.split('. {')[0] if '. {' in err_str else (err_str[:150] + "..." if len(err_str) > 150 else err_str)
                    logger.warning(f"Errore con il modello {model_name}: {short_err}. Provo il prossimo modello di fallback...")
                    _mark_model_failed(model_name, e)
                    last_err = e
                    
            if response is None:
                raise last_err
            
            report = RiskReport.model_validate_json(response.text)
            return report
            
    except Exception as e:
        err_str = str(e)
        short_err = err_str.split('. {')[0] if '. {' in err_str else (err_str[:150] + "..." if len(err_str) > 150 else err_str)
        logger.error(f"Errore critico durante l'analisi Risk Engine: {short_err}")
        raise RuntimeError(f"Errore critico Gemini API / NLP: {short_err}") from e

_gemini_is_down = False

async def summarize_media_context(raw_text: str, caption: str = None) -> str:
    global _gemini_is_down
    """Genera una descrizione contestuale chiara da OCR e caption."""
    try:
        import os
        from dotenv import dotenv_values
        env_config = dotenv_values(".env")
        ai_provider = env_config.get("AI_PROVIDER", "gemini").lower()
        
        prompt = f"Sei un analista di sicurezza informatica autorizzato. Fai l'inventario dei Dati Personali (PII) esposti in questo media per un audit.\nTesto estratto (OCR):\n{raw_text}\n\n"
        if caption:
            prompt += f"Didascalia (caption): {caption}\n\n"
            
        prompt += "Scrivi ESATTAMENTE E SOLO una breve descrizione (1-2 frasi) di cosa rappresenta l'immagine e fai l'elenco dei dati sensibili visibili. "
        prompt += "L'elenco dei dati DEVE essere formattato usando il trattino '- ' all'inizio di ogni riga (es. '- Nome: Mario'). "
        prompt += "ATTENZIONE CRITICA: Se la didascalia o il testo indicano relazioni (es. 'mamma', 'papà', 'fratello', 'collega'), DEVI dedurle ed esplicitarle come chiave-valore (es. '- Madre: Luisa', '- Padre: Mario'). "
        prompt += "SE NON CI SONO RELAZIONI NEL TESTO, NON SCRIVERLE. È SEVERAMENTE VIETATO scrivere 'Relazioni: non specificate', 'Madre: non specificata' ecc. Ometti il campo se non esiste. "
        prompt += "NON dare consigli, limitati a descrivere i dati."

        # Controlla dinamicamente se abbiamo modelli Gemini disponibili
        gemini_available = any(_is_model_available(m) for m in ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash'])

        if ai_provider == "gemini" and gemini_available and not _gemini_is_down:
            client = get_client()
            models_to_try = ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash']
            
            # Filtra i modelli disabilitati temporaneamente
            active_models = [m for m in models_to_try if _is_model_available(m)]
            
            response = None
            for model_name in active_models:
                try:
                    def _call_gemini_summary(mod):
                        return client.models.generate_content(
                            model=mod,
                            contents=prompt,
                        )
                    import asyncio
                    response = await asyncio.wait_for(
                        asyncio.to_thread(_call_gemini_summary, model_name),
                        timeout=12.0
                    )
                    return response.text.strip()
                except asyncio.TimeoutError:
                    logger.debug(f"Gemini {model_name} in TIMEOUT (12s) per image summary. Non lo banno per preservarlo per il Risk Engine.")
                    continue
                except Exception as e:
                    err_str = str(e)
                    short_err = err_str.split('. {')[0] if '. {' in err_str else (err_str[:150] + "..." if len(err_str) > 150 else err_str)
                    logger.debug(f"Gemini {model_name} fallito per image summary: {short_err}. Non lo banno.")
                    continue
            
            # Se tutti i modelli tentati in questo giro hanno fallito, controlliamo se sono tutti disabilitati ora
            if all(not _is_model_available(m) for m in models_to_try):
                logger.warning("Tutti i modelli Gemini hanno fallito per image summary. Fallback a Groq e disabilitazione temporanea di Gemini per media context...")
                _gemini_is_down = True
            
            # Fallback a Groq se Gemini fallisce (es. Rate Limit o Safety)
            from groq import Groq
            groq_api_key = env_config.get("GROQ_API_KEY")
            if groq_api_key:
                try:
                    groq_client = Groq(api_key=groq_api_key)
                    completion = groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                    return completion.choices[0].message.content.strip()
                except Exception as e:
                    logger.warning(f"Anche il fallback Groq ha fallito: {e}")
            
            return "Errore durante la generazione del riassunto AI."

        else:
            from groq import Groq
            groq_api_key = env_config.get("GROQ_API_KEY")
            if not groq_api_key:
                return "Riassunto AI non disponibile (Manca GROQ_API_KEY)."
                
            groq_client = Groq(api_key=groq_api_key)
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            return completion.choices[0].message.content.strip()

    except Exception as e:
        logger.warning(f"Errore in summarize_media_context: {e}")
        return "Errore durante la generazione del riassunto AI."
