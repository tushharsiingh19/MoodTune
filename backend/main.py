"""
MoodTunes AI - FastAPI Backend Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

from app.routes import auth, mood, music, history, favorites
from app.database.connection import engine, Base
from app.utils.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MoodTunes AI API",
    description="Emotion-Based Music Recommendation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# NOTE: allow_origins=["*"] with allow_credentials=True is NOT allowed by browsers.
# We list origins explicitly. Add your exact Render/Vercel frontend URLs here.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # open during development/debugging
    allow_credentials=False,       # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Starting MoodTunes AI API...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MoodTunes AI API...")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/auth", tags=["Authentication"])
app.include_router(mood.router,      prefix="/api",      tags=["Mood Detection"])
app.include_router(music.router,     prefix="/api",      tags=["Music Recommendations"])
app.include_router(history.router,   prefix="/api",      tags=["Search History"])
app.include_router(favorites.router, prefix="/api",      tags=["Favorites"])

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"message": "MoodTunes AI API is running", "version": "1.0.0", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "MoodTunes AI"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
