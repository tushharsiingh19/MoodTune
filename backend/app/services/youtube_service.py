"""
YouTube Data API v3 Service Layer
Fetches YouTube video URLs and thumbnails for songs
"""

import logging
import httpx
from typing import Optional, Dict
from app.utils.config import settings

logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


class YouTubeService:
    """Handles YouTube Data API v3 integration"""

    async def search_song(self, song_name: str, artist: str) -> Dict[str, Optional[str]]:
        """
        Search YouTube for a song and return the video URL and thumbnail.

        Args:
            song_name: Name of the song
            artist: Artist name

        Returns:
            dict with youtube_url and youtube_thumbnail
        """
        if not settings.YOUTUBE_API_KEY:
            logger.warning("YouTube API key not configured.")
            return {"youtube_url": None, "youtube_thumbnail": None}

        query = f"{song_name} {artist} official audio"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    YOUTUBE_SEARCH_URL,
                    params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": 1,
                        "videoCategoryId": "10",  # Music category
                        "key": settings.YOUTUBE_API_KEY,
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                if not items:
                    return {"youtube_url": None, "youtube_thumbnail": None}

                item = items[0]
                video_id = item["id"]["videoId"]
                thumbnail = item["snippet"]["thumbnails"]["high"]["url"]

                return {
                    "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                    "youtube_thumbnail": thumbnail,
                }
            except httpx.HTTPStatusError as e:
                logger.error(f"YouTube API error {e.response.status_code}: {e}")
                return {"youtube_url": None, "youtube_thumbnail": None}
            except Exception as e:
                logger.error(f"YouTube search failed for '{song_name}': {e}")
                return {"youtube_url": None, "youtube_thumbnail": None}

    async def enrich_songs_with_youtube(self, songs: list) -> list:
        """
        Enrich a list of song dicts with YouTube data.
        Runs searches concurrently for performance.
        """
        import asyncio

        async def enrich(song: dict) -> dict:
            yt_data = await self.search_song(song["song_name"], song["artist"])
            return {**song, **yt_data}

        tasks = [enrich(song) for song in songs]
        return await asyncio.gather(*tasks)


# Singleton
youtube_service = YouTubeService()
