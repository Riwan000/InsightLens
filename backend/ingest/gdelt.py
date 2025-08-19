import time
import requests
from requests.exceptions import RequestException

from backend.db import save_insight

def fetch_gdelt(query: str = "market OR finance OR technology", max_records: int = 10):
    """
    GDELT 2.0 DOC API returns news documents with rich metadata.
    Reference:
      https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
    """
    retries = 3
    delay = 1  # seconds
    for i in range(retries):
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
            return # Success, exit the function
        except RequestException as e:
            if r.status_code == 429 and i < retries - 1:
                print(f"⚠️ GDELT rate limit hit. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"❌ GDELT error: {e}")
                break # Non-retryable error or last retry failed
        except Exception as e:
            print(f"❌ GDELT error: {e}")
            break # Catch any other unexpected errors
