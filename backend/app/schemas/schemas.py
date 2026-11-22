"""
Pydantic schemas for request validation and response serialization
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ─────────────────────────────────────────────
# MOOD SCHEMAS
# ─────────────────────────────────────────────

class MoodRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=1000)


class MoodResponse(BaseModel):
    mood: str
    confidence: float
    emoji: str
    description: str
    color: str


# ─────────────────────────────────────────────
# MUSIC SCHEMAS
# ─────────────────────────────────────────────

class RecommendRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=1000)
    mood: Optional[str] = None


class SongResponse(BaseModel):
    song_name: str
    artist: str
    album: Optional[str] = None
    album_image: Optional[str] = None
    spotify_url: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_thumbnail: Optional[str] = None
    popularity: Optional[int] = None
    preview_url: Optional[str] = None


class RecommendResponse(BaseModel):
    mood: str
    confidence: float
    emoji: str
    description: str
    color: str
    songs: List[SongResponse]


# ─────────────────────────────────────────────
# HISTORY SCHEMAS
# ─────────────────────────────────────────────

class SearchHistoryResponse(BaseModel):
    id: int
    text: str
    mood: str
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# FAVORITES SCHEMAS
# ─────────────────────────────────────────────

class FavoriteCreate(BaseModel):
    song_name: str
    artist: str
    album: Optional[str] = None
    album_image: Optional[str] = None
    spotify_url: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_thumbnail: Optional[str] = None
    popularity: Optional[int] = None
    mood: Optional[str] = None


class FavoriteResponse(BaseModel):
    id: int
    song_name: str
    artist: str
    album: Optional[str]
    album_image: Optional[str]
    spotify_url: Optional[str]
    youtube_url: Optional[str]
    youtube_thumbnail: Optional[str]
    popularity: Optional[int]
    mood: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
