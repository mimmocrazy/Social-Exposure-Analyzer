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
    Sei un esperto analista di Social Engineering e Sicurezza OSINT.
    Riceverai in input un JSON STRUTTURATO contenente i risultati di vari moduli OSINT (es. DuckDuckGo, Holehe, Instagram).
    
    ATTENZIONE - IDENTIFICAZIONE DEL BERSAGLIO E FALSI POSITIVI:
    Il tuo BERSAGLIO ESATTO è: {target_info}.
    Ignora rigorosamente qualsiasi PII o dato appartenente a omonimi o ad altre persone menzionate nei risultati.
    
    ATTENZIONE - GESTIONE ALLUCINAZIONI E PROFILI PRIVATI:
    Nel JSON, controlla il campo `status`. Se lo status è `PROTECTED` o `LOGIN_WALL` o un errore 429, significa che quel modulo ha fallito l'estrazione.
    Se TUTTI i moduli non hanno restituito alcun dato valido sul bersaglio, imposta `insufficient_data=True` e lascia il resto vuoto.
    Se invece hai trovato dati validi (es. tramite Holehe o DuckDuckGo), procedi regolarmente.
    
    Il tuo compito:
    1. Estrai le PII valide in `pii_extracted`.
    2. Valuta il rischio globale (`score` da 0 a 100) ma rendilo MATEMATICAMENTE TRASPARENTE usando `score_breakdown`.
       Assegna punti esatti in base ai ritrovamenti. Es: 
       - "Trovata email esposta tramite DuckDuckGo": +20 punti
       - "Holehe ha rilevato l'iscrizione a 3 siti esterni": +15 punti
       - "Rilevata potenziale geolocalizzazione o luogo di lavoro": +15 punti
       La somma di questi punti DEVE essere uguale al `score` finale.
    3. Calcola i `sub_scores` (identity_exposure, network_exposure, routine_exposure) da 0 a 100 per mostrare su quali assi l'utente è più esposto.
    4. Popola `threat_vectors` derivati da questi dati reali.
    5. Fornisci `mitigation_advice` e `mitigation_sections` basati ESATTAMENTE sui dati che hai trovato.
    """
    
    payload_str = raw_text[:20000] # Limite di sicurezza stringa

    
    try:
        logger.info("Avvio analisi Risk Engine tramite Gemini Pro (Structured Output)...")
        # In contesto asincrono, possiamo sfruttare l'SDK se supporta aio o eseguirlo in thread.
        # Utilizziamo la sintassi sincrona standard dell'SDK all'interno del context asincrono
        client = get_client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=payload_str,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=RiskReport,
                temperature=0.2, # Basso per risposte deterministiche e formali
            ),
        )
        
        # Validazione Pydantic sicura della risposta text JSON-like
        report = RiskReport.model_validate_json(response.text)
        return report
        
    except Exception as e:
        logger.error(f"Errore critico durante l'analisi Risk Engine: {e}")
        # Fallback sicuro in caso di downtime AI o refusal
        from backend.models.risk import RiskSubScores
        return RiskReport(
            score=0,
            sub_scores=RiskSubScores(identity_exposure=0, network_exposure=0, routine_exposure=0),
            level="LOW",
            threat_vectors=["Analisi non completata per errore di sistema LLM"],
            mitigation_advice="Controllare manualmente l'esposizione dei dati.",
            mitigation_sections=[],
            insufficient_data=True,
            pii_extracted=[]
        )
