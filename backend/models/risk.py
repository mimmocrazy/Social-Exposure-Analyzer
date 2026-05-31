from pydantic import BaseModel, Field
from typing import List
from backend.models import RiskLevel

class Entity(BaseModel):
    label: str = Field(description="Il tipo di PII (es. EMAIL, PERSON, LOCATION, ORGANIZATION)")
    value: str = Field(description="Il valore esatto estratto dal testo")
    confidence_score: float = Field(description="Un punteggio da 0.0 a 1.0 basato sulla tua certezza dell'estrazione")

class MitigationSection(BaseModel):
    title: str = Field(description="Titolo sintetico della macrosezione (es. Esposizione Anagrafica, Informazioni di Contatto, Canali Social, Relazioni Personali, ecc.)")
    exposed_data: str = Field(description="Citazione precisa del dato o dei dati esposti collegati a questa sezione")
    criticality: str = Field(description="Livello di criticità della macrosezione (es. CRITICA, ALTA, MEDIA, BASSA)")
    mitigation: str = Field(description="Mitigazione specifica, consigli e azioni concrete da intraprendere")

class ScoreBreakdown(BaseModel):
    reason: str = Field(description="Motivazione dettagliata (es. 'Trovate 3 email su DuckDuckGo e account registrati su Holehe')")
    points_added: int = Field(description="Punti assegnati per questa specifica motivazione (da 1 a 100)")

class RiskSubScores(BaseModel):
    identity_exposure: int = Field(ge=0, le=100, description="Punteggio di rischio legato a dati anagrafici e contatti diretti (es. email, telefono, nome completo).")
    network_exposure: int = Field(ge=0, le=100, description="Punteggio di rischio legato a legami familiari, amicizie, colleghi e interazioni sociali.")
    routine_exposure: int = Field(ge=0, le=100, description="Punteggio di rischio legato a luoghi frequentati, orari, check-in e abitudini di vita.")

class RiskReport(BaseModel):
    score: int = Field(ge=0, le=100, description="Risk score globale from 0 to 100")
    score_breakdown: List[ScoreBreakdown] = Field(description="Ripartizione matematica trasparente dei punti assegnati")
    sub_scores: RiskSubScores = Field(description="Sub-punteggi dettagliati che compongono il rischio globale")
    level: RiskLevel = Field(description="Risk level classification")
    threat_vectors: List[str] = Field(description="List of identified social engineering threat vectors")
    mitigation_advice: str = Field(description="Actionable advice to mitigate the risks")
    mitigation_sections: List[MitigationSection] = Field(description="Lista dettagliata divisa per macrosezioni con consiglio, citazione del dato esposto, criticità e mitigazioni", default_factory=list)
    insufficient_data: bool = Field(description="True if the provided PII is insufficient to determine a meaningful risk score")
    pii_extracted: List[Entity] = Field(description="Lista delle PII (Dati Sensibili) estratti dal testo raw. Se non trovi nulla, restituisci lista vuota.", default_factory=list)
