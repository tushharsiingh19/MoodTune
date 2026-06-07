"""
Application configuration using pydantic-settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://neondb_owner:npg_Q8zIPxYoac6n@ep-polished-breeze-aqidgcpz-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

    # JWT
    SECRET_KEY: str = "changeme-super-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # Spotify
    SPOTIFY_CLIENT_ID: str = "cd2f624c68f1428c8b3e0f9fec5523e6"
    SPOTIFY_CLIENT_SECRET: str = "a02fc56814dc4625a5af13a9b8db8e87"
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/api/auth/spotify/callback"

    # YouTube
    YOUTUBE_API_KEY: str = "AIzaSyBFSo2XIYCYjTWiz0UEzk0HLXyysCwWaF0"

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "MoodTunes AI"
    VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
