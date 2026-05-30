from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dos_prevention_payload_too_large():
    """
    Testa il middleware globale anti-DoS introdotto tramite Autonomous Optimization.
    Un payload massivo (superiore ai 10.000 byte) deve essere bloccato istantaneamente
    restituendo un HTTP 413 Payload Too Large.
    """
    huge_string = "A" * 10001
    payload = {"target_url": huge_string}
    
    response = client.post("/api/v1/analyze", json=payload)
    
    # Verifica che il middleware abbia intercettato e rifiutato la richiesta
    assert response.status_code == 413
    assert response.json() == {"detail": "Payload Too Large. Max size is 10000 bytes."}
