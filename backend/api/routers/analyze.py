import asyncio
import uuid
import re
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session
from backend.schemas import AnalyzeRequest
from backend.models import ProfileAnalysis, AnalysisStatus
from backend.database import get_session, engine
from backend.core.logger import logger
from backend.services.discovery import SherlockAdapter
from backend.services.scraper import gather_profile_metadata

router = APIRouter()

async def run_scraping_task(analysis_id: uuid.UUID, target: str):
    """
    Orchestra l'esecuzione di Discovery (se username) e Scraping dei metadati.
    Aggiorna lo stato del database al completamento.
    """
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
        
        # Aggiornamento Database con i dati raw
        with Session(engine) as session:
            analysis = session.get(ProfileAnalysis, analysis_id)
            if analysis:
                analysis.raw_data_dump = {"profiles": raw_data}
                analysis.status = AnalysisStatus.COMPLETED
                session.add(analysis)
                session.commit()
                logger.info(f"Task asincrono di OSINT concluso per {analysis_id}")
                
    except Exception as e:
        logger.error(f"Fallimento durante l'orchestrazione asincrona {analysis_id}: {e}")
        with Session(engine) as session:
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
