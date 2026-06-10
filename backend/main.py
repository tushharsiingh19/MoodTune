"""
MoodTunes AI - FastAPI Backend Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import uvicorn

from app.routes import auth, mood, music, history, favorites
from app.database.connection import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MoodTunes AI API",
    description="Emotion-Based Music Recommendation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://moodtune-web.onrender.com"
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://moodtunes.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting MoodTunes AI API...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MoodTunes AI API...")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(mood.router, prefix="/api", tags=["Mood Detection"])
app.include_router(music.router, prefix="/api", tags=["Music Recommendations"])
app.include_router(history.router, prefix="/api", tags=["Search History"])
app.include_router(favorites.router, prefix="/api", tags=["Favorites"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "MoodTunes AI API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "MoodTunes AI"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
