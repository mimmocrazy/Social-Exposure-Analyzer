import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.services.scraper import gather_profile_metadata
import httpx
import tempfile

async def main():
    urls = ["https://instagram.com/marco_rossi_sec_99"]
    def dummy(phase): pass
    results = await gather_profile_metadata(urls, ig_sessionid=None, update_phase_callback=dummy)
    
    images = []
    for item in results:
        if item.get("images"):
            images.extend(item["images"])
            
    print(f"Trovate {len(images)} immagini")
    
    if not images:
        return
        
    async with httpx.AsyncClient() as img_client:
        for idx, img_obj in enumerate(images):
            img_url = img_obj.get("url")
            caption = img_obj.get("caption")
            print(f"\n--- Immagine {idx} ---")
            print(f"Caption: [omesso]")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
            }
            try:
                img_resp = await img_client.get(img_url, headers=headers, follow_redirects=True, timeout=15.0)
                print(f"Status Download: {img_resp.status_code}")
                if img_resp.status_code == 200:
                    print(f"Content-Length: {len(img_resp.content)}")
                else:
                    print("FALLITO")
            except Exception as e:
                print(f"Errore: {e}")

if __name__ == "__main__":
    asyncio.run(main())
