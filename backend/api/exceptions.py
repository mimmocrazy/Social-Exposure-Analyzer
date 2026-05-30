from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

async def global_exception_handler(request: Request, exc: Exception):
    # Logga l'errore completo (stacktrace) internamente per il debug
    logger.exception(f"Errore non gestito durante la richiesta {request.method} {request.url}")
    
    # Restituisci al client una risposta standard senza stacktrace per sicurezza
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"}
    )
