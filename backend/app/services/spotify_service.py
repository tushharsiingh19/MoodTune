"""
Spotify Web API Service Layer
Handles authentication and song search by mood/genre
"""

import logging
import base64
import httpx
from typing import List, Optional, Dict
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Mood → Spotify search parameters
MOOD_TO_SPOTIFY: Dict[str, Dict] = {
    "happy": {
        "query": "happy pop upbeat",
        "seed_genres": "pop,dance",
        "target_valence": 0.8,
        "target_energy": 0.7,
        "min_valence": 0.5,
    },
    "sad": {
        "query": "sad emotional acoustic",
        "seed_genres": "acoustic,indie",
        "target_valence": 0.2,
        "target_energy": 0.3,
        "max_valence": 0.4,
    },
    "angry": {
        "query": "angry rock intense",
        "seed_genres": "rock,metal",
        "target_energy": 0.9,
        "target_valence": 0.3,
        "min_energy": 0.7,
    },
    "romantic": {
        "query": "romantic love songs",
        "seed_genres": "romance,soul",
        "target_valence": 0.6,
        "target_energy": 0.4,
        "target_danceability": 0.5,
    },
    "relaxed": {
        "query": "chill ambient relaxing",
        "seed_genres": "chill,ambient",
        "target_energy": 0.3,
        "target_valence": 0.5,
        "max_energy": 0.5,
    },
    "motivational": {
        "query": "motivational workout pump up",
        "seed_genres": "hip-hop,work-out",
        "target_energy": 0.85,
        "target_valence": 0.7,
        "min_energy": 0.6,
    },
    "party": {
        "query": "party dance hits",
        "seed_genres": "dance,edm",
        "target_danceability": 0.9,
        "target_energy": 0.85,
        "min_danceability": 0.7,
    },
    "study": {
        "query": "lofi study instrumental focus",
        "seed_genres": "study,classical",
        "target_energy": 0.35,
        "target_instrumentalness": 0.7,
        "max_energy": 0.5,
    },
}


class SpotifyService:
    """
    Handles Spotify Web API integration.
    Uses Client Credentials Flow (no user auth needed for search).
    """

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"
    _access_token: Optional[str] = None

    async def _get_access_token(self) -> Optional[str]:
        """
        Get Spotify access token using Client Credentials Flow.
        Caches token for reuse (token is valid for ~1 hour).
        """
        if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
            logger.warning("Spotify credentials not configured.")
            return None

        if self._access_token:
            return self._access_token

        credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.TOKEN_URL,
                    headers={
                        "Authorization": f"Basic {encoded}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={"grant_type": "client_credentials"},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                self.__class__._access_token = data["access_token"]
                return self._access_token
            except Exception as e:
                logger.error(f"Failed to get Spotify token: {e}")
                return None

    async def search_songs(self, mood: str, limit: int = 10) -> List[Dict]:
        """
        Search Spotify for songs matching the given mood.

        Returns a list of song dicts with:
        - song_name, artist, album, album_image, spotify_url, popularity, preview_url
        """
        token = await self._get_access_token()
        if not token:
            return self._get_fallback_songs(mood)

        mood_params = MOOD_TO_SPOTIFY.get(mood, MOOD_TO_SPOTIFY["relaxed"])
        query = mood_params["query"]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.API_BASE}/search",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "q": query,
                        "type": "track",
                        "limit": limit,
                        "market": "IN",
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                tracks = data.get("tracks", {}).get("items", [])
                return [self._format_track(track) for track in tracks if track]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # Token expired, reset and retry
                    self.__class__._access_token = None
                    logger.warning("Spotify token expired, will refresh on next request.")
                logger.error(f"Spotify search error: {e}")
                return self._get_fallback_songs(mood)
            except Exception as e:
                logger.error(f"Spotify service error: {e}")
                return self._get_fallback_songs(mood)

    def _format_track(self, track: Dict) -> Dict:
        """Format a Spotify track object into our standard song dict"""
        artists = track.get("artists", [])
        artist_name = ", ".join(a["name"] for a in artists)
        album = track.get("album", {})
        images = album.get("images", [])
        album_image = images[0]["url"] if images else None

        return {
            "song_name": track.get("name", "Unknown"),
            "artist": artist_name,
            "album": album.get("name"),
            "album_image": album_image,
            "spotify_url": track.get("external_urls", {}).get("spotify"),
            "popularity": track.get("popularity"),
            "preview_url": track.get("preview_url"),
        }

    def _get_fallback_songs(self, mood: str) -> List[Dict]:
        """
        Fallback song list when Spotify API is unavailable.
        Returns curated songs per mood.
        """
        fallback = {
            "happy": [
                {"song_name": "Happy", "artist": "Pharrell Williams", "album": "G I R L",
                 "album_image": "https://i.scdn.co/image/ab67616d0000b273e8107e6d9214baa81bb79bba",
                 "spotify_url": "https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH",
                 "popularity": 85, "preview_url": None},
                {"song_name": "Good as Hell", "artist": "Lizzo", "album": "Cuz I Love You",
                 "album_image": None, "spotify_url": "https://open.spotify.com/track/5yY8Q8EIFGvUtSkvSqMVmz",
                 "popularity": 78, "preview_url": None},
            ],
            "sad": [
                {"song_name": "The Night We Met", "artist": "Lord Huron", "album": "Strange Trails",
                 "album_image": None, "spotify_url": "https://open.spotify.com/track/3ZMIcOOoG2oI7UXcBbOcYP",
                 "popularity": 82, "preview_url": None},
            ],
            "study": [
                {"song_name": "Clair de Lune", "artist": "Claude Debussy", "album": "Suite bergamasque",
                 "album_image": None, "spotify_url": "https://open.spotify.com/track/4Tr4HkA7PwTv1Gp1jCtRxR",
                 "popularity": 75, "preview_url": None},
            ],
        }
        return fallback.get(mood, fallback.get("happy", []))


# Singleton
spotify_service = SpotifyService()
