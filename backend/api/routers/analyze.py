import asyncio
import uuid
import re
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session
from backend.schemas import AnalyzeRequest
from backend.models import ProfileAnalysis, AnalysisStatus
from backend.database import get_session
import backend.database
from backend.models.user import User
from backend.api.routers.auth import get_current_user
from backend.core.logger import logger
from backend.services.discovery import SherlockAdapter
from backend.services.scraper import gather_profile_metadata

router = APIRouter()

async def guess_real_name(username: str) -> str:
    """Usa l'LLM per dedurre il nome reale dall'username per potenziare l'OSINT."""
    try:
        import os
        from dotenv import dotenv_values
        env_config = dotenv_values(".env")
        ai_provider = env_config.get("AI_PROVIDER", "gemini").lower()
        prompt = f"Data l'username '{username}', deduci il probabile nome e cognome reale. Rispondi SOLO con il nome e cognome testuale, o 'Sconosciuto' se è totalmente impossibile da dedurre. Esempio 1: mario.rossi89 -> Mario Rossi. Esempio 2: tomasmontagna_ -> Tomas Montagna."
        
        name = ""
        
        if ai_provider == "groq":
            from groq import Groq
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            name = completion.choices[0].message.content.strip()
        else:
            from backend.services.risk_engine import get_client
            client = get_client()
            models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']
            response = None
            last_err = None
            
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    break
                except Exception as e:
                    logger.warning(f"Errore con {model_name} in guess_real_name: {e}. Provo il fallback...")
                    last_err = e
                    
            if response is None:
                raise last_err
                
            name = response.text.strip()
            
        if name and name.lower() != 'sconosciuto':
            return name
    except Exception as e:
        logger.warning(f"Errore durante la deduzione del nome per {username}: {e}")
    return None

def update_analysis_phase(analysis_id: uuid.UUID, phase: str):
    """Aggiorna lo stato della fase nel database per il tracciamento in tempo reale sul Frontend."""
    try:
        from sqlmodel import Session
        import backend.database
        from backend.models import ProfileAnalysis
        with Session(backend.database.engine) as session:
            analysis = session.get(ProfileAnalysis, analysis_id)
            if analysis:
                analysis.current_phase = phase
                session.add(analysis)
                session.commit()
    except Exception as e:
        logger.error(f"Errore durante l'aggiornamento della fase {phase}: {e}")

