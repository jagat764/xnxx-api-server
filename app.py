from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import httpx

app = FastAPI()
client = httpx.AsyncClient()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/search")
async def search(q: str, page: int = 1):
    url = f"https://www.xnxx.com/search/{q}/{page}"
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.select(".thumb"):
        href = a.get("href")
        img = a.select_one("img")
        if not href or not img: continue
        results.append({
            "url": "https://www.xnxx.com" + href,
            "thumbnail": img.get("data-src") or img.get("src")
        })
    return results

@app.get("/api/video")
async def get_video(url: str):
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    script = soup.find("script", text=lambda x: x and "html5player.setVideoUrlHigh" in x)
    if not script:
        return JSONResponse({"error": "No video URL found"}, status_code=500)
    text = script.string
    start = text.find("html5player.setVideoUrlHigh('") + len("html5player.setVideoUrlHigh('")
    end = text.find("')", start)
    video_url = text[start:end]
    return {"video": video_url}
