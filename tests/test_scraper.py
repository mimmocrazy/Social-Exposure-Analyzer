import pytest
from backend.services.scraper import gather_profile_metadata

@pytest.mark.asyncio
async def test_gather_profile_metadata_success(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.text = '<html><head><title>John Doe</title><meta name="description" content="Software Engineer @ Tech"/></head></html>'
    
    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)
    
    results = await gather_profile_metadata(["https://example.com/johndoe"], enable_ddg=False)
    
    assert len(results) == 1
    assert results[0]["status"] == "ACCESSIBLE"
    assert results[0]["title"] == "John Doe"
    assert results[0]["bio"] == "Software Engineer @ Tech"

@pytest.mark.asyncio
async def test_gather_profile_metadata_ssrf_protection():
    # Verifica che le richieste verso localhost o IP interni vengano scartate
    results = await gather_profile_metadata(["http://localhost:8080/admin", "http://192.168.1.10/router"], enable_ddg=False)
    
    assert len(results) == 2
    for r in results:
        assert r["status"] == "PROTECTED"
        assert r["error"] == "SSRF Policy Violation"

@pytest.mark.asyncio
async def test_gather_profile_metadata_http_error(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 403
    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)
    
    results = await gather_profile_metadata(["https://example.com/private"], enable_ddg=False)
    
    assert results[0]["status"] == "PROTECTED"
    assert "HTTP Error 403" in results[0]["error"]

@pytest.mark.asyncio
async def test_instagram_deep_scan_success(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.json = mocker.MagicMock(return_value={
        "data": {"user": {"full_name": "Test User", "biography": "Hello", "edge_owner_to_timeline_media": {"edges": []}}}
    })
    type(mock_response).text = mocker.PropertyMock(return_value='<html><body>IG JSON</body></html>')
    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)
    
    results = await gather_profile_metadata(["https://instagram.com/test"], ig_sessionid="123", enable_ddg=False)
    
    assert any(r["source"] == "Instagram Deep Scan API" for r in results)

@pytest.mark.asyncio
async def test_facebook_deep_scan_success(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.text = '<html><body>Test FB text</body></html>'
    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)
    
    results = await gather_profile_metadata(["https://facebook.com/test"], enable_fb_scan=True, fb_sessionid="c_user=123", enable_ddg=False)
    assert any(r["source"] == "Facebook Deep Scan API" and "Test FB text" in r["bio"] for r in results)

@pytest.mark.asyncio
async def test_facebook_deep_scan_login_wall(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.text = '<html><body>accedi a facebook</body></html>'
    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)
    
    results = await gather_profile_metadata(["https://facebook.com/test"], enable_fb_scan=True, fb_sessionid="c_user=123", enable_ddg=False)
    assert any(r["error"] == "Login Wall" for r in results)

@pytest.mark.asyncio
async def test_duckduckgo_success(mocker):
    # Mock GET fallito
    mock_get = mocker.AsyncMock()
    mock_get.status_code = 404
    mocker.patch('httpx.AsyncClient.get', return_value=mock_get)
    
    # Mock POST per DDG
    mock_post = mocker.AsyncMock()
    mock_post.status_code = 200
    mock_post.text = '<html><body><td class="result-snippet">DDG Result</td></body></html>'
    mocker.patch('httpx.AsyncClient.post', return_value=mock_post)
    
    results = await gather_profile_metadata(["https://example.com/test"], enable_ddg=True, real_name="Sconosciuto")
    assert any(r["source"] == "DuckDuckGo" and "DDG Result" in r["bio"] for r in results)
