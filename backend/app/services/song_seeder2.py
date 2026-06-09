"""
MoodTunes AI — Song Database Seeder
=====================================
Reads the curated SONG_CATALOG and inserts every song into the
PostgreSQL `songs` table.  Safe to re-run — skips existing spotify_ids.

Run once after setting up the DB:
    cd backend
    python -m app.services.song_seeder

Optional: re-run weekly via a cron job to pick up new catalog additions.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Make sure the backend root is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, engine, Base
from app.models.models import Song
from app.services.song_catalog import SONG_CATALOG, get_catalog_stats
from app.services.youtube_service import youtube_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def build_spotify_url(spotify_id: str) -> str:
    return f"https://open.spotify.com/track/{spotify_id}" if spotify_id else None


async def fetch_youtube_data(song_name: str, artist: str) -> dict:
    """
    Fetch YouTube URL + thumbnail for a song.
    Returns dict with youtube_url and youtube_thumbnail.
    Silently returns empty dict if YouTube API key is not configured.
    """
    try:
        return await youtube_service.search_song(song_name, artist)
    except Exception as e:
        logger.warning(f"YouTube fetch failed for '{song_name}': {e}")
        return {"youtube_url": None, "youtube_thumbnail": None}


async def seed_all(db: Session, fetch_youtube: bool = True, batch_size: int = 100):
    """
    Insert all catalog songs into the DB.

    Args:
        db:            SQLAlchemy session
        fetch_youtube: Whether to call YouTube API for each song (slower but richer)
        batch_size:    How many songs to commit per batch
    """
    stats = get_catalog_stats()
    logger.info("=" * 55)
    logger.info("MoodTunes AI — Song Seeder Starting")
    logger.info("=" * 55)
    logger.info(f"Catalog size: {stats['total']} songs across {len(SONG_CATALOG)} moods")
    if fetch_youtube:
        logger.info("YouTube enrichment: ENABLED (will be slow on first run)")
    else:
        logger.info("YouTube enrichment: DISABLED  (pass fetch_youtube=True to enable)")
    logger.info("-" * 55)

    total_added   = 0
    total_skipped = 0

    for mood, songs in SONG_CATALOG.items():
        logger.info(f"\n[{mood.upper()}] — {len(songs)} songs")
        mood_added = 0
        batch      = []

        for song_data in songs:
            spotify_id = song_data.get("spotify_id")

            # ── Duplicate check ──────────────────────────────────────────
            if spotify_id:
                exists = db.query(Song).filter(Song.spotify_id == spotify_id).first()
                if exists:
                    total_skipped += 1
                    continue

            # ── Build Spotify URL ────────────────────────────────────────
            spotify_url = build_spotify_url(spotify_id)

            # ── YouTube enrichment ───────────────────────────────────────
            yt_data = {"youtube_url": None, "youtube_thumbnail": None}
            if fetch_youtube:
                yt_data = await fetch_youtube_data(song_data["song_name"], song_data["artist"])

            # ── Create Song ORM object ───────────────────────────────────
            song = Song(
                song_name         = song_data["song_name"],
                artist            = song_data["artist"],
                album             = song_data.get("album"),
                album_image       = song_data.get("album_image"),        # None until Spotify API fills it
                spotify_url       = spotify_url,
                spotify_id        = spotify_id,
                youtube_url       = yt_data.get("youtube_url"),
                youtube_thumbnail = yt_data.get("youtube_thumbnail"),
                popularity        = song_data.get("popularity", 50),
                mood              = mood,
                genre             = song_data.get("genre"),
                preview_url       = song_data.get("preview_url"),
            )
            batch.append(song)
            mood_added  += 1
            total_added += 1

            # ── Batch commit ─────────────────────────────────────────────
            if len(batch) >= batch_size:
                db.add_all(batch)
                db.commit()
                batch = []
                logger.info(f"  Committed {mood_added} songs so far...")

        # Commit remaining
        if batch:
            db.add_all(batch)
            db.commit()

        logger.info(f"  ✅ {mood_added} added, {total_skipped} skipped (already exist)")

    logger.info("\n" + "=" * 55)
    logger.info(f"Seeding complete!")
    logger.info(f"  Added  : {total_added}")
    logger.info(f"  Skipped: {total_skipped}")
    logger.info(f"  Total in DB: {db.query(Song).count()}")
    logger.info("=" * 55)


async def enrich_existing_with_youtube(db: Session):
    """
    Back-fill YouTube URLs for songs already in the DB that are missing them.
    Useful if you seeded without YouTube enrichment initially.
    """
    songs_without_yt = (
        db.query(Song)
        .filter(Song.youtube_url == None)
        .all()
    )
    logger.info(f"Found {len(songs_without_yt)} songs without YouTube URLs")

    updated = 0
    for song in songs_without_yt:
        yt_data = await fetch_youtube_data(song.song_name, song.artist)
        if yt_data.get("youtube_url"):
            song.youtube_url       = yt_data["youtube_url"]
            song.youtube_thumbnail = yt_data["youtube_thumbnail"]
            updated += 1

    db.commit()
    logger.info(f"Updated {updated} songs with YouTube URLs")


async def main():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed catalog — set fetch_youtube=True if you have a YouTube API key
        await seed_all(db, fetch_youtube=False)

        # Optionally back-fill YouTube after seeding
        # await enrich_existing_with_youtube(db)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
