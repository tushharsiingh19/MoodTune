"""
Mood Detection ML Service
NLP Pipeline: Text Cleaning → Tokenization → Stopword Removal → Lemmatization → TF-IDF → Logistic Regression

Moods: Happy, Sad, Angry, Romantic, Relaxed, Motivational, Party, Study
"""

import os
import re
import logging
import joblib
import numpy as np
from typing import Tuple, Dict
from pathlib import Path

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger(__name__)

# Download required NLTK data (runs once)
def download_nltk_data():
    resources = ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger", "punkt_tab"]
    for resource in resources:
        try:
            nltk.download(resource, quiet=True)
        except Exception as e:
            logger.warning(f"Could not download NLTK resource {resource}: {e}")

download_nltk_data()

# ─────────────────────────────────────────────
# MOOD METADATA
# ─────────────────────────────────────────────

MOOD_METADATA: Dict[str, Dict] = {
    "happy": {
        "emoji": "😊",
        "description": "You're feeling joyful and upbeat! Here's some music to match your positive energy.",
        "color": "#FFD700",
        "spotify_query": "happy upbeat pop 2024",
        "genres": ["pop", "dance", "indie-pop"]
    },
    "sad": {
        "emoji": "😢",
        "description": "It's okay to feel sad. Here's some gentle music to keep you company.",
        "color": "#6B8DD6",
        "spotify_query": "sad emotional acoustic",
        "genres": ["acoustic", "indie", "sad"]
    },
    "angry": {
        "emoji": "😤",
        "description": "Channel that energy! Here's some intense music for your mood.",
        "color": "#FF4444",
        "spotify_query": "angry intense rock metal",
        "genres": ["rock", "metal", "punk"]
    },
    "romantic": {
        "emoji": "💕",
        "description": "Feeling love in the air? Here's some romantic music for you.",
        "color": "#FF69B4",
        "spotify_query": "romantic love songs ballad",
        "genres": ["romance", "soul", "r-n-b"]
    },
    "relaxed": {
        "emoji": "😌",
        "description": "Time to unwind. Here's some calming music to help you relax.",
        "color": "#90EE90",
        "spotify_query": "relaxing chill ambient",
        "genres": ["chill", "ambient", "sleep"]
    },
    "motivational": {
        "emoji": "💪",
        "description": "Ready to conquer the world? Here's your power playlist!",
        "color": "#FF8C00",
        "spotify_query": "motivational workout pump up",
        "genres": ["work-out", "hip-hop", "power"]
    },
    "party": {
        "emoji": "🎉",
        "description": "Let's get this party started! Here's your ultimate party mix.",
        "color": "#9B59B6",
        "spotify_query": "party dance hits club",
        "genres": ["dance", "edm", "party"]
    },
    "study": {
        "emoji": "📚",
        "description": "Focus mode activated. Here's some music to help you concentrate.",
        "color": "#20B2AA",
        "spotify_query": "study lofi instrumental concentration",
        "genres": ["study", "focus", "classical"]
    }
}

# Keywords to help with rule-based detection when model isn't available
MOOD_KEYWORDS = {
    "happy": ["happy", "joyful", "excited", "great", "wonderful", "amazing", "fantastic",
              "cheerful", "delighted", "elated", "ecstatic", "glad", "pleased", "content",
              "thrilled", "overjoyed", "euphoric", "awesome", "good mood"],
    "sad": ["sad", "unhappy", "depressed", "lonely", "heartbroken", "miserable", "cry",
            "tears", "grief", "melancholy", "sorrowful", "gloomy", "down", "blue",
            "devastated", "hopeless", "heartache", "broken", "lost"],
    "angry": ["angry", "furious", "mad", "rage", "frustrated", "irritated", "annoyed",
              "livid", "outraged", "enraged", "hate", "bitter", "resentful", "infuriated"],
    "romantic": ["love", "romantic", "crush", "sweetheart", "miss", "beloved", "adore",
                 "affection", "passion", "desire", "longing", "intimate", "tender", "cherish"],
    "relaxed": ["relaxed", "calm", "peaceful", "chill", "serene", "tranquil", "mellow",
                "laid-back", "stress free", "at ease", "comfortable", "leisure", "unwind"],
    "motivational": ["motivated", "inspired", "determined", "ambitious", "driven", "focused",
                     "goal", "achieve", "success", "hustle", "grind", "work hard", "push",
                     "internship", "career", "opportunity"],
    "party": ["party", "celebration", "dance", "nightclub", "vibes", "fun", "wild",
              "energetic", "hyped", "lit", "turnup", "groove", "jam", "festival"],
    "study": ["study", "studying", "focus", "concentrate", "exam", "homework", "work",
              "productivity", "reading", "research", "learning", "revision", "test"]
}


