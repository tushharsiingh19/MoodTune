"""
Optional: Use a pre-trained HuggingFace emotion model
Much more accurate than TF-IDF but requires more RAM/CPU
"""
from transformers import pipeline

class TransformerMoodDetector:
    # Maps HuggingFace emotion labels → our mood categories
    LABEL_MAP = {
        "joy": "happy",
        "sadness": "sad", 
        "anger": "angry",
        "love": "romantic",
        "fear": "relaxed",     # approximate
        "surprise": "party",   # approximate
    }

    def __init__(self):
        # Downloads ~500MB model on first run, then cached
        self.classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )

    def predict(self, text: str):
        results = self.classifier(text)[0]
        best = max(results, key=lambda x: x["score"])
        mood = self.LABEL_MAP.get(best["label"], "relaxed")
        return mood, round(best["score"], 2)