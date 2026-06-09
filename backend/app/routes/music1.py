"""
Music Recommendation Route
POST /api/recommend
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.models.models import User, SearchHistory
from app.schemas.schemas import RecommendRequest, RecommendResponse
from app.ml.mood_detector import mood_detector
from app.services.spotify_service import spotify_service
from app.services.youtube_service import youtube_service
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_songs(
    request: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Full pipeline: detect mood from text → fetch Spotify songs → enrich with YouTube links.

    Returns mood info + top 10 song recommendations.
    """
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text input cannot be empty"
        )

    # Step 1: Detect mood (use provided mood if given)
    if request.mood:
        mood = request.mood.lower()
        confidence = 1.0
    else:
        mood, confidence = mood_detector.predict(request.text)

    mood_info = mood_detector.get_mood_info(mood, confidence)

    # Step 2: Fetch songs from Spotify
    songs = await spotify_service.search_songs(mood=mood, limit=10)

    # Step 3: Enrich with YouTube data
    songs = await youtube_service.enrich_songs_with_youtube(songs)

    # Step 4: Save search history if authenticated
    if current_user:
        history_entry = SearchHistory(
            user_id=current_user.id,
            text=request.text,
            mood=mood,
            confidence=confidence,
        )
        db.add(history_entry)
        db.commit()

    return RecommendResponse(
        **mood_info,
        songs=songs,
    )