async def run_scraping_task(
    analysis_id: uuid.UUID, 
    target: str,
    enable_ddg: bool = True,
    enable_holehe: bool = True,
    ig_sessionid: str = None,
    enable_fb_scan: bool = False,
    fb_sessionid: str = None
):
    """
    Orchestra l'esecuzione di Discovery (se username) e Scraping dei metadati.
    Aggiorna lo stato del database al completamento.
    """
    if isinstance(analysis_id, str):
        analysis_id = uuid.UUID(analysis_id)
        
    try:
        update_analysis_phase(analysis_id, "Inizializzazione Sistema")
        urls_to_scrape = []
        real_name_deduced = None
        
        # Validazione rudimentale per identificare se l'input è un URL diretto o uno username
        if re.match(r"^https?://", target):
            urls_to_scrape.append(target)
            logger.info("Target identificato come URL diretto.")
        else:
            update_analysis_phase(analysis_id, "Discovery Sherlock")
            logger.info(f"Avvio Discovery tramite Sherlock per username: {target}")
            discovery_adapter = SherlockAdapter()
            urls_to_scrape = discovery_adapter.discover_profiles(target)
            
            update_analysis_phase(analysis_id, "Deduzione Identità LLM")
            logger.info(f"Avvio deduzione identità tramite LLM per l'username: {target}")
            real_name_deduced = await guess_real_name(target)
            if real_name_deduced:
                logger.info(f"Nome reale dedotto con successo: {real_name_deduced}")
        
        # Se non ho trovato URL validi in fase Discovery (o ne ho trovato zero)
        if not urls_to_scrape:
            raise Exception("Nessun URL utile trovato in fase di Discovery.")
            
        # Avvio pipeline Scraping asincrona con i nuovi flag
        raw_data = await gather_profile_metadata(
            urls_to_scrape, 
            real_name=real_name_deduced,
            enable_ddg=enable_ddg,
            ig_sessionid=ig_sessionid,
            enable_fb_scan=enable_fb_scan,
            fb_sessionid=fb_sessionid,
            update_phase_callback=lambda p: update_analysis_phase(analysis_id, p)
        )
        
        is_instagram_target = any("instagram.com" in url for url in urls_to_scrape)
        sherlock_attempted = not re.match(r"^https?://", target)

        images_to_ocr = []
        for item in raw_data:
            if item.get("images"):
                images_to_ocr.extend(item["images"])
        
        ocr_results_payload = []
        ocr_texts = []
        import httpx
        import tempfile
        import os
        from backend.services.ocr import extract_text_from_image
        from backend.services.risk_engine import summarize_media_context
        
        if images_to_ocr:
            update_analysis_phase(analysis_id, f"Estrazione Contenuto (0/{len(images_to_ocr)})")
            logger.info(f"Avvio estrazione OCR e AI context per {len(images_to_ocr)} immagini trovate.")
            async with httpx.AsyncClient() as img_client:
                for idx, img_obj in enumerate(images_to_ocr):
                    update_analysis_phase(analysis_id, f"Analisi Media ({idx+1}/{len(images_to_ocr)})")
                    try:
                        # Handle both string (legacy) and dict (new) image formats
                        img_url = img_obj if isinstance(img_obj, str) else img_obj.get("url")
                        caption = None if isinstance(img_obj, str) else img_obj.get("caption")
                        
                        if not img_url:
                            continue
                            
                        text = None
                        
                        if img_url.startswith("/mocks/"):
                            local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/public", img_url.lstrip("/")))
                            if os.path.exists(local_path):
                                import shutil
                                tmp_mock_path = os.path.join(tempfile.gettempdir(), f"ocr_mock_{analysis_id}_{idx}.png")
                                shutil.copy(local_path, tmp_mock_path)
                                text = extract_text_from_image(tmp_mock_path)
                        else:
                            img_resp = await img_client.get(img_url, timeout=10.0)
                            if img_resp.status_code == 200:
                                tmp_path = os.path.join(tempfile.gettempdir(), f"ocr_img_{analysis_id}_{idx}.jpg")
                                with open(tmp_path, "wb") as f:
                                    f.write(img_resp.content)
                                text = extract_text_from_image(tmp_path)
                        
                        if text and len(text.strip()) > 2:
                            ocr_texts.append(text)
                            ai_description = await summarize_media_context(text, caption)
                            ocr_results_payload.append({
                                "url": img_url,
                                "text_extracted": text,
                                "ai_description": ai_description
                            })
                            
                    except Exception as e:
                        logger.warning(f"Errore download ocr o riassunto immagine {idx}: {e}")

        # NLP Pipeline classica (SpaCy) come da requisiti universitari
        from backend.services.nlp import extract_pii
        combined_text = " ".join([p.get("bio", "") for p in raw_data if p.get("bio")])
        if ocr_texts:
            combined_text += " " + " ".join(ocr_texts)
            
        update_analysis_phase(analysis_id, "Correlazione NLP (SpaCy)")
        logger.info("Avvio estrazione PII tramite SpaCy...")
        spacy_entities = extract_pii(combined_text)
        spacy_payload = [e.model_dump() for e in spacy_entities]

        # Aggregazione strutturata JSON per l'LLM
        osint_payload = {
            "scraper_results": raw_data,
            "holehe_results": [],
            "databreach_results": [],
            "ocr_results": ocr_results_payload,
            "spacy_entities": spacy_payload,
            "metadata": {
                "target": target,
                "real_name_deduced": real_name_deduced,
                "enable_ddg": enable_ddg,
                "enable_holehe": enable_holehe,
                "ig_sessionid_provided": bool(ig_sessionid),
                "instagram_attempted": is_instagram_target,
                "sherlock_attempted": sherlock_attempted,
                "enable_fb_scan": enable_fb_scan,
                "fb_sessionid_provided": bool(fb_sessionid)
            }
        }

        # HOLEHE INTEGRATION
        if enable_holehe:
            update_analysis_phase(analysis_id, "Controllo Data Breach (Holehe)")
            # Semplice regex per trovare email in tutti i testi di bio
            combined_bio = " ".join([p.get("bio", "") for p in raw_data if p.get("bio")])
            emails_found = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', combined_bio)))
            if emails_found:
                logger.info(f"Trovate {len(emails_found)} email per Holehe OSINT: {emails_found}")
                from backend.services.holehe_adapter import run_holehe
                from backend.services.databreach_service import check_data_breaches
                for em in emails_found:
                    sites = await run_holehe(em)
                    if sites:
                        osint_payload["holehe_results"].append({
                            "email": em,
                            "registered_sites": sites
                        })
                        logger.info(f"[OSINT HOLEHE] {em} -> {sites}")
                    
                    # Data breach check
                    breaches = await check_data_breaches(em)
                    if breaches:
                        osint_payload["databreach_results"].append({
                            "email": em,
                            "breaches": breaches
                        })
                        logger.warning(f"[OSINT BREACH] {em} è esposta in {len(breaches)} databreaches!")
            
        import json
        payload_str = json.dumps(osint_payload, ensure_ascii=False)
        original_length = len(payload_str)
        
        # Limite di sicurezza Anti-DoS ottimizzato per LLM ad ampio contesto
        max_allowed_length = 100000
        if original_length > max_allowed_length:
            logger.warning(f"DoS Prevention: Testo troncato da {original_length} a {max_allowed_length} caratteri prima del Risk Engine.")
            payload_str = payload_str[:max_allowed_length]
        else:
            logger.info(f"Risk Engine Payload preparato con successo. Dimensione: {original_length} caratteri (limite DoS: {max_allowed_length}).")
            
        update_analysis_phase(analysis_id, "Analisi Risk Engine AI")
        logger.info("Avvio analisi Risk Engine tramite LLM...")
        # Risk Engine Analysis tramite payload JSON strutturato
        from backend.services.risk_engine import calculate_risk
        risk_report = await calculate_risk(payload_str, target, real_name_deduced)
        
        update_analysis_phase(analysis_id, "Generazione Report")
        pii_dicts = [pii.model_dump() for pii in risk_report.pii_extracted]
        
        # Aggiornamento Database con i dati raw, PII e Risk Score
        with Session(backend.database.engine) as session:
            analysis = session.get(ProfileAnalysis, analysis_id)
            if analysis:
                analysis.raw_data_dump = osint_payload
                analysis.pii_extracted = pii_dicts
                
                # Mapping campi Risk Engine sul DB Model
                analysis.risk_score = risk_report.score
                analysis.risk_level = risk_report.level.value
                analysis.llm_report = risk_report.model_dump_json()
                
                analysis.status = AnalysisStatus.COMPLETED
                session.add(analysis)
                session.commit()
                logger.info(f"Task asincrono di OSINT e Risk Engine concluso per {analysis_id}")
                
    except Exception as e:
        logger.error(f"Fallimento durante l'orchestrazione asincrona {analysis_id}: {e}")
        with Session(backend.database.engine) as session:
            analysis = session.get(ProfileAnalysis, analysis_id)
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                session.add(analysis)
                session.commit()

