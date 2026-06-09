"""
MoodTunes AI — Song Database Seeder
=====================================
Populates the `songs` table from SONG_CATALOG.
Safe to re-run — skips existing spotify_ids.

Run:
    cd backend
    python -m app.services.song_seeder                        # without YouTube
    python -m app.services.song_seeder --youtube              # with YouTube links
    python -m app.services.song_seeder --youtube --backfill   # only fill missing YT links
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, engine, Base
from app.models.models import Song
from app.services.song_catalog import SONG_CATALOG
from app.services.youtube_service import youtube_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 10


def build_spotify_url(spotify_id: str):
    return f"https://open.spotify.com/track/{spotify_id}" if spotify_id else None


async def seed_all(db: Session, fetch_youtube: bool = False):
    total_added   = 0
    total_skipped = 0

    logger.info("=" * 55)
    logger.info("MoodTunes AI — Song Seeder")
    logger.info(f"YouTube enrichment: {'ENABLED' if fetch_youtube else 'DISABLED'}")
    logger.info("=" * 55)

    # ── Pre-flight YouTube check ──────────────────────────────────────────────
    if fetch_youtube:
        test = await youtube_service.test_connection()
        if test["status"] != "ok":
            logger.error(f"YouTube pre-flight FAILED: {test['message']}")
            logger.error(f"Fix: {test.get('fix','')}")
            logger.warning("Continuing without YouTube enrichment...")
            fetch_youtube = False
        else:
            logger.info(f"YouTube pre-flight OK — {test['sample_url']}")

    for mood, songs in SONG_CATALOG.items():
        logger.info(f"\n[{mood.upper()}] {len(songs)} songs")
        batch       = []
        mood_added  = 0

        for song_data in songs:
            spotify_id = song_data.get("spotify_id")

            # Skip duplicates
            if spotify_id:
             exists = (
               db.query(Song)
              .filter(
                Song.spotify_id == spotify_id,
                Song.mood == mood
            )
            .first()
             )

            if exists:
                total_skipped += 1
                continue

            yt_data = {"youtube_url": None, "youtube_thumbnail": None}
            if fetch_youtube:
                yt_data = await youtube_service.search_song(
                    song_data["song_name"], song_data["artist"]
                )
                # Small delay to respect quota
                await asyncio.sleep(0.2)

            song = Song(
                song_name         = song_data["song_name"],
                artist            = song_data["artist"],
                album             = song_data.get("album"),
                spotify_url       = build_spotify_url(spotify_id),
                spotify_id        = spotify_id,
                youtube_url       = yt_data.get("youtube_url"),
                youtube_thumbnail = yt_data.get("youtube_thumbnail"),
                popularity        = song_data.get("popularity", 50),
                mood              = mood,
                genre             = song_data.get("genre"),
            )
            batch.append(song)
            mood_added  += 1
            total_added += 1

            if len(batch) >= BATCH_SIZE:
                db.add_all(batch)
                db.commit()
                batch = []

        if batch:
            db.add_all(batch)
            db.commit()

        logger.info(f"  ✅ {mood_added} added, {total_skipped} skipped")

    logger.info(f"\n{'='*55}")
    logger.info(f"Done!  Added: {total_added}  |  Skipped: {total_skipped}")
    logger.info(f"Total songs in DB: {db.query(Song).count()}")


async def backfill_youtube(db: Session):
    """Fill in YouTube URLs for songs that are missing them."""
    missing = db.query(Song).filter(Song.youtube_url == None).all()
    logger.info(f"Found {len(missing)} songs without YouTube URLs")

    if not missing:
        logger.info("Nothing to backfill.")
        return

    # Pre-flight check
    test = await youtube_service.test_connection()
    if test["status"] != "ok":
        logger.error(f"YouTube pre-flight FAILED: {test['message']}")
        logger.error(f"Fix: {test.get('fix','')}")
        return

    updated = 0
    for i, song in enumerate(missing, 1):
        yt = await youtube_service.search_song(song.song_name, song.artist)
        if yt.get("youtube_url"):
            song.youtube_url       = yt["youtube_url"]
            song.youtube_thumbnail = yt["youtube_thumbnail"]
            updated += 1
            logger.info(f"  [{i}/{len(missing)}] ✅ {song.song_name}")
        else:
            logger.warning(f"  [{i}/{len(missing)}] ❌ {song.song_name} — not found")

        # Commit every 10 updates
        if i % 10 == 0:
            db.commit()
        await asyncio.sleep(0.25)  # respect quota

    db.commit()
    logger.info(f"\nBackfill complete — updated {updated}/{len(missing)} songs")


async def main():
    parser = argparse.ArgumentParser(description="MoodTunes song seeder")
    parser.add_argument("--youtube",  action="store_true", help="Fetch YouTube links while seeding")
    parser.add_argument("--backfill", action="store_true", help="Only backfill missing YouTube links")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.backfill:
            await backfill_youtube(db)
        else:
            await seed_all(db, fetch_youtube=args.youtube)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
