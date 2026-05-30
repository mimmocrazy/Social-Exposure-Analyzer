from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    # Autonomus Optimization: Sostituito HttpUrl con str (max_length 2000) 
    # per supportare sia URL pieni che username standard (es. in Sherlock).
    target_url: str = Field(..., max_length=2000)
