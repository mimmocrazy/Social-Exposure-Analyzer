from backend.services.nlp import Entity, filter_and_deduplicate_entities

def test_nlp_filtering_threshold():
    """Verifica che le entità sotto soglia (0.85) vengano scartate."""
    raw = [
        Entity(label="PER", value="Mario Rossi", confidence_score=0.90),
        Entity(label="LOC", value="Roma", confidence_score=0.84),
        Entity(label="ORG", value="Acme Corp", confidence_score=0.95),
    ]
    
    result = filter_and_deduplicate_entities(raw)
    
    # "Roma" (0.84) deve essere scartata
    assert len(result) == 2
    assert not any(e.value == "Roma" for e in result)

def test_nlp_deduplication():
    """Verifica che venga mantenuta l'entità con score maggiore in caso di duplicati."""
    raw = [
        Entity(label="PER", value="Mario Rossi", confidence_score=0.88),
        Entity(label="PER", value="mario rossi", confidence_score=0.95),
        Entity(label="PER", value="MARIO ROSSI", confidence_score=0.92),
    ]
    
    result = filter_and_deduplicate_entities(raw)
    
    # Deve essercene solo 1
    assert len(result) == 1
    
    # E deve avere lo score massimo
    assert result[0].confidence_score == 0.95
