"""
Music Recommendation Route
POST /api/recommend
GET  /api/songs/{mood}          — browse catalog by mood
GET  /api/catalog/stats         — how many songs per mood

Priority:  PostgreSQL songs table  →  Spotify live API  →  hardcoded fallback
"""

import random
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.connection import get_db
from app.models.models import User, SearchHistory, Song
from app.schemas.schemas import RecommendRequest, RecommendResponse, SongResponse
from app.ml.mood_detector import mood_detector
from app.services.spotify_service import spotify_service
from app.services.youtube_service import youtube_service
from app.utils.auth import get_current_user

router  = APIRouter()
logger  = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def song_orm_to_dict(s: Song) -> dict:
    """Convert a Song ORM row to a plain dict matching SongResponse."""
    return {
        "song_name"         : s.song_name,
        "artist"            : s.artist,
        "album"             : s.album,
        "album_image"       : s.album_image,
        "spotify_url"       : s.spotify_url,
        "youtube_url"       : s.youtube_url,
        "youtube_thumbnail" : s.youtube_thumbnail,
        "popularity"        : s.popularity,
        "preview_url"       : s.preview_url,
    }


def get_db_songs(db: Session, mood: str, limit: int = 10) -> list[dict]:
    """
    Pull songs from the DB for a mood.
    Picks randomly from the top-50 most popular so every request feels fresh.
    """
    rows = (
        db.query(Song)
        .filter(Song.mood == mood)
        .order_by(Song.popularity.desc())
        .limit(50)
        .all()
    )
    if not rows:
        return []

    pool = list(rows)
    random.shuffle(pool)
    return [song_orm_to_dict(s) for s in pool[:limit]]


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/recommend", response_model=RecommendResponse)
async def recommend_songs(
    request      : RecommendRequest,
    db           : Session         = Depends(get_db),
    current_user : Optional[User]  = Depends(get_current_user),
):
    """
    Full pipeline:
      1. Detect mood from text  (or use provided mood override)
      2. Try PostgreSQL catalog  → instant, no API call needed
      3. Fall back to Spotify live search  → slower, requires API key
      4. Enrich with YouTube URLs           → parallel async calls
      5. Save to search history if authenticated
    """
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text input cannot be empty"
        )

    # ── Step 1: Mood detection ────────────────────────────────────────────
    if request.mood:
        mood       = request.mood.lower()
        confidence = 1.0
    else:
        mood, confidence = mood_detector.predict(request.text)

    mood_info = mood_detector.get_mood_info(mood, confidence)
    logger.info(f"Mood detected: {mood} ({confidence:.2f})")

    # ── Step 2: DB catalog (primary source) ──────────────────────────────
    songs = get_db_songs(db, mood, limit=10)

    if songs:
        logger.info(f"Serving {len(songs)} songs from DB catalog for mood '{mood}'")
    else:
        # ── Step 3: Spotify live fallback ────────────────────────────────
        logger.info(f"No DB songs for '{mood}', falling back to Spotify API")
        songs = await spotify_service.search_songs(mood=mood, limit=10)

        # ── Step 4: YouTube enrichment ───────────────────────────────────
        if songs:
            logger.info("Enriching with YouTube links...")
            songs = await youtube_service.enrich_songs_with_youtube(songs)

    # ── Step 5: Save search history ──────────────────────────────────────
    if current_user:
        db.add(SearchHistory(
            user_id    = current_user.id,
            text       = request.text,
            mood       = mood,
            confidence = confidence,
        ))
        db.commit()

    return RecommendResponse(**mood_info, songs=songs)


@router.get("/songs/{mood}", response_model=List[SongResponse])
def browse_songs_by_mood(
    mood  : str,
    limit : int     = Query(default=20, ge=1, le=50),
    skip  : int     = Query(default=0, ge=0),
    db    : Session = Depends(get_db),
):
    """
    Browse the song catalog for a specific mood.
    Returns paginated results ordered by popularity.

    Example:  GET /api/songs/happy?limit=20&skip=0
    """
    valid_moods = {"happy","sad","angry","romantic","relaxed","motivational","party","study"}
    if mood.lower() not in valid_moods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mood. Choose from: {', '.join(sorted(valid_moods))}"
        )

    songs = (
        db.query(Song)
        .filter(Song.mood == mood.lower())
        .order_by(Song.popularity.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [song_orm_to_dict(s) for s in songs]


@router.get("/catalog/stats")
def catalog_stats(db: Session = Depends(get_db)):
    """
    Returns the total number of songs in the DB per mood.
    Useful for the frontend to show catalog size badges.
    """
    from sqlalchemy import func
    rows = (
        db.query(Song.mood, func.count(Song.id).label("count"))
        .group_by(Song.mood)
        .all()
    )
    stats   = {row.mood: row.count for row in rows}
    total   = sum(stats.values())
    return {"moods": stats, "total": total}


@router.post("/admin/songs", status_code=status.HTTP_201_CREATED)
def add_song(
    song_data    : SongResponse,
    mood         : str,
    db           : Session = Depends(get_db),
    current_user : User    = Depends(get_current_user),
):
    """
    Manually add a single song to the catalog.
    Requires authentication (admin use).
    """
    song = Song(
        song_name         = song_data.song_name,
        artist            = song_data.artist,
        album             = song_data.album,
        album_image       = song_data.album_image,
        spotify_url       = song_data.spotify_url,
        youtube_url       = song_data.youtube_url,
        youtube_thumbnail = song_data.youtube_thumbnail,
        popularity        = song_data.popularity or 50,
        mood              = mood.lower(),
        preview_url       = song_data.preview_url,
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return {"message": "Song added", "id": song.id, "mood": song.mood}