class MoodDetector:
    """
    NLP-based mood detection pipeline.
    Falls back to keyword matching if ML model is not available.
    """

    MODEL_PATH = Path(__file__).parent.parent.parent / "ml_models" / "mood_model.pkl"
    VECTORIZER_PATH = Path(__file__).parent.parent.parent / "ml_models" / "vectorizer.pkl"

    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))
        self.model = None
        self.vectorizer = None
        self._load_models()

    def _load_models(self):
        """Load pre-trained model and vectorizer if they exist"""
        try:
            if self.MODEL_PATH.exists() and self.VECTORIZER_PATH.exists():
                self.model = joblib.load(self.MODEL_PATH)
                self.vectorizer = joblib.load(self.VECTORIZER_PATH)
                logger.info("ML models loaded successfully.")
            else:
                logger.warning("ML model files not found. Using keyword-based detection.")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")

    def clean_text(self, text: str) -> str:
        """
        Clean input text:
        - Convert to lowercase
        - Remove special characters and numbers
        - Normalize whitespace
        """
        text = text.lower()
        text = re.sub(r"[^a-zA-Z\s']", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize_and_lemmatize(self, text: str) -> str:
        """
        Tokenize, remove stopwords, and lemmatize the text.
        Returns processed text as a single string for TF-IDF.
        """
        tokens = word_tokenize(text)
        processed = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]
        return " ".join(processed)

    def preprocess(self, text: str) -> str:
        """Full preprocessing pipeline"""
        cleaned = self.clean_text(text)
        return self.tokenize_and_lemmatize(cleaned)

    def _keyword_based_detection(self, text: str) -> Tuple[str, float]:
        """
        Fallback: keyword-based mood detection.
        Returns (mood, confidence_score)
        """
        text_lower = text.lower()
        scores = {}

        for mood, keywords in MOOD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[mood] = score

        best_mood = max(scores, key=scores.get)
        total = sum(scores.values())

        if total == 0:
            # Default to relaxed if no keywords matched
            return "relaxed", 0.40

        confidence = min(scores[best_mood] / max(total, 1), 1.0)
        # Normalize confidence to a reasonable range
        confidence = max(0.45, min(confidence + 0.35, 0.95))
        return best_mood, round(confidence, 2)

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict mood from text.
        Uses ML model if available, otherwise falls back to keyword matching.

        Returns:
            Tuple of (mood: str, confidence: float)
        """
        if self.model and self.vectorizer:
            try:
                processed = self.preprocess(text)
                vector = self.vectorizer.transform([processed])
                mood = self.model.predict(vector)[0]
                proba = self.model.predict_proba(vector)[0]
                confidence = float(np.max(proba))
                return mood, round(confidence, 2)
            except Exception as e:
                logger.error(f"ML prediction failed: {e}. Falling back to keyword detection.")

        return self._keyword_based_detection(text)

    def get_mood_info(self, mood: str, confidence: float) -> dict:
        """Get full mood metadata including emoji, description, and color"""
        meta = MOOD_METADATA.get(mood, MOOD_METADATA["relaxed"])
        return {
            "mood": mood,
            "confidence": confidence,
            "emoji": meta["emoji"],
            "description": meta["description"],
            "color": meta["color"],
        }


# Singleton instance
mood_detector = MoodDetector()
