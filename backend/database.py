import os
from sqlmodel import SQLModel, create_engine, Session

# Recupera l'URL dal sistema (usato in produzione su Azure)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Produzione: PostgreSQL
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # Dev locale: SQLite fallback
    sqlite_file_name = "data/social_exposure_analyzer.db"
    sqlite_url = f"sqlite:///./{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    # Crea la directory data se non esiste
    import os
    os.makedirs("data", exist_ok=True)
    
    # Importa i modelli affinché SQLModel li registri
    from backend.models import ProfileAnalysis
    from backend.models.user import User
    
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
