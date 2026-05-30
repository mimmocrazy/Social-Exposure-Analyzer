from pydantic import BaseModel, HttpUrl

class AnalyzeRequest(BaseModel):
    target_url: HttpUrl
