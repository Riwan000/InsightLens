import requests
import os
import time
from typing import Optional
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from backend.db import save_insight

load_dotenv()

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
            content = sn.get("description", "")
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['en'])
                content = " ".join([t['text'] for t in transcript.fetch()])
            except NoTranscriptFound:
                print(f"No English transcript found for video {video_id}")
            except TranscriptsDisabled:
                print(f"Transcripts are disabled for video {video_id}")
            except Exception as e:
                print(f"Error fetching transcript for video {video_id}: {e}")

            insight = {
                "source": "youtube_trending",
                "title": sn["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "content": content,
                "published_at": sn["publishedAt"],
            }
            save_insight(**insight)
            insights.append(insight)
        print(f"✅ YouTube: stored {len(insights)} trending items.")
        return insights
    except Exception as e:
        print(f"❌ YouTube error: {e}")
        return []

def fetch_youtube_search(query: str, max_results: int = 10):
    if not YOUTUBE_API_KEY:
        print("⚠️ YOUTUBE_API_KEY not set; skipping YouTube search.")
        return
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": YOUTUBE_API_KEY,
        }
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        for it in items:
            sn = it.get("snippet", {})
            video_id = it.get("id", {}).get("videoId", "")
            if video_id:
                content = sn.get("description", "")
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['en'])
                content = " ".join([t['text'] for t in transcript.fetch()])
            except NoTranscriptFound:
                print(f"No English transcript found for video {video_id}")
            except TranscriptsDisabled:
                print(f"Transcripts are disabled for video {20} {video_id}")
            except Exception as e:
                print(f"Error fetching transcript for video {video_id}: {e}")

            insight = {
                "source": "youtube_search",
                "title": sn["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "content": content,
                "published_at": sn["publishedAt"],
            }
            save_insight(**insight)
            insights.append(insight)
        print(f"✅ YouTube: stored {len(insights)} search results for '{query}'.")
        return insights
    except Exception as e:
        print(f"❌ YouTube search error: {e}")
        return []
