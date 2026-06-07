"""
MoodTunes AI - Model Training Script
Trains a TF-IDF + Logistic Regression mood classifier.

Run: python -m app.ml.train_model
"""

import os
import re
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK resources
for res in ["punkt", "stopwords", "wordnet", "punkt_tab"]:
    nltk.download(res, quiet=True)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "ml_models"
OUTPUT_DIR.mkdir(exist_ok=True)

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))


def clean_and_process(text: str) -> str:
    """Full NLP preprocessing pipeline"""
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = word_tokenize(text)
    processed = [
        lemmatizer.lemmatize(t)
        for t in tokens
        if t not in stop_words and len(t) > 2
    ]
    return " ".join(processed)


def build_training_data():
    """
    Build comprehensive training dataset with labeled examples.
    In production, replace this with real labeled data from a CSV.
    """
    data = {
        "text": [
            # HAPPY
            "I am so happy today, everything is perfect",
            "Feeling amazing and on top of the world",
            "Today was the best day of my life",
            "I just got great news and I am overjoyed",
            "Life is beautiful and I feel fantastic",
            "I am thrilled about my new job",
            "Feeling cheerful and full of energy",
            "What a wonderful day, I am ecstatic",
            "I am so excited for the weekend",
            "My mood is great today, feeling joyful",
            "Everything is going so well, I am delighted",
            "I just achieved my goal and I am elated",
            "Feeling blessed and happy today",
            "I am in such a good mood right now",
            "Such a happy and fulfilling day",

            # SAD
            "I am feeling very sad and lonely today",
            "I am heartbroken after the breakup",
            "Feeling depressed and hopeless",
            "I cannot stop crying, feeling miserable",
            "Everything feels empty and meaningless",
            "I miss my family so much, feeling lonely",
            "Today is a dark and gloomy day for me",
            "I feel like I have lost everything",
            "Nobody understands me, I am so sad",
            "I am grieving and feeling devastated",
            "Feeling melancholy and down today",
            "I have been crying all night",
            "My heart is broken and I feel blue",
            "Feeling hopeless about the future",
            "Everything makes me want to cry",

            # ANGRY
            "I am so angry right now, this is infuriating",
            "I cannot control my rage, so mad",
            "This situation is making me furious",
            "I am frustrated and absolutely livid",
            "How dare they do this, I am outraged",
            "I feel so bitter and resentful",
            "This injustice makes my blood boil",
            "I hate how things turned out, so angry",
            "Feeling irritated and annoyed all day",
            "I want to scream I am so frustrated",
            "This is totally unfair, I am enraged",
            "I cannot stand this anymore, fuming",
            "People keep disrespecting me, I am furious",
            "My anger is at an all time high",
            "I am seething with rage right now",

            # ROMANTIC
            "I am deeply in love with someone special",
            "I miss my partner so much, feeling romantic",
            "Love is in the air today, feeling tender",
            "I have a crush and cannot stop thinking about them",
            "Feeling passionate and full of love",
            "My heart races when I see my beloved",
            "I am in a romantic and loving mood",
            "Everything feels magical when I am with you",
            "I adore my partner with all my heart",
            "Feeling affectionate and romantic today",
            "I long for the one I love",
            "Love makes everything better, feeling warm",
            "I want to spend every moment with my sweetheart",
            "Feeling intimate and close to my partner",
            "Romance is in the air, I feel love",

            # RELAXED
            "I am feeling calm and relaxed today",
            "Everything is peaceful and serene right now",
            "I just want to chill and unwind",
            "Feeling stress free and at ease",
            "I am in a very tranquil and mellow mood",
            "Time to sit back and enjoy the quiet",
            "I feel so comfortable and laid back today",
            "Feeling zen and completely at peace",
            "Just want to relax and take it easy",
            "I am in a calm and gentle state of mind",
            "Nothing stresses me out right now",
            "Feeling perfectly content and serene",
            "I want to lie down and chill out",
            "So calm and relaxed, nothing can bother me",
            "Feeling peaceful and totally unwound",

            # MOTIVATIONAL
            "I am ready to conquer my goals today",
            "Feeling motivated and determined to succeed",
            "Nothing can stop me, I am driven",
            "I am inspired and ready to work hard",
            "Today I will crush my goals and hustle",
            "I am excited for my internship starting",
            "Feeling ambitious and focused on success",
            "I am going to achieve great things today",
            "My drive and determination are unstoppable",
            "I am motivated to push through challenges",
            "Ready to grind and make things happen",
            "Feeling powerful and ready to take on the world",
            "I have a clear goal and I will achieve it",
            "My ambition is at an all time high",
            "I am determined to succeed no matter what",

            # PARTY
            "I am ready to party all night long",
            "Let us celebrate and have a great time",
            "Feeling hype and ready to dance",
            "Tonight is going to be an epic night out",
            "I want to dance and have fun all night",
            "Party mode activated, feeling so energetic",
            "Let us turn up and celebrate",
            "I am in the mood to go clubbing",
            "Time to groove and let loose tonight",
            "Feeling lit and ready to party hard",
            "I want to celebrate with music and dancing",
            "The party vibes are strong today",
            "Ready to have the time of my life",
            "Let us get this party started right now",
            "Feeling electric and ready to dance all night",

            # STUDY
            "I need to focus and study for my exam",
            "I need to concentrate and get work done",
            "Time to hit the books and study hard",
            "I am in deep study mode right now",
            "I need music to help me concentrate",
            "Preparing for my exams and need to focus",
            "I have a lot of homework to finish today",
            "Working on my research and need to focus",
            "I want to be productive and study effectively",
            "Deep work session, need to concentrate",
            "Finals are coming and I need to study",
            "I am trying to learn and absorb information",
            "I need to stay focused for this assignment",
            "Studying hard for my upcoming test",
            "I want background music while I study",
        ],
        "mood": (
            ["happy"] * 15 +
            ["sad"] * 15 +
            ["angry"] * 15 +
            ["romantic"] * 15 +
            ["relaxed"] * 15 +
            ["motivational"] * 15 +
            ["party"] * 15 +
            ["study"] * 15
        )
    }
    return pd.DataFrame(data)


def train():
    """Train and save the mood classification model"""
    logger.info("Building training dataset...")
    df = build_training_data()
    logger.info(f"Training examples: {len(df)}")
    logger.info(f"Mood distribution:\n{df['mood'].value_counts()}")

    # Preprocess text
    logger.info("Preprocessing text...")
    df["processed_text"] = df["text"].apply(clean_and_process)

    X = df["processed_text"]
    y = df["mood"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Build TF-IDF vectorizer
    logger.info("Fitting TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),        # Unigrams and bigrams
        min_df=1,
        max_df=0.95,
        sublinear_tf=True          # Apply log normalization to TF
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Train Logistic Regression
    logger.info("Training Logistic Regression classifier...")
    model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver="lbfgs",
        multi_class="multinomial",
        random_state=42
    )
    model.fit(X_train_vec, y_train)

    # Evaluate
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"\nTest Accuracy: {accuracy:.4f}")
    logger.info(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")

    # Cross-validation
    pipeline = Pipeline([("tfidf", vectorizer), ("clf", model)])
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
    logger.info(f"\nCross-validation scores: {cv_scores}")
    logger.info(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Save models
    model_path = OUTPUT_DIR / "mood_model.pkl"
    vectorizer_path = OUTPUT_DIR / "vectorizer.pkl"

    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    logger.info(f"\nModel saved to: {model_path}")
    logger.info(f"Vectorizer saved to: {vectorizer_path}")
    logger.info("Training complete!")

    return model, vectorizer


if __name__ == "__main__":
    train()
