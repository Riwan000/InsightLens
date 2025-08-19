import os
import requests
from typing import Optional
from backend.db import save_insight
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY")

def fetch_newsapi(query: str = None, language: str = "en", page_size: int = 10):
    """
    Fetch recent headlines from NewsAPI (free tier: 100 req/day).
    If query is None, use top-headlines; else use 'everything'.
    """
    if not NEWS_API_KEY:
        print("⚠️ NEWS_API_KEY not set; skipping NewsAPI.")
        return

    try:
        if query:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": language,
                "pageSize": page_size,
                "sortBy": "publishedAt",
                "apiKey": NEWS_API_KEY,
            }
        else:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "language": language,
                "pageSize": page_size,
                "apiKey": NEWS_API_KEY,
            }

        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        for art in data.get("articles", []):
            save_insight(
                source="newsapi",
                title=art.get("title") or "",
                url=art.get("url") or "",
                content=art.get("description") or (art.get("content") or ""),
                published_at=art.get("publishedAt") or "",
            )
        print(f"✅ NewsAPI: stored {len(data.get('articles', []))} items.")
    except Exception as e:
        print(f"❌ NewsAPI error: {e}")
