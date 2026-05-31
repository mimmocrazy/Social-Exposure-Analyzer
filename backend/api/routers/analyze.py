import asyncio
import uuid
import re
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session
from backend.schemas import AnalyzeRequest
from backend.models import ProfileAnalysis, AnalysisStatus
from backend.database import get_session
import backend.database
from backend.models.user import User
from backend.api.routers.auth import get_current_user
from backend.core.logger import logger
from backend.services.discovery import SherlockAdapter
from backend.services.scraper import gather_profile_metadata

router = APIRouter()

async def guess_real_name(username: str) -> str:
    """Usa l'LLM per dedurre il nome reale dall'username per potenziare l'OSINT."""
    try:
        from backend.services.risk_engine import get_client
        client = get_client()
        prompt = f"Data l'username '{username}', deduci il probabile nome e cognome reale. Rispondi SOLO con il nome e cognome testuale, o 'Sconosciuto' se è totalmente impossibile da dedurre. Esempio 1: mario.rossi89 -> Mario Rossi. Esempio 2: tomasmontagna_ -> Tomas Montagna."
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        name = response.text.strip()
        if name and name.lower() != 'sconosciuto':
            return name
    except Exception as e:
        logger.warning(f"Errore durante la deduzione del nome per {username}: {e}")
    return None

async def run_scraping_task(
    analysis_id: uuid.UUID, 
    target: str,
    enable_ddg: bool = True,
    enable_holehe: bool = True,
    ig_sessionid: str = None
):
    """
    Orchestra l'esecuzione di Discovery (se username) e Scraping dei metadati.
    Aggiorna lo stato del database al completamento.
    """
    if isinstance(analysis_id, str):
        analysis_id = uuid.UUID(analysis_id)
        
    try:
        urls_to_scrape = []
        real_name_deduced = None
        
        # Validazione rudimentale per identificare se l'input è un URL diretto o uno username
        if re.match(r"^https?://", target):
            urls_to_scrape.append(target)
            logger.info("Target identificato come URL diretto.")
        else:
            logger.info("Target identificato come username, avvio pipeline Discovery...")
            discovery_adapter = SherlockAdapter()
            urls_to_scrape = discovery_adapter.discover_profiles(target)
            
            logger.info(f"Avvio deduzione identità tramite LLM per l'username: {target}")
            real_name_deduced = await guess_real_name(target)
            if real_name_deduced:
                logger.info(f"Nome reale dedotto con successo: {real_name_deduced}")
        
        # Se non ho trovato URL validi in fase Discovery (o ne ho trovato zero)
        if not urls_to_scrape:
            raise Exception("Nessun URL utile trovato in fase di Discovery.")
            
        # Avvio pipeline Scraping asincrona con i nuovi flag
        raw_data = await gather_profile_metadata(
            urls_to_scrape, 
            real_name=real_name_deduced,
            enable_ddg=enable_ddg,
            ig_sessionid=ig_sessionid
        )
        
        # Aggregazione Testo
        combined_text = ""
        
        for profile in raw_data:
            if profile.get("title"): combined_text += profile["title"] + " "
            if profile.get("bio"): combined_text += profile["bio"] + " "

        # HOLEHE INTEGRATION
        if enable_holehe:
            # Semplice regex per trovare email nel testo
            emails_found = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', combined_text)))
            if emails_found:
                logger.info(f"Trovate {len(emails_found)} email per Holehe OSINT: {emails_found}")
                from backend.services.holehe_adapter import run_holehe
                for em in emails_found:
                    sites = await run_holehe(em)
                    if sites:
                        holehe_str = f"\n[OSINT HOLEHE] L'email {em} risulta registrata su questi account: {', '.join(sites)}."
                        combined_text += holehe_str
                        logger.info(holehe_str)
            
        # Limite di sicurezza Anti-DoS per l'analisi NLP
        if len(combined_text) > 10000:
            logger.warning(f"DoS Prevention: Testo troncato da {len(combined_text)} a 10000 caratteri prima dell'NLP.")
            combined_text = combined_text[:10000]
            
        # Risk Engine Analysis (Gemini Flash) tramite text integrale e OSINT
        from backend.services.risk_engine import calculate_risk
        risk_report = await calculate_risk(combined_text)
        
        pii_dicts = [pii.model_dump() for pii in risk_report.pii_extracted]
        
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
def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    target_str = str(request.target_url)
    
    # Creazione record iniziale in DB
    analysis = ProfileAnalysis(
        target_url=target_str,
        status=AnalysisStatus.PENDING,
        user_id=current_user.id
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    
    # Affida l'orchestrazione al BackgroundTask nativo
    background_tasks.add_task(
        run_scraping_task, 
        analysis.id, 
        target_str,
        request.enable_ddg,
        request.enable_holehe,
        request.ig_sessionid
    )
    
    return {
        "message": "Richiesta OSINT presa in carico",
        "analysis_id": analysis.id
    }

@router.get("/analyze/{analysis_id}")
def get_analysis_status(
    analysis_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint per il polling del Frontend.
    Restituisce lo stato corrente dell'analisi e, se COMPLETED, i risultati.
    """
    analysis = session.get(ProfileAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analisi non trovata")
        
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato a visualizzare questa analisi")
        
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
