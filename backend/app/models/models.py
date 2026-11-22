"""
SQLAlchemy ORM Models
Defines: User, SearchHistory, Favorites, Song
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class SearchHistory(Base):
    """Stores user mood search history"""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    mood = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="search_history")

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, mood={self.mood})>"


class Favorite(Base):
    """User's favorite songs"""
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    song_name = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    album_image = Column(String(500), nullable=True)
    spotify_url = Column(String(500), nullable=True)
    youtube_url = Column(String(500), nullable=True)
    youtube_thumbnail = Column(String(500), nullable=True)
    popularity = Column(Integer, nullable=True)
    mood = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite(id={self.id}, song={self.song_name})>"


class Song(Base):
    """
    Curated song catalog — mood-tagged songs stored in PostgreSQL.
    Used as the primary source for recommendations (faster than live Spotify API).
    Falls back to Spotify API only when DB has no songs for a mood.
    """
    __tablename__ = "songs"

    id             = Column(Integer, primary_key=True, index=True)
    song_name      = Column(String(255), nullable=False)
    artist         = Column(String(255), nullable=False)
    album          = Column(String(255), nullable=True)
    album_image    = Column(String(500), nullable=True)   # album art URL
    spotify_url    = Column(String(500), nullable=True)
    spotify_id     = Column(String(100), unique=True, nullable=True)  # dedup key
    youtube_url    = Column(String(500), nullable=True)
    youtube_thumbnail = Column(String(500), nullable=True)
    popularity     = Column(Integer, nullable=True, default=50)
    mood           = Column(String(50), nullable=False, index=True)
    genre          = Column(String(100), nullable=True)
    preview_url    = Column(String(500), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Song(id={self.id}, song='{self.song_name}', mood='{self.mood}')>"
