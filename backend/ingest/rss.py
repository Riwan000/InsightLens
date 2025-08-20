import time
import feedparser
import urllib.parse
import time
from backend.db import save_insight

def fetch_google_news_rss(topic: str = None, region: str = "IN:en", max_items: int = 10):
    """
    Fetch Google News RSS (free, no key). Topic optional.
    region is 'IN:en' for India-English feed by default.
    """
    try:
        base = "https://news.google.com/rss"
        if topic:
            # topic query
            encoded_topic = urllib.parse.quote_plus(topic)
            url = f"{base}/search?q={encoded_topic}&hl=en-IN&gl=IN&ceid={region}"
        else:
            # top headlines for region
            url = f"{base}?hl=en-IN&gl=IN&ceid={region}"

        feed = feedparser.parse(url)
        count = 0
        for entry in feed.entries[:max_items]:
            published_struct = entry.get("published_parsed")
            published_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", published_struct) if published_struct else ""
            insight = {
                "source": "google_rss",
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "content": entry.get("summary", ""),
                "published_at": published_iso,
            }
            save_insight(**insight)
            insights.append(insight)
            count += 1
        print(f"✅ Google RSS: stored {count} items.")
        return insights
    except Exception as e:
        print(f"❌ Google RSS error: {e}")
        return []
