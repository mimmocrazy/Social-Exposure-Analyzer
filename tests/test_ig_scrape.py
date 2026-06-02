import asyncio
import os
import sys

# Aggiungi la root del progetto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.services.scraper import gather_profile_metadata

async def main():
    print("Testing Instagram Deep Scan without mocks...")
    # Scegliamo un profilo pubblico noto, es. 'instagram' o 'cristiano' o un brand 'nike'
    # Per non testare su persone vere, usiamo un account istituzionale.
    urls = ["https://instagram.com/marco_rossi_sec_99"]
    
    # Callback vuota
    def dummy_callback(phase):
        print(f"Phase update: {phase}")

    results = await gather_profile_metadata(urls, ig_sessionid="123456789", update_phase_callback=dummy_callback)
    
    import json
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
