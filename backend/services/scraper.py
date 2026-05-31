import httpx
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from backend.core.logger import logger

async def gather_profile_metadata(
    urls: List[str], 
    real_name: str = None, 
    enable_ddg: bool = True,
    ig_sessionid: str = None
) -> List[Dict[str, Any]]:
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

    target_to_search = urls[0].split('/')[-1] if urls else "unknown"

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        # 1. Instagram Deep Scan (Se sessionid fornito)
        if ig_sessionid and target_to_search and target_to_search != "unknown":
            try:
                logger.info(f"Avvio Instagram Deep Scan per {target_to_search} tramite sessionid.")
                ig_headers = headers.copy()
                ig_headers["Cookie"] = f"sessionid={ig_sessionid}"
                ig_headers["X-IG-App-ID"] = "936619743392459"
                ig_api_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={target_to_search}"
                
                ig_resp = await client.get(ig_api_url, headers=ig_headers, follow_redirects=True)
                if ig_resp.status_code == 200:
                    ig_data = ig_resp.json()
                    user_data = ig_data.get("data", {}).get("user", {})
                    if user_data:
                        deep_bio = f"Full Name: {user_data.get('full_name')} | Followers: {user_data.get('edge_followed_by', {}).get('count')} | Bio: {user_data.get('biography')} | Business Email: {user_data.get('business_email')} | Business Phone: {user_data.get('business_phone_number')} | Profile Pic: {user_data.get('profile_pic_url_hd')}"
                        
                        # Estrazione Luoghi e Testi dagli ultimi post
                        timeline = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
                        recent_locations = []
                        recent_captions = []
                        
                        for edge in timeline[:12]: # Analizza gli ultimi 12 post
                            node = edge.get("node", {})
                            
                            # Estrai Luogo (Location tag)
                            loc = node.get("location")
                            if loc and loc.get("name"):
                                recent_locations.append(loc.get("name"))
                                
                            # Estrai Testo/Caption
                            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                            if caption_edges:
                                text = caption_edges[0].get("node", {}).get("text")
                                if text:
                                    recent_captions.append(text.replace("\n", " ")[:100])
                        
                        if recent_locations:
                            deep_bio += f" | Post Locations (Luoghi Frequenti): {', '.join(set(recent_locations))}"
                        if recent_captions:
                            deep_bio += f" | Recent Post Captions: {' || '.join(recent_captions)}"
                            
                        results.append({
                            "source": "Instagram Deep Scan API",
                            "url": f"API: {target_to_search}",
                            "status": "ACCESSIBLE",
                            "bio": deep_bio,
                            "error": None
                        })
                        logger.info("Instagram Deep Scan riuscito con successo.")
                else:
                    logger.warning(f"Instagram Deep Scan fallito con status {ig_resp.status_code}")
            except Exception as e:
                logger.warning(f"Errore in Instagram Deep Scan: {e}")

        # 2. Standard Web Scraping
        # Se l'utente ha fornito un sessionid, lo scraping anonimo su Instagram è sempre inutile
        # (colpisce il login wall anche se il Deep Scan ha fallito per rate-limit 429)
        ig_deep_scan_attempted = bool(ig_sessionid and target_to_search and target_to_search != "unknown")
        has_deep_scan = any(r["source"] == "Instagram Deep Scan API" for r in results)
        for url in urls:
            parsed = urllib.parse.urlparse(url)
            is_instagram = "instagram.com" in (parsed.hostname or "")
            if is_instagram and (has_deep_scan or ig_deep_scan_attempted):
                logger.info(f"Skipping standard scraping per {url} (Deep Scan {'riuscito' if has_deep_scan else 'tentato ma fallito'}).")
                continue

            profile_data = {
                "source": "Web Scraping",
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
                
                if response.status_code >= 400:
                    profile_data["status"] = "PROTECTED"
                    profile_data["error"] = f"HTTP Error {response.status_code}"
                    logger.warning(f"Accesso protetto o negato per {url} (HTTP {response.status_code})")
                else:
                    profile_data["status"] = "ACCESSIBLE"
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    if soup.title:
                        profile_data["title"] = soup.title.string.strip()
                        
                    meta_desc = soup.find("meta", attrs={"name": "description"}) or \
                                soup.find("meta", attrs={"property": "og:description"})
                    
                    if meta_desc:
                        profile_data["bio"] = meta_desc.get("content", "").strip()
                        
                    title_lower = profile_data["title"].lower() if profile_data["title"] else ""
                    is_login_wall = "login" in title_lower or "sign in" in title_lower or "accedi" in title_lower
                    
                    if is_login_wall or not profile_data["bio"]:
                        logger.warning(f"Rilevato Login Wall o mancanza di dati per {url}. Iniezione warning anti-allucinazione.")
                        profile_data["bio"] = (profile_data["bio"] or "") + "\n[WARNING: PROFILO PRIVATO O INACCESSIBILE. NON INVENTARE DATI.]"
                        
            except httpx.RequestError as e:
                logger.error(f"Errore di connettività durante lo scraping di {url}: {e}")
                profile_data["status"] = "PROTECTED"
                profile_data["error"] = "Network/Timeout Error"
                
            results.append(profile_data)
            
        # 3. OSINT Aggressivo: Ricerca DuckDuckGo (se abilitato)
        if enable_ddg:
            try:
                if target_to_search and target_to_search != "unknown":
                    # Cerca RIGOROSAMENTE l'username per evitare omonimie e falsi positivi
                    search_queries = [target_to_search]
                        
                    for q in search_queries:
                        ddg_url = f"https://lite.duckduckgo.com/lite/"
                        logger.info(f"Avvio OSINT profondo su DuckDuckGo per: {q}")
                        resp = await client.post(ddg_url, data={"q": q}, follow_redirects=True)
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "html.parser")
                            snippets = soup.find_all("td", class_="result-snippet")
                            ddg_text = " ".join([s.get_text(strip=True) for s in snippets])
                            if ddg_text:
                                results.append({
                                    "source": "DuckDuckGo",
                                    "url": f"Search: {q}",
                                    "status": "ACCESSIBLE",
                                    "bio": ddg_text,
                                    "error": None
                                })
            except Exception as e:
                logger.warning(f"OSINT DuckDuckGo fallito: {e}")
            
    return results
