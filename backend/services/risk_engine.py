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

async def calculate_risk(raw_text: str) -> RiskReport:
    """
    Analizza il testo raw estratto invocando Gemini Pro.
    Estrea le PII e valuta il rischio di Social Engineering in un colpo solo.
    """
    system_prompt = """
    Sei un esperto analista di Social Engineering e Sicurezza OSINT.
    Ti fornirò un testo raw aggregato da scraping web e ricerche OSINT.
    
    Il tuo compito in un singolo passaggio:
    1. Analizza il testo fornito.
    2. Valuta il rischio di esposizione. Se trovi un semplice username o una bio generica il rischio è BASSO. Se trovi possibili collegamenti, email, scuole o posizioni lavorative il rischio sale.
    3. Popola `threat_vectors` con possibili minacce derivate (es. Phishing mirato se c'è un'azienda).
    4. Fornisci `mitigation_advice` per rimediare.
    5. Imposta `insufficient_data=True` se il testo non contiene nulla di utile per un attacco.
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
        return RiskReport(
            score=0,
            level="LOW",
            threat_vectors=["Analisi non completata per errore di sistema LLM"],
            mitigation_advice="Controllare manualmente l'esposizione dei dati.",
            insufficient_data=True
        )
