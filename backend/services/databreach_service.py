import httpx
import asyncio
from backend.core.logger import logger

async def check_data_breaches(email: str) -> list:
    """
    Controlla se l'email è stata esposta in data breach noti utilizzando
    l'API pubblica e gratuita XposedOrNot.
    Restituisce una lista di stringhe (i nomi dei databreach).
    """
    breaches = []
    url = f"https://api.xposedornot.com/v1/check-email/{email}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if "breaches" in data and len(data["breaches"]) > 0:
                    # L'API di solito restituisce list di list di stringhe
                    first_list = data["breaches"][0]
                    breaches.extend(first_list)
                    logger.warning(f"[DATABREACH OSINT] Trovati {len(first_list)} breach per {email}")
            elif resp.status_code == 404:
                # 404 significa nessuna violazione trovata
                logger.info(f"[DATABREACH OSINT] Nessuna violazione trovata per {email}")
            else:
                logger.warning(f"[DATABREACH OSINT] API ha restituito status {resp.status_code} per {email}")
    except Exception as e:
        logger.error(f"[DATABREACH OSINT] Errore durante la richiesta a XposedOrNot: {e}")
        
    return breaches
