import httpx
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from backend.core.logger import logger

async def gather_profile_metadata(
    urls: List[str], 
    real_name: str = None, 
    enable_ddg: bool = True,
    ig_sessionid: str = None,
    enable_fb_scan: bool = False,
    fb_sessionid: str = None
) -> List[Dict[str, Any]]:
    """
    Estrae metadati di base dagli URL forniti (approccio Search Dorking).
    Implementa un meccanismo di fallback sicuro nel caso in cui il profilo
    risulti bloccato, inesistente o privato.
    """
    results = []
    
    # Header di base per mitigare controlli anti-bot rudimentali
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    target_to_search = urls[0].split('/')[-1] if urls else "unknown"

    async with httpx.AsyncClient(headers=headers, timeout=10.0, http2=True) as client:
        # 1. Instagram Deep Scan (Se sessionid fornito o se stiamo scansionando Instagram)
        is_instagram_target = any("instagram.com" in url for url in urls)
        if (ig_sessionid or is_instagram_target) and target_to_search and target_to_search != "unknown":
            try:
                logger.info(f"Avvio Instagram Deep Scan per {target_to_search} (sessionid fornito: {bool(ig_sessionid)})")
                ig_headers = headers.copy()
                if ig_sessionid:
                    ig_headers["Cookie"] = f"sessionid={ig_sessionid}"
                ig_headers["X-IG-App-ID"] = "936619743392459"
                ig_headers["X-ASBD-ID"] = "129477"
                ig_headers["X-IG-WWW-Claim"] = "0"
                ig_headers["X-Requested-With"] = "XMLHttpRequest"
                ig_headers["Referer"] = f"https://www.instagram.com/{target_to_search}/"
                ig_headers["Origin"] = "https://www.instagram.com"
                
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
        has_deep_scan = any(r["source"] == "Instagram Deep Scan API" for r in results)
        for url in urls:
            parsed = urllib.parse.urlparse(url)
            is_instagram = "instagram.com" in (parsed.hostname or "")
            if is_instagram and has_deep_scan:
                logger.info(f"Skipping standard scraping per {url} in quanto il Deep Scan è andato a buon fine.")
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
                    search_queries = [target_to_search]
                    if real_name and real_name.lower() != "sconosciuto":
                        # Cerca il nome esatto
                        search_queries.append(f'"{real_name}"')
                        # Dork esplicita per profili OnlyFans e leak (come richiesto)
                        search_queries.append(f'"{real_name}" onlyfans OR leak')
                        
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
                
        # 4. Facebook Deep Scan (mbasic)
        if enable_fb_scan and (fb_sessionid or target_to_search != "unknown"):
            try:
                logger.info(f"Avvio Facebook Deep Scan per {target_to_search}")
                fb_headers = headers.copy()
                if fb_sessionid:
                    fb_headers["Cookie"] = fb_sessionid if "c_user" in fb_sessionid else f"c_user={fb_sessionid}"
                
                # Usiamo mbasic per facilitare lo scraping HTML
                fb_url = f"https://mbasic.facebook.com/{target_to_search}"
                fb_resp = await client.get(fb_url, headers=fb_headers, follow_redirects=True)
                
                if fb_resp.status_code == 200:
                    soup = BeautifulSoup(fb_resp.text, "html.parser")
                    # Rimuoviamo script e style
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text(separator=" ", strip=True)
                    # Limitiamo il testo ai primi 2000 caratteri per evitare noise eccessivo
                    text = text[:2000]
                    
                    if text:
                        results.append({
                            "source": "Facebook Deep Scan API",
                            "url": fb_url,
                            "status": "ACCESSIBLE",
                            "bio": f"Extracted Text: {text}",
                            "error": None
                        })
                        logger.info("Facebook Deep Scan riuscito.")
                else:
                    logger.warning(f"Facebook Deep Scan fallito con status {fb_resp.status_code}")
            except Exception as e:
                logger.warning(f"Errore in Facebook Deep Scan: {e}")

    return results
