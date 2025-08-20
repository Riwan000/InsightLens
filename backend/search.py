# insightlens/backend/search.py

import sqlite3
from typing import List, Dict, Optional
from fastapi import APIRouter, Query
from .db import get_conn
from .ingest.news import fetch_newsapi
from .ingest.gdelt import fetch_gdelt
from .ingest.reddit import fetch_reddit
from .ingest.rss import fetch_google_news_rss
import urllib.parse
from .ingest.youtube import fetch_youtube_trending, fetch_youtube_search
from .llm import summarize_insights

router = APIRouter()

def search_insights(
    query: str,
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
    limit: int = Query(20, ge=1, le=100),
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    newly_fetched_insights = []
    existing_insights = []

    # Fetch from all sources and save to DB before searching
    if query:
        # Fetch from all sources and save to DB
        # These functions now return the fetched data as well
        news_insights = fetch_newsapi(query=query, page_size=limit)
        gdelt_insights = fetch_gdelt(query=query, max_records=limit)
        google_news_insights = fetch_google_news_rss(topic=query, max_items=limit)
        reddit_query = query.replace(" ", "_")
        reddit_insights = fetch_reddit(subreddit=reddit_query, limit=limit)
        youtube_insights = fetch_youtube_search(query=query, max_results=limit)

        # Combine newly fetched insights
        newly_fetched_insights = []
        if news_insights: newly_fetched_insights.extend(news_insights)
        if gdelt_insights: newly_fetched_insights.extend(gdelt_insights)
        if google_news_insights: newly_fetched_insights.extend(google_news_insights)
        if reddit_insights: newly_fetched_insights.extend(reddit_insights)
        if youtube_insights: newly_fetched_insights.extend(youtube_insights)

    # Retrieve existing insights from the database
    existing_insights = search_insights(query, limit, offset, start_date, end_date)

    # Combine existing and newly fetched insights for summarization
    all_insights = existing_insights + newly_fetched_insights

    print(f"Total insights for summarization: {len(all_insights)} items")
    print(f"All insights content: {all_insights}")
    summary = summarize_insights(query, all_insights)
    return {"results": all_insights, "summary": summary}

