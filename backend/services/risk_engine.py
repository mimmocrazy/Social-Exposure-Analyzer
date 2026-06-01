import os
import json
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

    ### 2. DIRETTIVE DI ESTRAZIONE PII (ZERO DATA LOSS)
    Devi operare con meticolosità estrema. Ispeziona ogni singola stringa in `scraper_results`, `ocr_results` (sia testo che descrizioni AI) e `spacy_entities`.
    Estrai e mappa in `pii_extracted` ogni possibile traccia utile per l'Ingegneria Sociale:
    - IDENTITY / RELATIONAL: Nomi completi, età, date di nascita, nomi di parenti e amici.
    - CONTACT / ACCOUNT: Email, telefoni, handle social alternativi, username, account su piattaforme terze.
    - PROFESSIONAL: Luogo di lavoro, ruoli, badge aziendali, ID dipendente.
    - LOGISTICS / ROUTINE: Indirizzi fisici, tracciamenti pacchi, carte d'imbarco, targhe, luoghi frequentati abitualmente, check-in.
    - ALTRE INFO: Qualsiasi altro dettaglio estraibile dalle foto e dai testi (es. hobby, eventi, marchi).

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
    - `mitigation_sections`: Crea UNA SEZIONE PER OGNI MACRO-CATEGORIA di rischio individuata. DEVI assolutamente creare sezioni dedicate alle vulnerabilità derivanti dalle IMMAGINI (es. "Ingegneria Sociale via Badge Aziendale", "Tracciamento Fisico via Carta d'Imbarco" o "Clonazione Targa"). Ogni sezione DEVE contenere:
        - `title`: Nome della categoria o vulnerabilità.
        - `threat_vector`: Il vettore di attacco esatto (es. "Spear Phishing", "Physical Tracking", "Social Engineering via Impersonazione").
        - `exposed_data`: Citazione letterale e precisa del dato (es. "Foto con Badge Aziendale visibile", "Post con nomi dei genitori"). Non essere vago.
        - `criticality`: CRITICA | ALTA | MEDIA | BASSA.
        - `mitigation`: Minimo 3-4 azioni correttive CONCRETE, PRATICHE e IMMEDIATE descritte estesamente.endale").
    """
    
    max_payload = 60000
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
            
            models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']
            response = None
            last_err = None
            
            for model_name in models_to_try:
                try:
                    logger.info(f"Tentativo di generazione report con modello {model_name}...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=payload_str,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            response_schema=RiskReport,
                            temperature=0.2, 
                        ),
                    )
                    logger.info(f"Successo con il modello {model_name}!")
                    break
                except Exception as e:
                    logger.warning(f"Errore con il modello {model_name}: {e}. Provo il prossimo modello di fallback...")
                    last_err = e
                    
            if response is None:
                raise last_err
            
            report = RiskReport.model_validate_json(response.text)
            return report
            
    except Exception as e:
        logger.error(f"Errore critico durante l'analisi Risk Engine: {e}")
        # Rilancia l'eccezione per far fallire correttamente l'analisi asincrona
        raise e

async def summarize_media_context(raw_text: str, caption: str = None) -> str:
    """Genera una descrizione contestuale chiara da OCR e caption."""
    try:
        import os
        from dotenv import dotenv_values
        env_config = dotenv_values(".env")
        ai_provider = env_config.get("AI_PROVIDER", "gemini").lower()
        
        prompt = f"Hai il seguente testo estratto (OCR) da una foto o screenshot:\n\n{raw_text}\n\n"
        if caption:
            prompt += f"Inoltre, il post originale contiene questa didascalia (caption): {caption}\n\n"
            
        prompt += "Scrivi ESATTAMENTE E SOLO una breve e chiara descrizione (1-2 frasi) di cosa rappresenta la foto e se espone nomi, contatti o dettagli utili per ingegneria sociale (es. 'Carta d'imbarco di Mario Rossi', 'Conversazione whatsapp con il numero 3331234567')."

        if ai_provider == "gemini":
            client = get_client()
            models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-flash-latest']
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    return response.text.strip()
                except Exception as e:
                    logger.debug(f"Gemini {model_name} fallito per image summary: {e}")
                    continue
            
            logger.warning("Tutti i modelli Gemini hanno fallito per image summary. Fallback a Groq...")
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
