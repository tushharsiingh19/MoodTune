"""
MoodTunes AI - Optimized Model Training Script
================================================
Pipeline:
  1. Load data from data.csv (with fallback to hardcoded examples)
  2. Text cleaning → Tokenization → Stopword Removal → Lemmatization
  3. TF-IDF Vectorization (unigrams + bigrams + trigrams)
  4. Auto model selection (LR vs LinearSVC vs SGD)
  5. Calibration → predict_proba support on all models
  6. Cross-validation evaluation
  7. Save best model + vectorizer as .pkl

Run:
  python -m app.ml.train_model
"""

import re
import logging
import warnings
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.utils import resample

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── NLTK Downloads ────────────────────────────────────────────────────────────
for res in ["punkt", "stopwords", "wordnet", "punkt_tab", "omw-1.4"]:
    nltk.download(res, quiet=True)

# ── Paths ─────────────────────────────────────────────────────────────────────
ML_DIR    = Path(__file__).parent
OUTPUT_DIR = Path(__file__).parent.parent.parent / "ml_models"
OUTPUT_DIR.mkdir(exist_ok=True)

DATA_CSV = ML_DIR / "data.csv"

# ── NLP Tools ─────────────────────────────────────────────────────────────────
lemmatizer = WordNetLemmatizer()
stop_words  = set(stopwords.words("english"))

# Keep negation words — they flip mood meaning ("not happy" ≠ "happy")
NEGATIONS = {"not", "no", "never", "neither", "nor", "nothing", "nobody",
             "nowhere", "cannot", "can't", "won't", "don't", "doesn't",
             "didn't", "isn't", "aren't", "wasn't", "weren't", "hardly",
             "barely", "scarcely"}
stop_words -= NEGATIONS

# ── Mood Labels ───────────────────────────────────────────────────────────────
VALID_MOODS = {
    "happy", "sad", "angry", "romantic",
    "relaxed", "motivational", "party", "study"
}

# =============================================================================
# SECTION 1 — TEXT PREPROCESSING
# =============================================================================

