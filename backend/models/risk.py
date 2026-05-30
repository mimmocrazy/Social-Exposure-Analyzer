from pydantic import BaseModel, Field
from typing import List
from backend.models import RiskLevel

class RiskReport(BaseModel):
    score: int = Field(ge=0, le=100, description="Risk score from 0 to 100")
    level: RiskLevel = Field(description="Risk level classification")
    threat_vectors: List[str] = Field(description="List of identified social engineering threat vectors")
    mitigation_advice: str = Field(description="Actionable advice to mitigate the risks")
    insufficient_data: bool = Field(description="True if the provided PII is insufficient to determine a meaningful risk score")
