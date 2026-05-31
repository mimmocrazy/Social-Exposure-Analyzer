import uuid
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str

    # Un utente ha molte analisi (Risolve l'importazione ritardata per evitare import circolari)
    analyses: List["ProfileAnalysis"] = Relationship(back_populates="user")
