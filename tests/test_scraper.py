import pytest
from backend.services.scraper import gather_profile_metadata

@pytest.mark.asyncio
async def test_gather_profile_metadata_success(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.text = '<html><head><title>John Doe</title><meta name="description" content="Software Engineer @ Tech"/></head></html>'
    
    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)
    
    results = await gather_profile_metadata(["https://example.com/johndoe"])
    
    assert len(results) == 1
    assert results[0]["status"] == "ACCESSIBLE"
    assert results[0]["title"] == "John Doe"
    assert results[0]["bio"] == "Software Engineer @ Tech"

@pytest.mark.asyncio
async def test_gather_profile_metadata_ssrf_protection():
    # Verifica che le richieste verso localhost o IP interni vengano scartate
    results = await gather_profile_metadata(["http://localhost:8080/admin", "http://192.168.1.10/router"])
    
    assert len(results) == 2
    for r in results:
        assert r["status"] == "PROTECTED"
        assert r["error"] == "SSRF Policy Violation"

@pytest.mark.asyncio
async def test_gather_profile_metadata_http_error(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 403
    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)
    
    results = await gather_profile_metadata(["https://example.com/private"])
    
    assert results[0]["status"] == "PROTECTED"
    assert "HTTP Error 403" in results[0]["error"]
