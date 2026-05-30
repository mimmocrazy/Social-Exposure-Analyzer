import logging
import sys
from loguru import logger
import re

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Ottieni il livello loguru corrispondente
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Trova il chiamante originale da cui la richiesta di log ha avuto origine
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def mask_pii(record):
    """Filtro di sicurezza per offuscare PII elementari dai log (Email/Telefoni)."""
    msg = str(record["message"])
    msg = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL-MASKED]', msg)
    msg = re.sub(r'\+?\d{2,3}[\s-]?\d{3}[\s-]?\d{4,5}', '[PHONE-MASKED]', msg)
    record["message"] = msg
    return True

def setup_logging():
    # Rimuovi i logger standard di loguru
    logger.remove()
    
    # Aggiungi stdout per Azure App Service con PII Masking
    logger.add(
        sys.stdout, 
        filter=mask_pii,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Intercetta i log di Uvicorn e FastAPI
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False
