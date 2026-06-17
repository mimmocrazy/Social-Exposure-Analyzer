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
    mock_generate.text = '{"score": 0, "score_breakdown": [], "sub_scores": {"identity_exposure": 0, "network_exposure": 0, "routine_exposure": 0}, "level": "HIGH", "threat_vectors": ["Phishing"], "mitigation_advice": "Advice", "mitigation_sections": [{"title": "Phishing Section", "threat_vector": "Phishing", "exposed_data": "test@test.com", "criticality": "ALTA", "mitigation": "Enable 2FA"}], "insufficient_data": false, "pii_extracted": [{"label": "EMAIL", "value": "test@test.com", "confidence_score": 0.9, "source": "DuckDuckGo"}]}'
    
    mock_client_instance = mocker.MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_generate
    
    mocker.patch('backend.services.risk_engine.get_client', return_value=mock_client_instance)
    mocker.patch('dotenv.dotenv_values', return_value={"AI_PROVIDER": "gemini"})
    
    pii_data = [{"label": "EMAIL", "value": "test@test.com"}]
    report = await calculate_risk(pii_data)
    
    assert report.score == 25  # CRITICA = 25 punti deterministici
    assert report.level.value == "MEDIUM"
    assert not report.insufficient_data
    
@pytest.mark.asyncio
async def test_calculate_risk_fallback(mocker):
    mock_client_instance = mocker.MagicMock()
    mock_client_instance.models.generate_content.side_effect = Exception("API Quota Exceeded")
    
    mocker.patch('backend.services.risk_engine.get_client', return_value=mock_client_instance)
    mocker.patch('dotenv.dotenv_values', return_value={"AI_PROVIDER": "gemini"})
    mocker.patch('openai.OpenAI', side_effect=Exception("GitHub fallito"))
    mocker.patch('groq.Groq', side_effect=Exception("Groq fallito"))
    
    with pytest.raises(RuntimeError) as exc_info:
        await calculate_risk([])
    
    assert "Errore critico Gemini API / NLP:" in str(exc_info.value)

@pytest.mark.skip(reason="Architettura multi-provider sostituita con circuit breaker esterno (GitHub/Groq)")
@pytest.mark.asyncio
async def test_model_temporary_disabling(mocker):
    from backend.services.risk_engine import _disabled_models
    import backend.services.risk_engine as risk_engine
    # Svuota i modelli disabilitati prima del test
    _disabled_models.clear()
    risk_engine._gemini_is_down = False
    
    mock_client_instance = mocker.MagicMock()
    # Primo modello fallisce con eccezione, secondo modello ha successo
    mock_generate = mocker.MagicMock()
    mock_generate.text = '{"score": 0, "score_breakdown": [], "sub_scores": {"identity_exposure": 0, "network_exposure": 0, "routine_exposure": 0}, "level": "LOW", "threat_vectors": [], "mitigation_advice": "Advice", "mitigation_sections": [{"title": "Minor Issue", "threat_vector": "N/A", "exposed_data": "N/A", "criticality": "BASSA", "mitigation": "N/A"}], "insufficient_data": false, "pii_extracted": []}'
    
    mock_client_instance.models.generate_content.side_effect = [
        Exception("429 Resource Exhausted"),
        mock_generate
    ]
    
    mocker.patch('backend.services.risk_engine.get_client', return_value=mock_client_instance)
    mocker.patch('dotenv.dotenv_values', return_value={"AI_PROVIDER": "gemini"})
    
    # Esegue la chiamata: il primo modello ('gemini-flash-latest') dovrebbe fallire ed essere disabilitato,
    # poi il secondo ('gemini-2.5-flash') dovrebbe avere successo.
    await calculate_risk("test payload")
    
    # Verifica che 'gemini-flash-latest' sia ora disabilitato
    assert not _is_model_available('gemini-flash-latest')
    assert _is_model_available('gemini-2.5-flash')
