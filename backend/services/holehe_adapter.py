import asyncio
import re
from typing import List
from backend.core.logger import logger

async def run_holehe(email: str) -> List[str]:
    """
    Esegue Holehe in un subprocess isolato per non bloccare l'event loop di FastAPI,
    e parsa l'output per trovare i siti su cui l'email è registrata.
    Restituisce una lista di nomi a dominio (es. ['twitter.com', 'instagram.com']).
    """
    logger.info(f"Avvio ricerca OSINT Holehe per l'email: {email}")
    import sys
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "holehe", email, "--only-used", "--no-color", "--no-clear",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0 and stderr:
            logger.warning(f"Holehe ha restituito un errore: {stderr.decode(errors='ignore')}")
            
        output = stdout.decode(errors='ignore')
        
        registered_sites = []
        # Cerchiamo tutte le righe che iniziano con [+]
        for line in output.split('\n'):
            line = line.strip()
            # Ignora la legenda
            if line.startswith("[+] Email used"):
                continue
                
            if line.startswith("[+] "):
                site = line[4:].strip()
                if site:
                    registered_sites.append(site)
                    
        logger.info(f"Holehe completato per {email}. Siti trovati: {len(registered_sites)}")
        return registered_sites
        
    except Exception as e:
        logger.error(f"Fallimento esecuzione Holehe per {email}: {e}")
        return []
