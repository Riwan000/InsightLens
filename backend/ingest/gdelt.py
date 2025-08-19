import requests
from backend.db import save_insight

def fetch_gdelt(query: str = "market OR finance OR technology", max_records: int = 10):
    """
    GDELT 2.0 DOC API returns news documents with rich metadata.
    Reference:
      https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
    """
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": query,
            "format": "json",
            "maxrecords": max_records,
            "sort": "DateDesc",
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", [])
        for art in articles:
            save_insight(
                source="gdelt",
                title=art.get("title", ""),
                url=art.get("url", ""),
                content=art.get("seendate", "") + " | " + (art.get("language", "") or ""),
                published_at=art.get("seendate", ""),
            )
        print(f"✅ GDELT: stored {len(articles)} items.")
    except Exception as e:
        print(f"❌ GDELT error: {e}")
