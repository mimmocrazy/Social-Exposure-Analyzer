import subprocess
import re
from abc import ABC, abstractmethod
from typing import List
from backend.core.logger import logger

class BaseDiscovery(ABC):
    """Interfaccia astratta per le strategie di Discovery dei profili OSINT."""
    
    @abstractmethod
    def discover_profiles(self, username: str) -> List[str]:
        pass

class SherlockAdapter(BaseDiscovery):
    """Adapter per l'esecuzione di Sherlock tramite subprocess."""
    
    def discover_profiles(self, username: str) -> List[str]:
        logger.info(f"Avvio Discovery tramite Sherlock per username: {username}")
        
        # Sanitizzazione input per prevenire eventuali command/argument injection
        if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            logger.error(f"Tentativo di injection rilevato o username malformato: {username}")
            raise ValueError("Username invalido: contiene caratteri non consentiti.")
            
        # Limitiamo ai social più critici per il Social Engineering Risk Assessment
        target_sites = ["facebook", "instagram", "twitter", "linkedin"]
        
        command = [
            "sherlock", username,
            "--site", *target_sites,
            "--print-found"
        ]
        
        valid_urls = []
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Effettua il parsing dell'output standard di Sherlock per estrarre gli URL
            for line in result.stdout.splitlines():
                if line.startswith("[+]"):
                    parts = line.split(": ", 1)
                    if len(parts) > 1:
                        valid_urls.append(parts[1].strip())
                        
        except FileNotFoundError:
            logger.warning("Sherlock non è installato o non è nel PATH. Uso fallback.")
        except Exception as e:
            logger.exception(f"Errore inaspettato durante l'esecuzione di Sherlock: {e}")
            
        # Fallback se Sherlock non trova nulla o non è installato
        if not valid_urls:
            logger.info("Nessun URL trovato tramite Sherlock. Applica fallback a Instagram.")
            valid_urls.append(f"https://instagram.com/{username}")
            
        return valid_urls
