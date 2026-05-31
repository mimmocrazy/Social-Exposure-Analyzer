from pydantic import BaseModel, Field
from typing import Optional

class AnalyzeRequest(BaseModel):
    # Autonomus Optimization: Sostituito HttpUrl con str (max_length 2000) 
    # per supportare sia URL pieni che username standard (es. in Sherlock).
    target_url: str = Field(..., max_length=2000)
    enable_ddg: bool = Field(default=True)
    enable_holehe: bool = Field(default=True)
    ig_sessionid: Optional[str] = Field(default=None)
    enable_fb_scan: bool = Field(default=False)
    fb_sessionid: Optional[str] = Field(default=None)
