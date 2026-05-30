import asyncio
import uuid
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session
from backend.schemas import AnalyzeRequest
from backend.models import ProfileAnalysis, AnalysisStatus
from backend.database import get_session, engine

router = APIRouter()

async def mock_scraping_task(analysis_id: uuid.UUID):
    # Simulazione processing asincrono
    await asyncio.sleep(3)
    
    # Istanziamo una nuova sessione isolata per il background task
    with Session(engine) as session:
        analysis = session.get(ProfileAnalysis, analysis_id)
        if analysis:
            analysis.status = AnalysisStatus.COMPLETED
            session.add(analysis)
            session.commit()

@router.post("/analyze", status_code=202)
def analyze_profile(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    # Creazione record in DB
    analysis = ProfileAnalysis(
        target_url=str(request.target_url),
        status=AnalysisStatus.PENDING
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    
    # Affida task in background
    background_tasks.add_task(mock_scraping_task, analysis.id)
    
    return {
        "message": "Richiesta presa in carico",
        "analysis_id": analysis.id
    }
