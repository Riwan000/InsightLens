import time
import requests
from requests.exceptions import RequestException
import time

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
            insights = []
            for art in articles:
                insight = {
                    "source": "gdelt",
                    "title": art.get("title", ""),
                    "url": art.get("url", ""),
                    "content": art.get("seendate", "") + " | " + (art.get("language", "") or ""),
                    "published_at": art.get("seendate", ""),
                }
                save_insight(**insight)
                insights.append(insight)
            print(f"✅ GDELT: stored {len(insights)} items.")
            return insights # Success, exit the function
        except RequestException as e:
            if r.status_code == 429 and i < retries - 1:
                print(f"⚠️ GDELT rate limit hit. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"❌ GDELT error: {e}")
                return [] # Non-retryable error or last retry failed
        except Exception as e:
            print(f"❌ GDELT error: {e}")
            return [] # Catch any other unexpected errors
