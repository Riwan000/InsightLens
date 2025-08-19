import os
import requests
from typing import Optional
from backend.db import save_insight

YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")

def fetch_youtube_trending(region_code: str = "US", max_results: int = 10):
    if not YOUTUBE_API_KEY:
        print("⚠️ YOUTUBE_API_KEY not set; skipping YouTube.")
        return
    try:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet",
            "chart": "mostPopular",
            "regionCode": region_code,
            "maxResults": max_results,
            "key": YOUTUBE_API_KEY,
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        for it in items:
            sn = it.get("snippet", {})
            video_id = it.get("id", "")
            save_insight(
                source="youtube",
                title=sn.get("title", ""),
                url=f"https://www.youtube.com/watch?v={video_id}",
                content=sn.get("description", ""),
                published_at=sn.get("publishedAt", ""),
            )
        print(f"✅ YouTube: stored {len(items)} trending items.")
    except Exception as e:
        print(f"❌ YouTube error: {e}")
