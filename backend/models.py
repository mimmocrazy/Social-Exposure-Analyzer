import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column, JSON, String, Text

class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RiskLevel(str, Enum):
    Basso = "Basso"
    Medio = "Medio"
    Alto = "Alto"

class ProfileAnalysis(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    target_url: str = Field(index=True)
    platform: Optional[str] = Field(default=None)
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING)
    scan_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_data_dump: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    pii_extracted: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    has_images_analyzed: bool = Field(default=False)
    risk_score: Optional[int] = Field(default=None, ge=0, le=100)
    risk_level: Optional[RiskLevel] = Field(default=None)
    llm_report: Optional[str] = Field(default=None, sa_column=Column(Text))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
