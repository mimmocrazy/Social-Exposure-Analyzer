import httpx
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from backend.core.logger import logger

async def gather_profile_metadata(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Estrae metadati di base dagli URL forniti (approccio Search Dorking).
    Implementa un meccanismo di fallback sicuro nel caso in cui il profilo
    risulti bloccato, inesistente o privato.
    """
    results = []
    
    # Header di base per mitigare controlli anti-bot rudimentali
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, come Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        for url in urls:
            profile_data = {
                "url": url,
                "status": "UNKNOWN",
                "title": None,
                "bio": None,
                "error": None
            }
            
            # Prevenzione SSRF (Server-Side Request Forgery)
            parsed = urllib.parse.urlparse(url)
            if parsed.hostname in ["localhost", "127.0.0.1", "0.0.0.0"] or \
               str(parsed.hostname).startswith("192.168.") or \
               str(parsed.hostname).startswith("10."):
                logger.warning(f"Violazione Security: Tentativo SSRF verso {url}")
                profile_data["status"] = "PROTECTED"
                profile_data["error"] = "SSRF Policy Violation"
                results.append(profile_data)
                continue
            
            try:
                logger.info(f"Avvio estrazione metadati (Scraping) da: {url}")
                response = await client.get(url, follow_redirects=True)
                
                # Logica di fallback: blocchi cloudflare, profili privati, etc.
                if response.status_code >= 400:
                    profile_data["status"] = "PROTECTED"
                    profile_data["error"] = f"HTTP Error {response.status_code}"
                    logger.warning(f"Accesso protetto o negato per {url} (HTTP {response.status_code})")
                else:
                    profile_data["status"] = "ACCESSIBLE"
                    
                    # Parsing per l'estrazione di metadati
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    if soup.title:
                        profile_data["title"] = soup.title.string.strip()
                        
                    # Ricerca bio su opengraph o meta description classici
                    meta_desc = soup.find("meta", attrs={"name": "description"}) or \
                                soup.find("meta", attrs={"property": "og:description"})
                    
                    if meta_desc:
                        profile_data["bio"] = meta_desc.get("content", "").strip()
                        
            except httpx.RequestError as e:
                logger.error(f"Errore di connettività durante lo scraping di {url}: {e}")
                profile_data["status"] = "PROTECTED"
                profile_data["error"] = "Network/Timeout Error"
                
            results.append(profile_data)
            
    return results
