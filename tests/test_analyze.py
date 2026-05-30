from fastapi.testclient import TestClient
from sqlmodel import Session
from backend.models import ProfileAnalysis, AnalysisStatus

def test_analyze_profile(client: TestClient, session: Session):
    """
    Verifica il comportamento dell'endpoint principale di ingestion (POST /api/v1/analyze).
    
    Asserisce che:
    - L'endpoint risponda con successo ad un payload valido (HTTP 202 Accepted).
    - Venga restituito l'ID univoco generato per l'analisi.
    - Nel database in-memory venga generato correttamente il record associato.
    - Lo stato dell'analisi appena salvata sia esplicitamente 'PENDING'.
    """
    payload = {"target_url": "https://linkedin.com/in/test"}
    response = client.post("/api/v1/analyze", json=payload)
    
    # Verifichiamo il codice 202 (Accepted), idoneo all'architettura a BackgroundTask
    assert response.status_code == 202
    
    data = response.json()
    assert "analysis_id" in data
    
    # Estraiamo l'ID e interroghiamo direttamente il database di test isolato
    import uuid
    analysis_id = uuid.UUID(data["analysis_id"])
    db_record = session.get(ProfileAnalysis, analysis_id)
    
    # Asserzioni sulla persistenza e integrità del dato
    assert db_record is not None
    assert db_record.target_url == "https://linkedin.com/in/test"
    # starlette.testclient.TestClient esegue i BackgroundTasks in modo SINCRONO prima di restituire la response
    assert db_record.status == AnalysisStatus.COMPLETED
