from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_contract_flow():
    """
    Testa il contratto API completo: Ingestion -> Polling.
    Autonomus Optimization: Utilizzato il TestClient di FastAPI per testare 
    il routing in modo deterministico e ad alte prestazioni.
    """
    # 1. Ingestion
    payload = {"target_url": "https://example.com/integration-test"}
    post_response = client.post("/api/v1/analyze", json=payload)
    
    assert post_response.status_code == 202, "L'endpoint di ingestion deve restituire 202 Accepted"
    data = post_response.json()
    assert "analysis_id" in data, "L'API deve restituire l'ID dell'analisi"
    
    analysis_id = data["analysis_id"]
    
    # 2. Polling
    get_response = client.get(f"/api/v1/analyze/{analysis_id}")
    assert get_response.status_code == 200, "L'endpoint di polling deve rispondere con 200 OK"
    
    poll_data = get_response.json()
    assert poll_data["id"] == analysis_id, "L'ID restituito dal polling deve combaciare con l'ingestion"
    assert poll_data["status"] in ["PENDING", "COMPLETED", "FAILED"], "Lo stato non è riconosciuto"
