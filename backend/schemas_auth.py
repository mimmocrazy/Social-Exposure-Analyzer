from typing import Optional
from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str

import uuid

class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
