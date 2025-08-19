# insightlens/backend/search.py

import sqlite3
from typing import List, Dict, Optional
from fastapi import APIRouter, Query
from .db import get_conn
from .ingest.news import fetch_newsapi
from .ingest.gdelt import fetch_gdelt
from .ingest.reddit import fetch_reddit
from .ingest.rss import fetch_google_news_rss
from .ingest.youtube import fetch_youtube_trending

router = APIRouter()

def search_insights(
    query: str,
    source: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict]:
    """Search stored insights by keyword(s) with optional filters."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    sql = """
        SELECT id, source, title, url, content, published_at, inserted_at
        FROM insights
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        kw = f"%{query}%"
        params.extend([kw, kw])

    if source:
        sql += " AND source = ?"
        params.append(source)

    if start_date:
        sql += " AND date(published_at) >= date(?)"
        params.append(start_date)
    if end_date:
        sql += " AND date(published_at) <= date(?)"
        params.append(end_date)

    sql += " ORDER BY published_at DESC, inserted_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    results = [dict(row) for row in c.execute(sql, params)]
    conn.close()
    return results


# 🔹 FastAPI route
@router.get("/search")
def search_router(
    query: str = Query(..., description="Keyword(s) to search in title or content"),
    source: Optional[str] = Query(None, description="Filter by source (rss, reddit, etc.)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    # Fetch from all sources and save to DB before searching
    if query:
        fetch_newsapi(query=query, page_size=limit)
        fetch_gdelt(query=query, max_records=limit)
        fetch_google_news_rss(topic=query, max_items=limit)
        fetch_reddit(subreddit=query, limit=limit)
        fetch_youtube_trending(region_code="US", max_results=limit)
    return search_insights(query, source, limit, offset, start_date, end_date)
