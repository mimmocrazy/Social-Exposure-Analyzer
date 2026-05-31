import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

from backend.main import app
from backend.database import get_session
import backend.models # Necessario affinché SQLModel registri le tabelle prima di create_all

from sqlalchemy.pool import StaticPool

# Database SQLite in-memory isolato per i test
sqlite_url = "sqlite:///:memory:"
engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Applica l'engine in-memory globalmente così i BackgroundTasks che importano `engine` da backend.database usano quello di test
import backend.database
backend.database.engine = engine

@pytest.fixture(name="session")
def session_fixture():
    """
    Crea un database SQLite in-memory, genera le tabelle per la durata 
    del test e fornisce una Sessione al chiamante.
    Alla fine del test, le tabelle vengono scartate per mantenere isolamento.
    
    Yields:
        Session: Sessione attiva di SQLModel connessa al DB in-memory.
    """
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Fornisce un TestClient di FastAPI configurato per utilizzare il 
    database di test. Esegue l'override della dependency `get_session` 
    e `get_current_user` dell'applicazione principale.
    """
    from backend.models.user import User
    from backend.core.security import get_password_hash
    from backend.api.routers.auth import get_current_user
    
    mock_user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password")
    )
    session.add(mock_user)
    session.commit()
    session.refresh(mock_user)
    
    def get_session_override():
        return session
        
    def get_current_user_override():
        return mock_user
    
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
