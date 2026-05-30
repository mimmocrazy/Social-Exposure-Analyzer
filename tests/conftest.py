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
    dell'applicazione principale in modo che le API usino la fixture della sessione.
    
    Args:
        session (Session): La sessione del database di test iniettata.
        
    Yields:
        TestClient: Istanza client pronta per effettuare richieste HTTP ai router.
    """
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
