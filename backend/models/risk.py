from pydantic import BaseModel, Field
from typing import List
from backend.models import RiskLevel

class Entity(BaseModel):
    label: str = Field(description="Il tipo di PII (es. EMAIL, PERSON, LOCATION, ORGANIZATION)")
    value: str = Field(description="Il valore esatto estratto dal testo")
    confidence_score: float = Field(description="Un punteggio da 0.0 a 1.0 basato sulla tua certezza dell'estrazione")

class RiskReport(BaseModel):
    score: int = Field(ge=0, le=100, description="Risk score from 0 to 100")
    level: RiskLevel = Field(description="Risk level classification")
    threat_vectors: List[str] = Field(description="List of identified social engineering threat vectors")
    mitigation_advice: str = Field(description="Actionable advice to mitigate the risks")
    insufficient_data: bool = Field(description="True if the provided PII is insufficient to determine a meaningful risk score")
    pii_extracted: List[Entity] = Field(description="Lista delle PII (Dati Sensibili) estratti dal testo raw. Se non trovi nulla, restituisci lista vuota.", default_factory=list)