def clean_and_process(text: str) -> str:
    """
    Full NLP preprocessing pipeline:
      lowercase → strip special chars → tokenize
      → remove stopwords (keep negations) → lemmatize
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # Lowercase
    text = text.lower()

    # Expand common contractions before stripping apostrophes
    contractions = {
        "i'm": "i am", "i've": "i have", "i'll": "i will",
        "i'd": "i would", "you're": "you are", "it's": "it is",
        "don't": "do not", "can't": "cannot", "won't": "will not",
        "doesn't": "does not", "didn't": "did not", "isn't": "is not",
        "aren't": "are not", "wasn't": "was not", "weren't": "were not",
        "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
        "couldn't": "could not", "wouldn't": "would not",
        "shouldn't": "should not", "that's": "that is",
        "there's": "there is", "they're": "they are",
        "we're": "we are", "we've": "we have", "they've": "they have",
        "let's": "let us",
    }
    for short, full in contractions.items():
        text = text.replace(short, full)

    # Remove URLs, mentions, hashtags
    text = re.sub(r"http\S+|www\S+|@\w+|#\w+", " ", text)

    # Keep only letters and spaces
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return ""

    # Tokenize
    tokens = word_tokenize(text)

    # Remove stopwords (negations preserved) + lemmatize + min length 2
    processed = [
        lemmatizer.lemmatize(t)
        for t in tokens
        if (t not in stop_words or t in NEGATIONS) and len(t) >= 2
    ]

    return " ".join(processed)


# =============================================================================
# SECTION 2 — HARDCODED TRAINING DATA (fallback / seed)
# =============================================================================

SEED_DATA = {
    "happy": [
        "I am so happy today everything is going perfectly",
        "Feeling absolutely amazing and on top of the world",
        "Today was the best day of my life I am ecstatic",
        "I just got great news and I am overjoyed right now",
        "Life is beautiful and I feel utterly fantastic",
        "I am thrilled about my new promotion at work",
        "Feeling cheerful and bursting with energy today",
        "What a wonderful morning I woke up feeling joyful",
        "I am so excited about the weekend plans ahead",
        "My mood is incredibly good today feeling blessed",
        "Everything is going so well I am absolutely delighted",
        "I just achieved my biggest goal and I feel elated",
        "Feeling grateful and happy about everything in my life",
        "I am in such a fantastic mood right now nothing can ruin it",
        "Such a happy and fulfilling day spent with loved ones",
        "I cannot stop smiling today everything feels perfect",
        "I feel like dancing I am so full of joy and happiness",
        "Got amazing news today feeling on cloud nine",
        "Life feels so good right now I am genuinely happy",
        "I feel light and free today pure happiness",
        "Just had the most wonderful experience feeling euphoric",
        "My heart is so full of happiness and gratitude today",
        "I am gleaming with joy today everything went right",
        "Feeling pure bliss and contentment with my life",
        "I am so pleased with how everything turned out today",
        "Woke up feeling refreshed and incredibly happy",
        "I am radiating positivity and joy today",
        "Such a good day today I feel genuinely elated",
        "I feel wonderful inside and out pure happiness",
        "Smiling from ear to ear today life is good",
    ],
    "sad": [
        "I am feeling very sad and lonely today nobody cares",
        "I am heartbroken after the breakup cannot stop crying",
        "Feeling deeply depressed and completely hopeless",
        "I cannot stop crying everything feels so miserable",
        "Everything feels empty and utterly meaningless to me",
        "I miss my family so much feeling devastatingly lonely",
        "Today is a dark and gloomy day I feel broken",
        "I feel like I have lost absolutely everything I valued",
        "Nobody understands me at all I am so deeply sad",
        "I am grieving and feeling completely devastated inside",
        "Feeling melancholy and very down today cannot shake it",
        "I have been crying all night nothing helps the pain",
        "My heart is shattered and I feel utterly blue",
        "Feeling completely hopeless about the future ahead",
        "Everything makes me want to cry today it is too much",
        "I feel invisible and unloved by everyone around me",
        "The sadness is overwhelming me today I cannot function",
        "I am in so much emotional pain right now it hurts",
        "Lost and alone with no one to turn to feeling sad",
        "My world feels dark and grey today so much sorrow",
        "I feel like a failure and it is making me so sad",
        "Crying silently because nobody notices my pain",
        "I do not see the point of anything today so sad",
        "Feeling numb and disconnected from everyone around",
        "My soul feels heavy with sadness today unbearable",
        "I wish things were different but they never change",
        "Tears keep falling and I do not know how to stop",
        "I feel so empty inside like nothing matters anymore",
        "The loneliness is crushing me today I am so sad",
        "I feel forgotten and unwanted by the world today",
    ],
    "angry": [
        "I am so angry right now this is absolutely infuriating",
        "I cannot control my rage I am completely mad",
        "This situation is making me furious beyond belief",
        "I am utterly frustrated and absolutely livid today",
        "How dare they do this to me I am totally outraged",
        "I feel so bitter and deeply resentful about this",
        "This injustice makes my blood boil I am enraged",
        "I hate how everything turned out so incredibly angry",
        "Feeling extremely irritated and annoyed the whole day",
        "I want to scream I am so unbelievably frustrated",
        "This is completely unfair and I am absolutely enraged",
        "I cannot stand this anymore I am fuming with anger",
        "People keep disrespecting me and I am furious now",
        "My anger is at an all time high today I am seething",
        "I am absolutely seething with rage right now cannot calm",
        "So fed up with everything my patience has run out",
        "I am burning with anger at the injustice of it all",
        "They crossed the line and I am absolutely furious",
        "I feel explosive with anger right now it is intense",
        "Rage is consuming me today I am so unbelievably mad",
        "I am disgusted and enraged by what just happened",
        "My temper is completely out of control right now",
        "I feel like I could explode I am that furious today",
        "Absolutely livid at the unfair treatment I received",
        "This betrayal has made me angrier than I have ever been",
        "I am boiling with rage and cannot calm myself down",
        "The audacity of people is making me so furious today",
        "I am incensed by what happened and want answers now",
        "Feeling wrathful and intensely angry about everything",
        "My blood is boiling with pure uncontrollable anger",
    ],
    "romantic": [
        "I am deeply in love with someone truly special to me",
        "I miss my partner so much feeling incredibly romantic",
        "Love is absolutely in the air today feeling very tender",
        "I have a crush and cannot stop thinking about them",
        "Feeling passionate and completely full of deep love",
        "My heart races wildly when I see my beloved partner",
        "I am in a romantic and loving mood tonight",
        "Everything feels so magical when I am with the one I love",
        "I adore my partner with every single piece of my heart",
        "Feeling deeply affectionate and very romantic today",
        "I long for the person I love more than anything",
        "Love makes everything better feeling warm and adored",
        "I want to spend every single moment with my sweetheart",
        "Feeling intimate and deeply close to my partner today",
        "Romance fills the air and I feel so much love",
        "I am head over heels in love and it feels wonderful",
        "Thinking about my partner and feeling butterflies inside",
        "I cherish every moment we share together so deeply",
        "The love I feel is overwhelming and beautiful today",
        "I am completely smitten and falling deeper in love",
        "My heart is overflowing with love for someone special",
        "I feel so connected and bonded with my partner today",
        "Love is the only thing on my mind right now",
        "I want to hold my partner close and never let go",
        "Feeling romantic and wanting to express my deep love",
        "Every thought brings me back to the one that I love",
        "I am falling more in love every single passing day",
        "The warmth of love surrounds me and fills my heart",
        "I feel a deep passionate connection with my partner",
        "My love for them grows stronger and deeper each day",
    ],
    "relaxed": [
        "I am feeling completely calm and deeply relaxed today",
        "Everything is peaceful and beautifully serene right now",
        "I just want to chill out and fully unwind tonight",
        "Feeling totally stress free and perfectly at ease",
        "I am in a very tranquil and wonderfully mellow mood",
        "Time to sit back and enjoy the quiet peaceful moment",
        "I feel so comfortable and completely laid back today",
        "Feeling zen and absolutely at peace with everything",
        "Just want to relax and take everything nice and easy",
        "I am in a calm and gentle state of mind right now",
        "Nothing stresses me out at all today complete peace",
        "Feeling perfectly content and wonderfully serene",
        "I want to lie down and completely chill out now",
        "So calm and relaxed absolutely nothing can bother me",
        "Feeling peacefully unwound and totally at rest",
        "I am melting into a state of pure relaxation today",
        "The world feels still and quiet and I love it",
        "I feel unhurried and completely at peace today",
        "Breathing slowly and feeling wonderfully tranquil",
        "Life feels slow and beautiful and completely calm",
        "I am in my happy place feeling deeply relaxed",
        "Nothing bothers me right now just pure serenity",
        "Feeling mellow and easygoing with no worries at all",
        "I am at peace with myself and the world today",
        "Just going with the flow feeling totally relaxed",
        "The calm feels good today no stress no worries",
        "I feel like I am floating in peaceful tranquility",
        "Everything is gentle and soft and perfectly calm",
        "I am completely unwound and feeling wonderfully serene",
        "So relaxed that nothing in the world could faze me",
    ],
    "motivational": [
        "I am absolutely ready to conquer all my goals today",
        "Feeling incredibly motivated and determined to succeed",
        "Nothing in this world can stop me I am fully driven",
        "I am deeply inspired and ready to work extremely hard",
        "Today I will crush every single goal and hustle hard",
        "I am so excited for my internship starting tomorrow",
        "Feeling fiercely ambitious and sharply focused on success",
        "I am going to achieve truly great things starting today",
        "My drive and determination are completely unstoppable",
        "I am powerfully motivated to push through all challenges",
        "Ready to grind relentlessly and make amazing things happen",
        "Feeling powerful confident and ready to take on the world",
        "I have a clear burning goal and I will absolutely achieve it",
        "My ambition is at an all time high nothing will stop me",
        "I am completely determined to succeed no matter what it takes",
        "I woke up today ready to be the best version of myself",
        "The fire in me is burning to chase my biggest dreams",
        "I believe in myself completely and I will make it happen",
        "Every obstacle is just another chance to prove myself",
        "I am on a mission today and nothing will distract me",
        "Feeling unstoppable and ready to level up my entire life",
        "I choose to be great today action over excuses always",
        "I am fueled by purpose and passion to reach my dreams",
        "Success is the only option on my mind right now",
        "I am laser focused and ready to put in the hard work",
        "My potential is limitless and today I will prove it",
        "Rising up today with full energy and fierce determination",
        "I am building the life I want one step at a time",
        "Every day is a new chance to get closer to my goals",
        "I am committed to my growth and I will never give up",
    ],
    "party": [
        "I am absolutely ready to party hard all night long",
        "Let us celebrate wildly and have the most amazing time",
        "Feeling completely hyped and totally ready to dance",
        "Tonight is going to be the most epic night out ever",
        "I want to dance all night and have incredible fun",
        "Party mode is fully activated feeling insanely energetic",
        "Let us turn up hard and celebrate like there is no tomorrow",
        "I am in the perfect mood to go clubbing tonight",
        "Time to groove freely and let completely loose tonight",
        "Feeling absolutely lit and so ready to party hard",
        "I want to celebrate everything with loud music and dancing",
        "The party vibes are incredibly strong today I am pumped",
        "Ready to have the absolute time of my life tonight",
        "Let us get this amazing party started right now",
        "Feeling electric and charged up ready to dance all night",
        "The music is calling me and I am ready to answer it",
        "I live for nights like this the energy is incredible",
        "Feeling so alive and ready for an unforgettable night out",
        "The dance floor is waiting for me and I cannot wait",
        "I am so excited to celebrate and let go of everything",
        "Tonight we celebrate and nothing can dim this vibe",
        "I am buzzing with excitement for this amazing night",
        "The pre party excitement is real I am so pumped up",
        "Time to dance until the sun comes up feeling amazing",
        "I am ready to make incredible memories tonight on the floor",
        "The beats are calling me and I am ready to move",
        "I want to lose myself in the music and just dance",
        "Feeling euphoric and ready for an absolutely wild night",
        "Tonight is for celebrating life and dancing freely",
        "I am in full party mode nothing can stop me tonight",
    ],
    "study": [
        "I need to focus completely and study hard for my exam",
        "I need to concentrate deeply and get all my work done",
        "Time to hit the books seriously and study very hard",
        "I am in total deep study mode right now focused",
        "I need the right music to help me concentrate better",
        "Preparing intensely for my exams and need full focus",
        "I have so much homework to finish today must focus",
        "Working on my research paper and need complete focus",
        "I want to be truly productive and study very effectively",
        "Deep focused work session I need to concentrate hard",
        "Finals are coming soon and I really need to study now",
        "I am trying hard to learn and absorb all the information",
        "I need to stay completely focused for this assignment",
        "Studying intensely hard for my very important upcoming test",
        "I want calm background music while I study productively",
        "I have a long study session ahead and need to focus",
        "Preparing for a big presentation and need concentration",
        "I am revising my notes and need complete silence",
        "I need to get into the zone for this study session",
        "Assignments are piling up and I need to stay focused",
        "I am doing research and need instrumental background music",
        "Library mode activated I need to concentrate fully",
        "I have three chapters to read and need to focus now",
        "Exam tomorrow and I am studying late into the night",
        "I need quiet productive music for my study session",
        "Brain in full gear studying and absorbing knowledge",
        "I want to maximize my productivity during this study time",
        "Focus is everything right now I need to study hard",
        "Sitting at my desk ready to study and learn everything",
        "I am in a deep study flow state and need to stay there",
    ],
}


# =============================================================================
# SECTION 3 — DATA AUGMENTATION
# =============================================================================

def augment_text(text: str) -> list[str]:
    """
    Simple rule-based augmentation:
      - Synonym swap for common mood words
      - Prefix injection ("Today I feel...", "Right now I am...")
      - Sentence shuffle for multi-sentence texts
    Returns a list of augmented variants (may be empty).
    """
    augmented = []

    prefixes = [
        "today", "right now", "honestly", "lately", "at this moment",
        "i feel like", "deep down", "currently", "i must say",
    ]

    # Add a random prefix variant
    words = text.split()
    if len(words) >= 4:
        prefix = np.random.choice(prefixes)
        augmented.append(f"{prefix} {text}")

    # Light synonym swaps for high-frequency words
    swaps = {
        "happy":       ["joyful", "cheerful", "elated", "glad", "content"],
        "sad":         ["unhappy", "sorrowful", "miserable", "gloomy", "down"],
        "angry":       ["furious", "livid", "enraged", "irate", "mad"],
        "excited":     ["thrilled", "pumped", "stoked", "eager", "enthusiastic"],
        "relaxed":     ["calm", "serene", "peaceful", "tranquil", "chill"],
        "motivated":   ["driven", "determined", "ambitious", "inspired", "focused"],
        "love":        ["adore", "cherish", "treasure", "fancy", "care for"],
        "feel":        ["am feeling", "sense", "experience"],
        "great":       ["wonderful", "fantastic", "amazing", "superb", "brilliant"],
        "terrible":    ["awful", "dreadful", "horrible", "atrocious", "dreadful"],
        "lonely":      ["alone", "isolated", "abandoned", "forsaken", "solitary"],
        "tired":       ["exhausted", "drained", "weary", "fatigued", "spent"],
    }

    swapped = text
    for word, synonyms in swaps.items():
        if word in swapped.lower():
            synonym = np.random.choice(synonyms)
            swapped = re.sub(r'\b' + word + r'\b', synonym, swapped, flags=re.IGNORECASE)
    if swapped != text:
        augmented.append(swapped)

    return augmented


def build_training_data() -> pd.DataFrame:
    """
    Load training data:
      1. Try data.csv in the same directory first
      2. Fall back to SEED_DATA hardcoded examples
      3. Apply augmentation to reach a healthy class size
    """
    rows = []

    # ── Load from CSV ──────────────────────────────────────────────────────
    if DATA_CSV.exists():
        logger.info(f"Loading data from {DATA_CSV}")
        csv_df = pd.read_csv(DATA_CSV)

        # Validate required columns
        if "text" not in csv_df.columns or "mood" not in csv_df.columns:
            logger.warning("CSV missing 'text' or 'mood' column — falling back to seed data.")
        else:
            # Drop rows with unknown moods or empty text
            csv_df = csv_df.dropna(subset=["text", "mood"])
            csv_df = csv_df[csv_df["mood"].isin(VALID_MOODS)]
            csv_df = csv_df[csv_df["text"].str.strip().str.len() > 5]
            rows.append(csv_df[["text", "mood"]])
            logger.info(f"CSV loaded: {len(csv_df)} valid rows")

    # ── Always include seed data as baseline ──────────────────────────────
    seed_rows = [
        {"text": t, "mood": mood}
        for mood, texts in SEED_DATA.items()
        for t in texts
    ]
    rows.append(pd.DataFrame(seed_rows))
    logger.info(f"Seed data: {len(seed_rows)} rows")

    df = pd.concat(rows, ignore_index=True)
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

    # ── Augmentation: pad under-represented classes to min 100 samples ────
    TARGET_MIN = 100
    augmented_rows = []

    for mood in VALID_MOODS:
        mood_df = df[df["mood"] == mood]
        count   = len(mood_df)

        if count < TARGET_MIN:
            needed = TARGET_MIN - count
            logger.info(f"Augmenting '{mood}': {count} → {TARGET_MIN} (+{needed})")
            pool = mood_df["text"].tolist()

            for _ in range(needed):
                base = np.random.choice(pool)
                variants = augment_text(base)
                if variants:
                    augmented_rows.append({"text": np.random.choice(variants), "mood": mood})
                else:
                    # Just repeat a slightly noisy copy
                    augmented_rows.append({"text": base + " truly", "mood": mood})

    if augmented_rows:
        df = pd.concat([df, pd.DataFrame(augmented_rows)], ignore_index=True)
        df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

    logger.info(f"Final dataset: {len(df)} rows")
    logger.info(f"Distribution:\n{df['mood'].value_counts().to_string()}")
    return df


# =============================================================================
# SECTION 4 — TRAINING
# =============================================================================

def get_vectorizer() -> TfidfVectorizer:
    """Return the optimized TF-IDF vectorizer"""
    return TfidfVectorizer(
        max_features=15000,          # rich vocabulary
        ngram_range=(1, 3),          # unigrams + bigrams + trigrams
        min_df=1,                    # keep rare but useful terms
        max_df=0.88,                 # drop near-universal terms
        sublinear_tf=True,           # log(TF) — reduces dominance of frequent words
        analyzer="word",
        token_pattern=r"\b[a-zA-Z][a-zA-Z]+\b",  # real words only
        strip_accents="unicode",
    )


def get_candidates(X_size: int) -> dict:
    """
    Return candidate models.
    LinearSVC wrapped in CalibratedClassifierCV so all support predict_proba.
    """
    # Choose cv folds based on dataset size to avoid empty folds
    cal_cv = min(5, max(2, X_size // 20))

    return {
        "LogisticRegression": LogisticRegression(
            max_iter=2000,
            C=5.0,
            solver="lbfgs",
            multi_class="multinomial",
            class_weight="balanced",   # handles class imbalance
            random_state=42,
        ),
        "LinearSVC_calibrated": CalibratedClassifierCV(
            LinearSVC(
                max_iter=3000,
                C=1.0,
                class_weight="balanced",
                random_state=42,
            ),
            cv=cal_cv,
            method="sigmoid",          # Platt scaling for probabilities
        ),
        "SGDClassifier": CalibratedClassifierCV(
            SGDClassifier(
                loss="modified_huber", # naturally supports predict_proba
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
            cv=cal_cv,
            method="sigmoid",
        ),
    }


def train():
    """
    Full training pipeline.
    Returns (best_model, vectorizer) tuple.
    """
    logger.info("=" * 60)
    logger.info("MoodTunes AI — Model Training")
    logger.info("=" * 60)

    # ── 1. Load Data ──────────────────────────────────────────────────────
    df = build_training_data()

    # ── 2. Preprocess ─────────────────────────────────────────────────────
    logger.info("\nPreprocessing text...")
    df["processed_text"] = df["text"].apply(clean_and_process)

    # Drop empty strings produced by preprocessing
    df = df[df["processed_text"].str.strip().str.len() > 0].reset_index(drop=True)

    X = df["processed_text"]
    y = df["mood"]

    logger.info(f"Samples after preprocessing: {len(X)}")

    # ── 3. Train/Test Split ───────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y          # preserve class distribution in both splits
    )
    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # ── 4. Vectorize ──────────────────────────────────────────────────────
    logger.info("\nFitting TF-IDF vectorizer...")
    vectorizer   = get_vectorizer()
    X_train_vec  = vectorizer.fit_transform(X_train)
    X_test_vec   = vectorizer.transform(X_test)
    logger.info(f"Vocabulary size: {len(vectorizer.vocabulary_):,}")

    # ── 5. Model Selection ────────────────────────────────────────────────
    logger.info("\nEvaluating candidate models (5-fold CV on train set)...")
    candidates  = get_candidates(len(X_train))
    cv_splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    best_name   = None
    best_score  = 0.0
    best_model  = None

    results = {}
    for name, clf in candidates.items():
        try:
            scores = cross_val_score(
                clf, X_train_vec, y_train,
                cv=cv_splitter, scoring="accuracy", n_jobs=-1
            )
            mean_score = scores.mean()
            results[name] = {"mean": mean_score, "std": scores.std(), "scores": scores}
            logger.info(f"  {name:<30} CV = {mean_score:.4f} (+/- {scores.std():.4f})")

            if mean_score > best_score:
                best_score = mean_score
                best_name  = name
                best_model = clf
        except Exception as e:
            logger.warning(f"  {name} failed: {e}")

    logger.info(f"\n✅ Best model: {best_name} (CV accuracy: {best_score:.4f})")

    # ── 6. Final Fit on Full Train Set ────────────────────────────────────
    logger.info("\nFitting best model on full training set...")
    best_model.fit(X_train_vec, y_train)

    # ── 7. Evaluation on Hold-Out Test Set ───────────────────────────────
    y_pred = best_model.predict(X_test_vec)
    test_acc = accuracy_score(y_test, y_pred)

    logger.info(f"\nTest Accuracy : {test_acc:.4f}")
    logger.info("\nClassification Report:")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=sorted(VALID_MOODS)))

    # Confusion matrix (compact text version)
    cm = confusion_matrix(y_test, y_pred, labels=sorted(VALID_MOODS))
    logger.info("\nConfusion Matrix (rows=actual, cols=predicted):")
    logger.info(f"  Labels: {sorted(VALID_MOODS)}")
    logger.info(f"\n{cm}")

    # ── 8. Save Artifacts ─────────────────────────────────────────────────
    model_path      = OUTPUT_DIR / "mood_model.pkl"
    vectorizer_path = OUTPUT_DIR / "vectorizer.pkl"
    metadata_path   = OUTPUT_DIR / "model_metadata.json"

    joblib.dump(best_model, model_path,      compress=3)
    joblib.dump(vectorizer, vectorizer_path, compress=3)

    import json
    metadata = {
        "model_name":    best_name,
        "cv_accuracy":   round(best_score, 4),
        "test_accuracy": round(test_acc, 4),
        "train_samples": int(len(X_train)),
        "test_samples":  int(len(X_test)),
        "vocab_size":    len(vectorizer.vocabulary_),
        "moods":         sorted(VALID_MOODS),
        "all_results":   {
            k: {"mean": round(v["mean"], 4), "std": round(v["std"], 4)}
            for k, v in results.items()
        },
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"\nSaved:")
    logger.info(f"  Model      → {model_path}")
    logger.info(f"  Vectorizer → {vectorizer_path}")
    logger.info(f"  Metadata   → {metadata_path}")
    logger.info("\n🎵 Training complete!")

    return best_model, vectorizer


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    train()