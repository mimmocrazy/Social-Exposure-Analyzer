import pytest
import logging
from backend.core.logger import mask_pii, custom_format, InterceptHandler

def test_mask_pii():
    # Test email masking
    record = {"message": "Found email: user@example.com in the leak"}
    mask_pii(record)
    assert record["message"] == "Found email: [EMAIL-MASKED] in the leak"
    
    # Test phone masking
    record = {"message": "Found phone: +39 333 123 4567 in the leak"}
    mask_pii(record)
    assert "[PHONE-MASKED]" in record["message"]
    
    # Test safe message
    record = {"message": "Found username testuser"}
    mask_pii(record)
    assert record["message"] == "Found username testuser"

def test_custom_format():
    # Test discovery tag
    record = {"name": "backend.services.discovery", "message": "Avvio...", "function": "test"}
    fmt = custom_format(record)
    assert "[SHERLOCK OSINT]" in fmt
    
    # Test Instagram Scraper tag
    record = {"name": "backend.services.scraper", "message": "Instagram lookup", "function": "test"}
    fmt = custom_format(record)
    assert "[INSTAGRAM API]" in fmt
    
    # Test DuckDuckGo Scraper tag
    record = {"name": "backend.services.scraper", "message": "DuckDuckGo search", "function": "test"}
    fmt = custom_format(record)
    assert "[DUCKDUCKGO OSINT]" in fmt
    
    # Test Generic Scraper tag
    record = {"name": "backend.services.scraper", "message": "Generic site", "function": "test"}
    fmt = custom_format(record)
    assert "[OSINT SCRAPER]" in fmt
    
    # Test Risk Engine
    record = {"name": "backend.services.risk_engine", "message": "Calc", "function": "test"}
    fmt = custom_format(record)
    assert "[RISK ENGINE AI]" in fmt
    
    # Test Identity
    record = {"name": "backend.api.routers.analyze", "message": "Calc", "function": "guess_real_name"}
    fmt = custom_format(record)
    assert "[LLM IDENTITY]" in fmt
    
    # Test Orchestrator
    record = {"name": "backend.api.routers.analyze", "message": "Calc", "function": "run"}
    fmt = custom_format(record)
    assert "[ORCHESTRATOR]" in fmt
    
    # Test Fallback
    record = {"name": "my_module.test", "message": "Msg", "function": "test"}
    fmt = custom_format(record)
    assert "[test]" in fmt

def test_intercept_handler():
    handler = InterceptHandler()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py", lineno=1,
        msg="Test message", args=(), exc_info=None
    )
    # Esegue emit (chiamerà logger di loguru sotto il cofano, quindi testiamo che non crashi)
    handler.emit(record)