@router.post("/analyze", status_code=202)
def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    target_str = str(request.target_url)
    
    # Creazione record iniziale in DB
    analysis = ProfileAnalysis(
        target_url=target_str,
        status=AnalysisStatus.PENDING,
        user_id=current_user.id
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    
    fb_cookie = None
    if request.enable_fb_scan and request.fb_c_user and request.fb_xs:
        fb_cookie = f"c_user={request.fb_c_user}; xs={request.fb_xs};"

    # Affida l'orchestrazione al BackgroundTask nativo
    background_tasks.add_task(
        run_scraping_task, 
        analysis.id, 
        target_str,
        request.enable_ddg,
        request.enable_holehe,
        request.ig_sessionid,
        request.enable_fb_scan,
        fb_cookie
    )
    
    return {
        "message": "Richiesta OSINT presa in carico",
        "analysis_id": analysis.id
    }

@router.get("/history")
def get_analysis_history(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Restituisce le ultime 3 ricerche OSINT effettuate dall'utente corrente.
    """
    from sqlmodel import select
    statement = select(ProfileAnalysis).where(ProfileAnalysis.user_id == current_user.id).order_by(ProfileAnalysis.scan_date.desc()).limit(3)
    results = session.exec(statement).all()
    
    history = []
    for analysis in results:
        history.append({
            "id": analysis.id,
            "target_url": analysis.target_url,
            "status": analysis.status,
            "scan_date": analysis.scan_date,
            "risk_score": analysis.risk_score,
            "risk_level": analysis.risk_level,
        })
    return history

@router.get("/analyze/{analysis_id}")
def get_analysis_status(
    analysis_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint per il polling del Frontend.
    Restituisce lo stato corrente dell'analisi e, se COMPLETED, i risultati.
    """
    analysis = session.get(ProfileAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analisi non trovata")
        
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato a visualizzare questa analisi")
        
    import json
    llm_report_parsed = None
    if analysis.llm_report:
        try:
            llm_report_parsed = json.loads(analysis.llm_report)
        except:
            llm_report_parsed = analysis.llm_report

    return {
        "id": analysis.id,
        "target_url": analysis.target_url,
        "status": analysis.status,
        "current_phase": analysis.current_phase,
        "scan_date": analysis.scan_date,
        "risk_score": analysis.risk_score,
        "risk_level": analysis.risk_level,
        "pii_extracted": analysis.pii_extracted,
        "llm_report": llm_report_parsed,
        "raw_data_dump": analysis.raw_data_dump,
        "error_message": analysis.error_message
    }

@router.delete("/analyze/{analysis_id}")
def delete_analysis(
    analysis_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Rimuove un'analisi dalla cronologia dell'utente.
    """
    analysis = session.get(ProfileAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analisi non trovata")
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato a eliminare questa analisi")
    
    session.delete(analysis)
    session.commit()
    return {"message": "Analisi eliminata con successo"}
