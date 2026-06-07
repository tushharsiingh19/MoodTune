"""
Mood Detection Route
POST /api/predict-mood
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.models.models import User, SearchHistory
from app.schemas.schemas import MoodRequest, MoodResponse
from app.ml.mood_detector import mood_detector
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/predict-mood", response_model=MoodResponse)
async def predict_mood(
    request: MoodRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Analyze text and predict the user's emotional mood.

    Returns predicted mood, confidence score, emoji, description, and accent color.
    Also saves to search history if user is authenticated.
    """
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text input cannot be empty"
        )

    # Run NLP mood prediction
    mood, confidence = mood_detector.predict(request.text)
    mood_info = mood_detector.get_mood_info(mood, confidence)

    # Save to search history if authenticated
    if current_user:
        history_entry = SearchHistory(
            user_id=current_user.id,
            text=request.text,
            mood=mood,
            confidence=confidence,
        )
        db.add(history_entry)
        db.commit()

    return MoodResponse(**mood_info)
