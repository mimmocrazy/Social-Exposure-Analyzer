import os
from dotenv import load_dotenv
load_dotenv() # Carica subito le variabili d'ambiente da .env

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import subprocess

from backend.api.routers import analyze, auth
from backend.core.logger import setup_logging, logger
from backend.api.exceptions import global_exception_handler

def run_security_check():
    """Esegue un rapido check di sicurezza in background (solo dev)."""
    if os.environ.get("ENVIRONMENT", "development") != "production":
        try:
            logger.info("Inizializzazione check di sicurezza (Safety)...")
            subprocess.Popen(["safety", "check"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

from backend.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eseguito allo startup dell'app
    setup_logging()
    logger.info("Avvio di Social Exposure Analyzer...")
    create_db_and_tables()
    logger.info("Database SQLite e tabelle inizializzati per il dev locale.")
    run_security_check()
    yield
    # Eseguito allo shutdown dell'app

app = FastAPI(
    title="Social Engineering Risk Assessment API",
    description="API per l'analisi dell'esposizione pubblica di dati personali e social engineering risk.",
    version="1.0.0",
    lifespan=lifespan
)

# Registrazione exception handler globale
app.add_exception_handler(Exception, global_exception_handler)

# SECURITY-FIRST MIDDLEWARE: Prevenzione base per header e misconfiguration
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Inietta HTTP security headers standard a ogni risposta.
    Costituisce il layer base del Security-First development flow.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """
    Autonomus Optimization: Middleware globale anti-DoS per prevenire
    l'ingestion di payload massivi direttamente all'ingresso dell'API.
    Se la richiesta supera i 10.000 byte, viene rigettata con 413.
    """
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > 10000:
            return JSONResponse(
                status_code=413, 
                content={"detail": "Payload Too Large. Max size is 10000 bytes."}
            )
    return await call_next(request)

# Configurazione CORS per sviluppo (da restrittivizzare in produzione Azure)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusione dei Router Inclusions
app.include_router(auth.router, prefix="/api/v1")
app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])
