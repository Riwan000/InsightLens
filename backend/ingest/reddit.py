import time
import requests
from backend.db import save_insight

HEADERS = {"User-Agent": "InsightLens/0.1 (+https://example.com)"}

def fetch_reddit(subreddit: str = "worldnews", sort: str = "hot", limit: int = 10):
    """
    Uses public Reddit JSON endpoints (no OAuth) with a custom User-Agent.
    Rate limits apply; suitable for light MVP usage.
    """
    try:
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
        params = {"limit": limit}
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        posts = data.get("data", {}).get("children", [])
        count = 0
        for post in posts:
            p = post.get("data", {})
            created_utc = p.get("created_utc")
            published_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created_utc)) if created_utc else ""
            save_insight(
                source="reddit",
                title=p.get("title", ""),
                url=("https://reddit.com" + p.get("permalink", "")),
                content=p.get("selftext", ""),
                published_at=published_iso,
            )
            count += 1
        print(f"✅ Reddit: stored {count} items from r/{subreddit}.")
    except Exception as e:
        print(f"❌ Reddit error: {e}")
