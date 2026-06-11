import os
import json
import time
from google import genai
from google.genai import types
from backend.models.risk import RiskReport, ScoreBreakdown
from backend.models import RiskLevel
from backend.core.logger import logger

import re

def _get_all_gemini_keys():
    keys = []
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if "GEMINI_API_KEY" in line:
                    match = re.search(r'GEMINI_API_KEY\s*=\s*["\']?(AQ\.[\w-]+)["\']?', line)
                    if match:
                        keys.append(match.group(1))
    
    current_env_key = os.getenv("GEMINI_API_KEY")
    if current_env_key and current_env_key not in keys:
        keys.append(current_env_key)
        
    seen = set()
    return [k for k in keys if not (k in seen or seen.add(k))]

_gemini_keys_pool = _get_all_gemini_keys()
_current_key_idx = 0
_client = None

def get_client():
    global _client, _current_key_idx, _gemini_keys_pool
    if _client is None:
        if _gemini_keys_pool:
            _client = genai.Client(api_key=_gemini_keys_pool[_current_key_idx])
            logger.info(f"Inizializzato Gemini con chiave {_current_key_idx+1}/{len(_gemini_keys_pool)}")
        else:
            _client = genai.Client()
    return _client

def rotate_gemini_key() -> bool:
    global _client, _current_key_idx, _gemini_keys_pool, _disabled_models
    if not _gemini_keys_pool or len(_gemini_keys_pool) <= 1:
        return False
    _current_key_idx = (_current_key_idx + 1) % len(_gemini_keys_pool)
    logger.warning(f"🔄 ROTAZIONE CHIAVE GEMINI: Passo alla chiave {_current_key_idx + 1}/{len(_gemini_keys_pool)}")
    _client = genai.Client(api_key=_gemini_keys_pool[_current_key_idx])
    _disabled_models.clear()
    return True

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

    ### 3. VALUTAZIONE DELLA CRITICITÀ
    NON generare tu un punteggio `score` o `sub_scores` globale, questi campi verranno calcolati matematicamente a valle dal sistema centrale. Per conformità allo schema JSON, imposta pure a 0 quei valori.
    Concentrati sull'attribuire una `criticality` ESTREMAMENTE precisa (CRITICA, ALTA, MEDIA, BASSA) ad ogni singola vulnerabilità individuata in `mitigation_sections`. Sii spietato.
    - Dati CRITICI: Email esposte, Data Breach, Password, Badge.
    - Dati ALTI: Numeri di telefono, indirizzi, documenti fisici di viaggio, targhe.
    - Dati MEDI: Relazioni familiari o colleghi identificati.
    - Dati BASSI: Luoghi o Routine generiche identificate.

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
    global _gemini_is_down
    
    if isinstance(raw_text, (dict, list)):
        import json
        raw_text = json.dumps(raw_text)
    else:
        raw_text = str(raw_text)
        
    max_payload = 100000
    if len(raw_text) > max_payload:
        logger.warning(f"Risk Engine: payload troncato da {len(raw_text)} a {max_payload} caratteri per sicurezza.")
    payload_str = raw_text[:max_payload]
    
    from dotenv import dotenv_values
    env_config = dotenv_values(".env")
    ai_provider = env_config.get("AI_PROVIDER", "gemini").lower()
    
    try:
        async def call_gemini():
            logger.info("Avvio analisi Risk Engine tramite Gemini Pro (Strutturato con Fallback/Rotazione)...")
            gemini_available = any(_is_model_available(m) for m in ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-pro-latest'])
            if not gemini_available or _gemini_is_down:
                raise Exception("Tutti i modelli Gemini sono down o in timeout.")
                
            models_to_try = ['gemini-flash-latest', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-pro-latest']
            keys_tried = 0
            max_keys = max(1, len(_gemini_keys_pool))
            
            while keys_tried < max_keys:
                client = get_client()
                active_models = [m for m in models_to_try if _is_model_available(m)]
                if not active_models:
                    active_models = models_to_try
                
                response = None
                for model_name in active_models:
                    try:
                        logger.info(f"Tentativo con Gemini {model_name}...")
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
                        logger.info(f"Successo con Gemini {model_name}!")
                        break
                    except asyncio.TimeoutError:
                        _mark_model_failed(model_name, asyncio.TimeoutError())
                    except Exception as e:
                        _mark_model_failed(model_name, e)
                        
                if response is not None:
                    return RiskReport.model_validate_json(response.text)
                    
                keys_tried += 1
                if keys_tried < max_keys:
                    rotate_gemini_key()
                else:
                    raise Exception("Tutte le chiavi Gemini hanno fallito in rotazione.")
            raise Exception("Chiamata Gemini fallita.")

        async def call_github():
            logger.info("Avvio analisi Risk Engine tramite GitHub Models (Azure AI)...")
            import openai
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token or github_token == "INSERISCI_QUI_IL_TUO_GITHUB_PAT":
                raise Exception("GITHUB_TOKEN non configurato o vuoto.")
                
            client = openai.OpenAI(base_url="https://models.inference.ai.azure.com", api_key=github_token)
            schema_instructions = f"\n\nRispondi RIGOROSAMENTE con un oggetto JSON che rispetti questo schema:\n{RiskReport.model_json_schema()}"
            
            try:
                completion = client.chat.completions.create(
                    messages=[{"role": "system", "content": system_prompt + schema_instructions}, {"role": "user", "content": payload_str}],
                    model="gpt-4o-mini", temperature=0.2, response_format={"type": "json_object"}
                )
                return RiskReport.model_validate_json(completion.choices[0].message.content)
            except Exception as e:
                logger.warning(f"Errore gpt-4o-mini: {e}. Fallback interno a gpt-4o...")
                completion = client.chat.completions.create(
                    messages=[{"role": "system", "content": system_prompt + schema_instructions}, {"role": "user", "content": payload_str}],
                    model="gpt-4o", temperature=0.2, response_format={"type": "json_object"}
                )
                return RiskReport.model_validate_json(completion.choices[0].message.content)

        async def call_groq():
            logger.info("Avvio analisi Risk Engine tramite Groq (Llama 3.3 70B)...")
            from groq import Groq
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise Exception("GROQ_API_KEY non configurata.")
            groq_client = Groq(api_key=groq_api_key)
            schema_json = json.dumps(RiskReport.model_json_schema())
            groq_sys_prompt = system_prompt + f"\nRESTITUISCI ESATTAMENTE UN OGGETTO JSON CON LA SEGUENTE STRUTTURA: {schema_json}\nNon aggiungere NESSUN ALTRO TESTO."
            
            def _call_groq_risk():
                return groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": groq_sys_prompt}, {"role": "user", "content": payload_str}],
                    temperature=0.2, response_format={"type": "json_object"}
                )
            import asyncio
            completion = await asyncio.wait_for(asyncio.to_thread(_call_groq_risk), timeout=30.0)
            return RiskReport.model_validate_json(completion.choices[0].message.content)

        # Matrice di Fallback basata su AI_PROVIDER
        providers = [
            ("Gemini Pro", call_gemini),
            ("GitHub Models", call_github),
            ("Groq", call_groq)
        ]
        
        if ai_provider == "github":
            providers = [("GitHub Models", call_github), ("Groq", call_groq), ("Gemini Pro", call_gemini)]
        elif ai_provider == "groq":
            providers = [("Groq", call_groq), ("GitHub Models", call_github), ("Gemini Pro", call_gemini)]

        report = None
        for name, func in providers:
            try:
                report = await func()
                if report:
                    break
            except Exception as e:
                err_str = str(e).split('. {')[0] if '. {' in str(e) else str(e)[:150]
                logger.warning(f"Rete non disponibile sul nodo {name} ({err_str}). Switch al provider di Fallback in corso...")
                if name == "Gemini Pro":
                    global _gemini_is_down
                    _gemini_is_down = True
                
        if not report:
            raise RuntimeError("Alta disponibilità esaurita: tutti i nodi AI mondiali (Gemini, GitHub, Groq) sono irraggiungibili.")

        # --- Calcolo Deterministico dello Score ---
        def calculate_deterministic_risk(rep: RiskReport) -> RiskReport:
            total_score = 0
            breakdown = []
            sub_identity = 0
            sub_network = 0
            sub_routine = 0
            
            for section in rep.mitigation_sections:
                crit = section.criticality.upper()
                points = 0
                if "CRITICA" in crit:
                    points = 25
                elif "ALTA" in crit:
                    points = 15
                elif "MEDIA" in crit:
                    points = 5
                elif "BASSA" in crit:
                    points = 2
                
                if points > 0:
                    total_score += points
                    breakdown.append(ScoreBreakdown(
                        reason=f"[{section.criticality}] {section.title}",
                        points_added=points
                    ))
                
                # Euristiche per smistare i punti nelle 3 categorie (Identity, Network, Routine)
                tv = (section.threat_vector + " " + section.title).lower()
                if "routine" in tv or "luog" in tv or "track" in tv or "fisic" in tv or "viaggi" in tv or "targa" in tv:
                    sub_routine += points
                elif "relazion" in tv or "social" in tv or "famigl" in tv or "network" in tv or "colleg" in tv or "amici" in tv:
                    sub_network += points
                else:
                    sub_identity += points
            
            # Applica un cap a 100
            rep.score = min(100, max(0, total_score))
            rep.score_breakdown = breakdown
            
            # Popola i threat vectors estratti in modo che il frontend li legga
            extracted_threats = []
            for section in rep.mitigation_sections:
                if section.threat_vector and section.threat_vector not in extracted_threats:
                    extracted_threats.append(section.threat_vector)
            
            if not rep.threat_vectors:
                rep.threat_vectors = extracted_threats
            else:
                for t in extracted_threats:
                    if t not in rep.threat_vectors:
                        rep.threat_vectors.append(t)
            
            # Sub-scores calcolati matematicamente (moltiplicati per avere un peso visivo sulla progress bar, max 100)
            if rep.sub_scores:
                rep.sub_scores.identity_exposure = min(100, int(sub_identity * 2.0))
                rep.sub_scores.network_exposure = min(100, int(sub_network * 2.0))
                rep.sub_scores.routine_exposure = min(100, int(sub_routine * 2.0))
            
            # Sincronizza il RiskLevel con lo score matematico
            if rep.score >= 75:
                rep.level = RiskLevel.CRITICAL
            elif rep.score >= 50:
                rep.level = RiskLevel.HIGH
            elif rep.score >= 25:
                rep.level = RiskLevel.MEDIUM
            else:
                rep.level = RiskLevel.LOW
            
            logger.info(f"Punteggio di rischio deterministico calcolato: {rep.score}/100")
            return rep

        report = calculate_deterministic_risk(report)
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

        if ai_provider == "github":
            import openai
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token and github_token != "INSERISCI_QUI_IL_TUO_GITHUB_PAT":
                client = openai.OpenAI(
                    base_url="https://models.inference.ai.azure.com",
                    api_key=github_token,
                )
                try:
                    completion = client.chat.completions.create(
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        model="gpt-4o-mini",
                        temperature=0.2,
                    )
                    return completion.choices[0].message.content.strip()
                except Exception as e:
                    logger.warning(f"Errore gpt-4o-mini image context: {e}. Fallback a Gemini...")
                    ai_provider = "gemini"
            else:
                ai_provider = "gemini"

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
                    logger.debug(f"Gemini {model_name} in TIMEOUT (12s) per image summary.")
                    _mark_model_failed(model_name, asyncio.TimeoutError())
                    continue
                except Exception as e:
                    err_str = str(e)
                    short_err = err_str.split('. {')[0] if '. {' in err_str else (err_str[:150] + "..." if len(err_str) > 150 else err_str)
                    logger.debug(f"Gemini {model_name} fallito per image summary: {short_err}")
                    _mark_model_failed(model_name, e)
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
