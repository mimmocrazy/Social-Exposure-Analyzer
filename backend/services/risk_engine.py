import os
import json
from google import genai
from google.genai import types
from backend.models.risk import RiskReport
from backend.core.logger import logger

# Inizializza il client usando google-genai. 
# Richiede la variabile d'ambiente GEMINI_API_KEY
client = genai.Client()

async def calculate_risk(pii_data: list) -> RiskReport:
    """
    Analizza le PII estratte invocando Gemini Pro tramite Structured Outputs.
    Valuta il rischio di Social Engineering e restituisce un RiskReport garantito a livello di schema.
    """
    system_prompt = """
    Sei un esperto analista di Social Engineering e Sicurezza OSINT.
    Analizza il JSON delle PII (Personally Identifiable Information) estratte da profili social pubblici.
    
    Regole di Valutazione Rigide:
    1. Zero Allucinazioni: basati esclusivamente sui dati JSON forniti nel payload. 
    2. Calcola l'impatto (score 0-100). Esempio: Email + Telefono + Data di Nascita = Score Alto (facilita SIM Swapping o Phishing mirato). Solo Nome comune = Score Basso.
    3. Imposta `insufficient_data=True` e `score` sotto i 20 se i dati non bastano per ipotizzare un attacco reale.
    4. Elenca i vettori di minaccia concreti in `threat_vectors`.
    5. Fornisci consigli pratici in `mitigation_advice`.
    """
    
    # Prevenzione Data Leakage (OWASP A09): Limitiamo il payload ai soli dati utente (nessun secret di sistema)
    payload_str = json.dumps(pii_data, ensure_ascii=False)
    
    try:
        logger.info("Avvio analisi Risk Engine tramite Gemini Pro (Structured Output)...")
        # In contesto asincrono, possiamo sfruttare l'SDK se supporta aio o eseguirlo in thread.
        # Utilizziamo la sintassi sincrona standard dell'SDK all'interno del context asincrono
        response = client.models.generate_content(
            model='gemini-2.5-pro',
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
