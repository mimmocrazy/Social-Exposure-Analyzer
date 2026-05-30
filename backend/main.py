from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import create_db_and_tables
from backend.api.routers import analyze

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eseguito allo startup dell'app
    create_db_and_tables()
    yield
    # Eseguito allo shutdown dell'app

app = FastAPI(
    title="Social Engineering Risk Assessment API",
    description="API per l'analisi dell'esposizione pubblica di dati personali e social engineering risk.",
    version="1.0.0",
    lifespan=lifespan
)

# Configurazione CORS per sviluppo (da restrittivizzare in produzione Azure)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusione dei router
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
