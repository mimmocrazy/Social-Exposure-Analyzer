import asyncio
import uuid
import re
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session
from backend.schemas import AnalyzeRequest
from backend.models import ProfileAnalysis, AnalysisStatus
from backend.database import get_session
import backend.database
from backend.core.logger import logger
from backend.services.discovery import SherlockAdapter
from backend.services.scraper import gather_profile_metadata

router = APIRouter()

async def run_scraping_task(analysis_id: uuid.UUID, target: str):
    """
    Orchestra l'esecuzione di Discovery (se username) e Scraping dei metadati.
    Aggiorna lo stato del database al completamento.
    """
    if isinstance(analysis_id, str):
        analysis_id = uuid.UUID(analysis_id)
        
    try:
        urls_to_scrape = []
        
        # Validazione rudimentale per identificare se l'input è un URL diretto o uno username
        if re.match(r"^https?://", target):
            urls_to_scrape.append(target)
            logger.info("Target identificato come URL diretto.")
        else:
            logger.info("Target identificato come username, avvio pipeline Discovery...")
            discovery_adapter = SherlockAdapter()
            urls_to_scrape = discovery_adapter.discover_profiles(target)
        
        # Se non ho trovato URL validi in fase Discovery (o ne ho trovato zero)
        if not urls_to_scrape:
            raise Exception("Nessun URL utile trovato in fase di Discovery.")
            
        # Avvio pipeline Scraping asincrona
        raw_data = await gather_profile_metadata(urls_to_scrape)
        
        # Simulazione Aggregazione Testo (Scraping + OCR)
        combined_text = ""
        # TODO reale: scaricare immagini profilo e passarle a ocr.py
        # es: combined_text += extract_text_from_image(img_path)
        
        for profile in raw_data:
            if profile.get("title"): combined_text += profile["title"] + " "
            if profile.get("bio"): combined_text += profile["bio"] + " "
            
        # Limite di sicurezza Anti-DoS per l'analisi NLP
        if len(combined_text) > 10000:
            logger.warning(f"DoS Prevention: Testo troncato da {len(combined_text)} a 10000 caratteri prima dell'NLP.")
            combined_text = combined_text[:10000]
            
        # Estrazione PII (NLP Pipeline)
        from backend.services.nlp import extract_pii
        pii_results = extract_pii(combined_text)
        pii_dicts = [pii.model_dump() for pii in pii_results]
        
        # Risk Engine Analysis (Gemini Pro)
        from backend.services.risk_engine import calculate_risk
        risk_report = await calculate_risk(pii_dicts)
        
        # Aggiornamento Database con i dati raw, PII e Risk Score
        with Session(backend.database.engine) as session:
            analysis = session.get(ProfileAnalysis, analysis_id)
            if analysis:
                analysis.raw_data_dump = {"profiles": raw_data}
                analysis.pii_extracted = pii_dicts
                
                # Mapping campi Risk Engine sul DB Model
                analysis.risk_score = risk_report.score
                analysis.risk_level = risk_report.level.value
                analysis.llm_report = risk_report.model_dump_json()
                
                # Se abbiamo analizzato immagini, setta flag
                # analysis.has_images_analyzed = True
                
                analysis.status = AnalysisStatus.COMPLETED
                session.add(analysis)
                session.commit()
                logger.info(f"Task asincrono di OSINT e Risk Engine concluso per {analysis_id}")
                
    except Exception as e:
        logger.error(f"Fallimento durante l'orchestrazione asincrona {analysis_id}: {e}")
        with Session(backend.database.engine) as session:
            analysis = session.get(ProfileAnalysis, analysis_id)
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                session.add(analysis)
                session.commit()

@router.post("/analyze", status_code=202)
def analyze_profile(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    target_str = str(request.target_url)
    
    # Creazione record iniziale in DB
    analysis = ProfileAnalysis(
        target_url=target_str,
        status=AnalysisStatus.PENDING
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    
    # Affida l'orchestrazione al BackgroundTask nativo
    background_tasks.add_task(run_scraping_task, analysis.id, target_str)
    
    return {
        "message": "Richiesta OSINT presa in carico",
        "analysis_id": analysis.id
    }

@router.get("/analyze/{analysis_id}")
def get_analysis_status(
    analysis_id: uuid.UUID,
    session: Session = Depends(get_session)
):
    """
    Endpoint per il polling del Frontend.
    Restituisce lo stato corrente dell'analisi e, se COMPLETED, i risultati.
    """
    analysis = session.get(ProfileAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analisi non trovata")
        
    import json
    llm_report_parsed = None
    if analysis.llm_report:
        try:
            llm_report_parsed = json.loads(analysis.llm_report)
        except:
            llm_report_parsed = analysis.llm_report

    return {
        "id": analysis.id,
        "target_url": analysis.target_url,
        "status": analysis.status,
        "scan_date": analysis.scan_date,
        "risk_score": analysis.risk_score,
        "risk_level": analysis.risk_level,
        "pii_extracted": analysis.pii_extracted,
        "llm_report": llm_report_parsed,
        "error_message": analysis.error_message
    }
