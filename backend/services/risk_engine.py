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
    
    ATTENZIONE - GESTIONE ALLUCINAZIONI E PROFILI PRIVATI:
    Se nel testo trovi il tag "[WARNING: PROFILO PRIVATO O INACCESSIBILE. NON INVENTARE DATI.]" o noti che i dati sono palesemente vuoti o limitati a form di login:
    - DEVI impostare `insufficient_data=True`.
    - NON DEVI in alcun modo inventare o dedurre PII fittizie. Lascia `pii_extracted` vuoto.
    - Specifica nei `mitigation_advice` e nelle `mitigation_sections` che il profilo ha esposizione nulla in quanto adeguatamente protetto da impostazioni di privacy (il rischio è BASSO).
    
    Il tuo compito in un singolo passaggio sui dati effettivamente trovati:
    1. Analizza il testo fornito.
    2. Estrai tutte le PII (Personally Identifiable Information) realmente presenti e popolale in `pii_extracted`.
    3. Valuta il rischio globale (`score` da 0 a 100).
    4. Calcola in `sub_scores` i seguenti punteggi (da 0 a 100):
       - `identity_exposure`: Rischio legato a dati anagrafici, contatti (email, telefono). Se trovi il tag [OSINT HOLEHE] che indica account registrati su altre piattaforme, questo punteggio DEVE alzarsi molto perché l'identità è diffusa.
       - `network_exposure`: Rischio legato a legami familiari, amici, colleghi esposti (rischio di attacchi a catena).
       - `routine_exposure`: Rischio legato a luoghi frequentati, geolocalizzazioni o abitudini.
    5. Popola `threat_vectors` con minacce derivate applicando questi concetti chiave del Social Engineering: 
       Evidenzia in particolare se "la pubblicazione ricorrente di luoghi frequentati, routine quotidiane, informazioni lavorative e legami familiari può facilitare tentativi di impersonificazione o messaggi fraudolenti personalizzati".
       (Menziona esplicitamente se hai trovato account correlati tramite Holehe e come questo amplia il vettore di attacco).
    6. Fornisci un `mitigation_advice` generale.
    7. Fornisci `mitigation_sections` dividendo il report in macrosezioni logiche in base ai dati trovati (es. "Esposizione Canali di Contatto", "Dati Anagrafici e Sensibili", "Relazioni Personali e Network", "Informazioni Professionali e Aziendali", ecc.).
       Per ciascuna macrosezione devi indicare:
       - `title`: Il nome della macrosezione
       - `exposed_data`: Quali dati esatti sono stati trovati esposti in questa categoria (citando i dati effettivi, es: "email info@...", "relazioni con Camilla, Alice").
       - `criticality`: Il livello di criticità associato a questa esposizione (es. CRITICA, ALTA, MEDIA, BASSA).
       - `mitigation`: Consigli ed azioni correttive specifiche per proteggere quella specifica macrosezione.
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
