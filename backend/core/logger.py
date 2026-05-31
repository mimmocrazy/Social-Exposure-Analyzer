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

def custom_format(record):
    """Genera un template di log dinamico, colorato e altamente semantico per i componenti."""
    name = record["name"]
    msg = record["message"]
    
    # Rilevamento intelligente del modulo per taggatura semantica e cromaticità neon
    if "discovery" in name or "Sherlock" in msg:
        tag = "<cyan><b>[SHERLOCK OSINT]</b></cyan>"
    elif "scraper" in name:
        if "Instagram" in msg or "ig_sessionid" in msg:
            tag = "<magenta><b>[INSTAGRAM API]</b></magenta>"
        elif "DuckDuckGo" in msg or "OSINT profondo su DuckDuckGo" in msg:
            tag = "<yellow><b>[DUCKDUCKGO OSINT]</b></yellow>"
        else:
            tag = "<blue><b>[OSINT SCRAPER]</b></blue>"
    elif "holehe" in name:
        tag = "<blue><b>[HOLEHE OSINT]</b></blue>"
    elif "risk_engine" in name:
        tag = "<green><b>[RISK ENGINE AI]</b></green>"
    elif "analyze" in name:
        if "guess_real_name" in record["function"] or "deduzione" in msg:
            tag = "<green><b>[LLM IDENTITY]</b></green>"
        else:
            tag = "<light-blue><b>[ORCHESTRATOR]</b></light-blue>"
    elif name == "uvicorn.access":
        tag = "<light-magenta><b>[HTTP ACCESS]</b></light-magenta>"
    elif "uvicorn" in name:
        tag = "<magenta><b>[SERVER]</b></magenta>"
    else:
        # Fallback pulito e compatto per moduli esterni
        short_name = name.split(".")[-1]
        tag = f"<light-black>[{short_name}]</light-black>"

    return f"<light-black>{{time:YYYY-MM-DD HH:mm:ss}}</light-black> | <level>{{level: <7}}</level> | {tag} - <level>{{message}}</level>{{exception}}\n"

def setup_logging():
    # Rimuovi i logger standard di loguru
    logger.remove()
    
    # Aggiungi stdout per Azure App Service con PII Masking e formattatore personalizzato
    logger.add(
        sys.stdout, 
        filter=mask_pii,
        format=custom_format
    )

    # Intercetta i log di Uvicorn e FastAPI
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False
