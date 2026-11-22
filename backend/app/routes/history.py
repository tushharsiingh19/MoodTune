"""
Search History Routes
GET /api/history
DELETE /api/history/{id}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.models import User, SearchHistory
from app.schemas.schemas import SearchHistoryResponse
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/history", response_model=List[SearchHistoryResponse])
def get_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's search history, newest first"""
    history = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return history


@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a specific history entry"""
    item = db.query(SearchHistory).filter(
        SearchHistory.id == history_id,
        SearchHistory.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found")

    db.delete(item)
    db.commit()


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear all search history for the current user"""
    db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).delete()
    db.commit()
