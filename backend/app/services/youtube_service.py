"""
MoodTunes AI — YouTube Data API v3 Service
===========================================
Improvements over original:
  - Detailed error logging with exact API response body
  - 3 query strategies (fallback if first returns nothing)
  - Thumbnail fallback (high → medium → default)
  - Quota-exceeded detection with clear message
  - Key-missing detection with clear message
  - Rate limiting: small delay between concurrent requests
  - /api/youtube/test endpoint for easy diagnosis
"""

import asyncio
import logging
import httpx
from typing import Optional, Dict, List

from app.utils.config import settings

logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# How long to wait between concurrent requests to avoid quota spikes
CONCURRENT_DELAY = 0.15   # seconds between each task


class YouTubeService:

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _check_key(self) -> bool:
        """Return False and log clearly if API key is missing."""
        key = settings.YOUTUBE_API_KEY
        if not key or key.strip() == "":
            logger.error(
                "YOUTUBE_API_KEY is missing or empty in your .env file.\n"
                "  1. Go to https://console.cloud.google.com\n"
                "  2. Enable 'YouTube Data API v3'\n"
                "  3. Create an API Key under Credentials\n"
                "  4. Add  YOUTUBE_API_KEY=AIza...  to backend/.env\n"
                "  5. Restart the backend server"
            )
            return False
        return True

    def _build_queries(self, song_name: str, artist: str) -> List[str]:
        """
        Return 3 query strategies from most specific to most generic.
        If strategy 1 returns no results, we try strategy 2, then 3.
        """
        return [
            f"{song_name} {artist} official audio",       # most specific
            f"{song_name} {artist} official video",       # try music video
            f"{song_name} {artist}",                      # plain search
        ]

    def _best_thumbnail(self, thumbnails: dict) -> Optional[str]:
        """Pick the best available thumbnail quality."""
        for quality in ("high", "medium", "default"):
            if quality in thumbnails:
                return thumbnails[quality].get("url")
        return None

    def _handle_api_error(self, status_code: int, body: str, song_name: str):
        """Log a human-readable message for common YouTube API errors."""
        if status_code == 400:
            logger.error(
                f"YouTube 400 Bad Request for '{song_name}'. "
                f"Check your API key format.\nResponse: {body[:300]}"
            )
        elif status_code == 403:
            if "quotaExceeded" in body or "dailyLimitExceeded" in body:
                logger.error(
                    "YouTube API daily quota exceeded!\n"
                    "  Free tier allows 10,000 units/day.\n"
                    "  Each search costs 100 units (~100 searches/day free).\n"
                    "  Options:\n"
                    "    • Wait until midnight Pacific Time for quota reset\n"
                    "    • Enable billing on Google Cloud for higher quota\n"
                    "    • Use the song seeder instead (run once, cache in DB)"
                )
            elif "keyInvalid" in body or "API_KEY_INVALID" in body:
                logger.error(
                    f"YouTube API key is INVALID.\n"
                    f"  Double-check YOUTUBE_API_KEY in your .env file.\n"
                    f"  Response: {body[:200]}"
                )
            else:
                logger.error(f"YouTube 403 Forbidden for '{song_name}'.\nResponse: {body[:300]}")
        elif status_code == 404:
            logger.warning(f"YouTube 404 for '{song_name}' — no results found.")
        else:
            logger.error(f"YouTube API error {status_code} for '{song_name}'.\nResponse: {body[:300]}")

    # ── Core search ───────────────────────────────────────────────────────────

    async def search_song(
        self,
        song_name: str,
        artist: str,
    ) -> Dict[str, Optional[str]]:
        """
        Search YouTube for a song.
        Tries up to 3 query strategies before giving up.

        Returns:
            {"youtube_url": str|None, "youtube_thumbnail": str|None}
        """
        empty = {"youtube_url": None, "youtube_thumbnail": None}

        if not self._check_key():
            return empty

        queries = self._build_queries(song_name, artist)

        async with httpx.AsyncClient(timeout=12.0) as client:
            for attempt, query in enumerate(queries, start=1):
                try:
                    logger.debug(f"YouTube search attempt {attempt}: '{query}'")

                    response = await client.get(
                        YOUTUBE_SEARCH_URL,
                        params={
                            "part":            "snippet",
                            "q":               query,
                            "type":            "video",
                            "maxResults":      1,
                            "videoCategoryId": "10",          # Music
                            "key":             settings.YOUTUBE_API_KEY,
                        },
                    )

                    # ── Non-2xx: log and decide whether to retry ──────────
                    if response.status_code != 200:
                        self._handle_api_error(
                            response.status_code,
                            response.text,
                            song_name
                        )
                        # Quota / auth errors won't improve with retries
                        if response.status_code in (400, 403):
                            return empty
                        continue   # try next query for 404 / 5xx

                    data  = response.json()
                    items = data.get("items", [])

                    if not items:
                        logger.debug(f"No results for query: '{query}' — trying next strategy")
                        continue

                    # ── Success ───────────────────────────────────────────
                    item       = items[0]
                    video_id   = item["id"].get("videoId")
                    thumbnails = item["snippet"].get("thumbnails", {})

                    if not video_id:
                        logger.warning(f"YouTube returned item with no videoId for '{song_name}'")
                        continue

                    thumbnail = self._best_thumbnail(thumbnails)

                    logger.info(f"YouTube found: '{song_name}' → https://youtu.be/{video_id}")
                    return {
                        "youtube_url":       f"https://www.youtube.com/watch?v={video_id}",
                        "youtube_thumbnail": thumbnail,
                    }

                except httpx.TimeoutException:
                    logger.warning(f"YouTube timeout (attempt {attempt}) for '{song_name}'")
                    continue
                except httpx.ConnectError:
                    logger.error("YouTube: No internet connection or DNS failure")
                    return empty
                except Exception as e:
                    logger.error(f"YouTube unexpected error for '{song_name}': {type(e).__name__}: {e}")
                    return empty

        # All 3 strategies exhausted
        logger.warning(f"YouTube: no results found for '{song_name}' by '{artist}' after 3 attempts")
        return empty

    # ── Batch enrichment ──────────────────────────────────────────────────────

    async def enrich_songs_with_youtube(self, songs: list) -> list:
        """
        Enrich a list of song dicts with YouTube URLs.
        Staggers requests slightly to reduce quota spike.
        """
        if not songs:
            return songs

        if not self._check_key():
            logger.warning("Skipping YouTube enrichment — API key not set.")
            return songs

        async def enrich_one(song: dict, delay: float) -> dict:
            await asyncio.sleep(delay)
            yt = await self.search_song(song["song_name"], song["artist"])
            return {**song, **yt}

        tasks = [
            enrich_one(song, i * CONCURRENT_DELAY)
            for i, song in enumerate(songs)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Replace exceptions with original song (no YouTube data)
        enriched = []
        for original, result in zip(songs, results):
            if isinstance(result, Exception):
                logger.error(f"enrich_one failed for '{original['song_name']}': {result}")
                enriched.append(original)
            else:
                enriched.append(result)

        yt_found = sum(1 for s in enriched if s.get("youtube_url"))
        logger.info(f"YouTube enrichment: {yt_found}/{len(enriched)} songs linked")
        return enriched

    # ── Diagnostic helper ─────────────────────────────────────────────────────

    async def test_connection(self) -> dict:
        """
        Test the YouTube API key with a single known search.
        Called by GET /api/youtube/test
        Returns a dict with status, message, and sample result.
        """
        if not self._check_key():
            return {
                "status":  "error",
                "message": "YOUTUBE_API_KEY is missing from .env",
                "fix":     "Add YOUTUBE_API_KEY=AIza... to backend/.env and restart",
            }

        result = await self.search_song("Bohemian Rhapsody", "Queen")

        if result["youtube_url"]:
            return {
                "status":       "ok",
                "message":      "YouTube API is working correctly",
                "sample_url":   result["youtube_url"],
                "sample_thumb": result["youtube_thumbnail"],
            }
        else:
            return {
                "status":  "error",
                "message": "YouTube API key is set but returned no results. "
                           "Check your Google Cloud Console for quota or restriction issues.",
                "fix":     (
                    "1. Visit https://console.cloud.google.com/apis/credentials\n"
                    "2. Make sure 'YouTube Data API v3' is ENABLED\n"
                    "3. Check the API key has no HTTP referrer restrictions\n"
                    "4. Check your daily quota at https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas"
                ),
            }


# Singleton
youtube_service = YouTubeService()
