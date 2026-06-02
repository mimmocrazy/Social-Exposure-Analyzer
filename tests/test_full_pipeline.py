import asyncio
import os
import sys
import uuid

# Aggiungi la root del progetto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.api.routers.analyze import run_scraping_task
from sqlmodel import Session
import backend.database
from backend.models import ProfileAnalysis

async def main():
    print("Testing Full Pipeline for marco_rossi_sec_99...")
    
    # Inizializza DB
    backend.database.create_db_and_tables()
    
    target = "marco_rossi_sec_99"
    analysis_id = uuid.uuid4()
    
    # Crea finto record
    with Session(backend.database.engine) as session:
        new_analysis = ProfileAnalysis(
            id=analysis_id,
            target_url="https://instagram.com/marco_rossi_sec_99",
            platform="instagram",
            status="IN_PROGRESS"
        )
        session.add(new_analysis)
        session.commit()
        
    print(f"Created analysis {analysis_id}")
    
    # Run pipeline (no ig_sessionid to test zero-login behavior which we know gets 8 images)
    await run_scraping_task(
        analysis_id=analysis_id,
        target=target,
        enable_ddg=False,
        enable_holehe=False,
        ig_sessionid=None
    )
    
    with Session(backend.database.engine) as session:
        analysis = session.get(ProfileAnalysis, analysis_id)
        print("STATUS:", analysis.status)
        import json
        
        raw = analysis.raw_osint_data
        if raw:
            for item in raw:
                print("SOURCE:", item.get("source"))
                print("IMAGES EXTRACTED BY SCRAPER:", len(item.get("images", [])))
                
        if analysis.risk_report_json:
            report = json.loads(analysis.risk_report_json)
            media_list = report.get("media_scanned", [])
            print("MEDIA IN RISK REPORT:", len(media_list))
            for m in media_list:
                print(" -", m.get("url"), m.get("description")[:100])
        else:
            print("NO RISK REPORT")

if __name__ == "__main__":
    asyncio.run(main())
