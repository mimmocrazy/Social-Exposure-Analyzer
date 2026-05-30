import pytest
import os
from backend.services.ocr import extract_text_from_image
from backend.services.risk_engine import calculate_risk
from backend.models.risk import RiskReport

def test_extract_text_from_image_success(mocker, tmp_path):
    # Setup file temporaneo
    fake_img = tmp_path / "test.jpg"
    fake_img.write_text("dummy")
    
    # Mock EasyOCR reader per evitare caricamento pesi/GPU
    mock_reader = mocker.MagicMock()
    mock_reader.readtext.return_value = ["Testo", "Estratto", "Sicuro"]
    mocker.patch('backend.services.ocr.get_reader', return_value=mock_reader)
    
    result = extract_text_from_image(str(fake_img))
    
    assert result == "Testo Estratto Sicuro"
    # Sicurezza: verifica cancellazione file
    assert not fake_img.exists()

def test_extract_text_from_image_error(mocker, tmp_path):
    fake_img = tmp_path / "corrupted.jpg"
    fake_img.write_text("dummy")
    
    mock_reader = mocker.MagicMock()
    mock_reader.readtext.side_effect = Exception("Immagine corrotta o tentativo evasione")
    mocker.patch('backend.services.ocr.get_reader', return_value=mock_reader)
    
    result = extract_text_from_image(str(fake_img))
    
    assert result == ""
    assert not fake_img.exists()

@pytest.mark.asyncio
async def test_calculate_risk_success(mocker):
    mock_generate = mocker.MagicMock()
    mock_generate.text = '{"score": 85, "level": "HIGH", "threat_vectors": ["Phishing"], "mitigation_advice": "Advice", "insufficient_data": false}'
    
    mock_client_instance = mocker.MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_generate
    
    mocker.patch('backend.services.risk_engine.get_client', return_value=mock_client_instance)
    
    pii_data = [{"label": "EMAIL", "value": "test@test.com"}]
    report = await calculate_risk(pii_data)
    
    assert report.score == 85
    assert report.level == "HIGH"
    assert not report.insufficient_data
    
@pytest.mark.asyncio
async def test_calculate_risk_fallback(mocker):
    mock_client_instance = mocker.MagicMock()
    mock_client_instance.models.generate_content.side_effect = Exception("API Quota Exceeded")
    
    mocker.patch('backend.services.risk_engine.get_client', return_value=mock_client_instance)
    
    report = await calculate_risk([])
    
    assert report.score == 0
    assert report.insufficient_data == True
    assert report.level == "LOW"
