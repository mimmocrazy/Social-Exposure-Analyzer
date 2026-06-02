import asyncio
import httpx

async def test_download():
    img_url = "https://scontent-fco2-1.cdninstagram.com/v/t51.82787-15/714774670_18604142128005268_3178732392304096375_n.jpg?stp=dst-jpg_e15_tt6&_nc_ht=scontent-fco2-1.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHfklboHF09RgKLrl3FFkO6RmmajvBzHnhTPchJZ5dz3H07VVmuWRTzK-XNGUIZpYw&_nc_ohc=prH8y1I7R_kQ7kNvwGZTll0&_nc_gid=EHhLHGlcuj1Una-u92u68Q&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_Af-PpoPS-4NN_CZdVJQSrFVTomapcWab5AXn4QcrEPuk4g&oe=6A2480D0&_nc_sid=8b3546"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(img_url, headers=headers, follow_redirects=True, timeout=15.0)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        print(f"Content length: {len(resp.content)} bytes")

if __name__ == "__main__":
    asyncio.run(test_download())
