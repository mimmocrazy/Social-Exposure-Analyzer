import pytest
import subprocess
from backend.services.discovery import SherlockAdapter

def test_discover_profiles_injection():
    adapter = SherlockAdapter()
    with pytest.raises(ValueError, match="Username invalido"):
        adapter.discover_profiles("invalid; injection")

def test_discover_profiles_success(mocker):
    adapter = SherlockAdapter()
    
    mock_result = mocker.MagicMock()
    mock_result.stdout = "[+] Facebook: https://facebook.com/test\n[+] Instagram: https://instagram.com/test\n[-] Twitter: Not Found"
    mocker.patch('subprocess.run', return_value=mock_result)
    
    urls = adapter.discover_profiles("test")
    assert len(urls) == 2
    assert "https://facebook.com/test" in urls
    assert "https://instagram.com/test" in urls

def test_discover_profiles_fallback_empty(mocker):
    adapter = SherlockAdapter()
    
    mock_result = mocker.MagicMock()
    mock_result.stdout = "[-] Facebook: Not Found"
    mocker.patch('subprocess.run', return_value=mock_result)
    
    urls = adapter.discover_profiles("test")
    assert len(urls) == 1
    assert urls[0] == "https://instagram.com/test"

def test_discover_profiles_filenotfound(mocker):
    adapter = SherlockAdapter()
    
    mocker.patch('subprocess.run', side_effect=FileNotFoundError("Sherlock non trovato"))
    
    urls = adapter.discover_profiles("test")
    assert len(urls) == 1
    assert urls[0] == "https://instagram.com/test"

def test_discover_profiles_exception(mocker):
    adapter = SherlockAdapter()
    
    mocker.patch('subprocess.run', side_effect=Exception("Generic error"))
    
    urls = adapter.discover_profiles("test")
    assert len(urls) == 1
    assert urls[0] == "https://instagram.com/test"
