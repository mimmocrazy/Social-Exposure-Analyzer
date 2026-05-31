import os
from sqlmodel import SQLModel, create_engine, Session

# Recupera l'URL dal sistema (usato in produzione su Azure)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Produzione: PostgreSQL
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # Dev locale: SQLite fallback
    sqlite_file_name = "social_exposure_analyzer.db"
    sqlite_url = f"sqlite:///./{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session
