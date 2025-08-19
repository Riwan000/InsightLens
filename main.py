# backend/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db import init_db
from backend.ingest.news import fetch_newsapi
from backend.ingest.rss import fetch_google_news_rss
from backend.ingest.reddit import fetch_reddit
from backend.ingest.youtube import fetch_youtube_trending, fetch_youtube_search
from backend.ingest.gdelt import fetch_gdelt
from backend.search import router as search_router

# -------------------------------
# Ingestion logic
# -------------------------------
def run_ingestion():
    print("🔧 Initializing DB…")
    init_db()

    # 🔹 Google News RSS (no key)
    fetch_google_news_rss(topic=None, region="IN:en", max_items=10)

    # 🔹 NewsAPI
    fetch_newsapi(query="SaaS OR startup OR AI", language="en", page_size=10)

    # 🔹 Reddit
    fetch_reddit(subreddit="technology", sort="hot", limit=10)

    # 🔹 YouTube
    fetch_youtube_trending(region_code="US", max_results=10)
    fetch_youtube_search(query="AI news", max_results=10)

    # 🔹 GDELT
    fetch_gdelt(query="SaaS OR startup OR technology OR finance", max_records=10)

    print("✅ Ingestion complete.")


# -------------------------------
# FastAPI App
# -------------------------------
app = FastAPI(title="InsightLens API", version="0.1.0")

# Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Ingestion trigger (manual via API)
@app.post("/ingest")
def ingest_data():
    run_ingestion()
    return {"status": "ingestion complete"}

# Attach search routes
app.include_router(search_router)


# -------------------------------
# Script entrypoint
# -------------------------------
if __name__ == "__main__":
    topic = os.getenv("INSIGHTLENS_TOPIC")
    if topic:
        from backend.ingest.rss import fetch_google_news_rss
        init_db()
        fetch_google_news_rss(topic=topic, region="IN:en", max_items=10)
        print("✅ Topic-specific RSS fetch complete.")
    else:
        run_ingestion()
