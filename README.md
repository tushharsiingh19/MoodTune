# 🎵 MoodTunes AI

**Emotion-based music recommendation platform.** Type how you feel, and the app classifies your mood with a custom NLP pipeline and recommends matching songs with Spotify and YouTube links.

![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?logo=postgresql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)

**Live demo:** [add-your-link-here](#) &nbsp;|&nbsp; **API docs:** `<your-backend-url>/docs`

> The backend runs on a free Render instance, so the first request after a period of inactivity can take about a minute while it wakes up.

<!-- Add a screenshot or GIF here, for example:
![MoodTunes AI screenshot](docs/screenshot.png)
-->

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
- [Machine Learning](#machine-learning)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Deployment](#deployment)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Mood detection from text** across 8 moods: happy, sad, angry, romantic, relaxed, motivational, party, study, with a confidence score.
- **Song recommendations:** 10 songs per request with album art placeholder, Spotify link and YouTube link.
- **Song catalog browser** with mood tabs, search and pagination (about 290 curated songs).
- **JWT authentication:** register, login, protected routes.
- **Favorites:** save and remove songs, filter by mood.
- **Mood history:** every analysis is saved for logged-in users, with a simple per-mood chart.
- **Resilient song sourcing:** PostgreSQL catalog first, Spotify live search second, static list last.
- **YouTube enrichment** with three query strategies and database caching to stay inside the API quota.
- **Spotify-inspired dark UI** with glassmorphism cards, animations and a mobile-first responsive layout.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS 3, Framer Motion, React Router 6, Axios, react-hot-toast |
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2 |
| Auth | JWT (python-jose), bcrypt via passlib |
| Machine Learning | scikit-learn, NLTK, pandas, NumPy, joblib |
| Database | PostgreSQL (Neon) |
| External APIs | Spotify Web API, YouTube Data API v3 |
| Deployment | Render (frontend and backend), Neon (database), Docker support |

## How It Works

```
User text
   │
   ▼
React (Axios + JWT header) ──► POST /api/recommend
                                   │
                                   ▼
                         NLP pipeline: clean → tokenize → stopwords
                         → lemmatize → TF-IDF → classifier
                                   │
                          mood + confidence
                                   │
          ┌────────────────────────┼─────────────────────────┐
          ▼                        ▼                         ▼
   1. PostgreSQL catalog    2. Spotify search         3. Static fallback
   (primary, fast)          (if DB has no songs)      (last resort)
          │
          ▼
   YouTube link enrichment (cached in the database)
          │
          ▼
   Saved to search history (if logged in) → JSON response → React UI
```

## Machine Learning

### Pipeline

1. **Cleaning:** lowercase, expand contractions, strip URLs, handles and non-letters.
2. **Tokenization** with NLTK.
3. **Stopword removal that keeps negations** (`not`, `never`, `no`), so "not happy" does not look like "happy".
4. **Lemmatization** with WordNet.
5. **TF-IDF** with up to 15,000 features, 1 to 3 n-grams and sublinear term frequency.
6. **Model selection:** Logistic Regression, calibrated LinearSVC and calibrated SGD are compared with 5-fold stratified cross-validation. The best one is saved with joblib. Calibration (Platt scaling) provides the probability used as the confidence score.
7. **Fallback:** if the model files are missing, a keyword matcher keeps the app working.

### Dataset

- A public text dataset of 40,120 rows, cleaned down to 36,651 rows (nulls, very short texts, URLs, mostly non-letter rows, duplicates removed).
- Class-balanced to 15,981 rows by capping the large classes.
- Merged with 240 hand-written examples (30 per mood).
- Stratified 80/20 split: 12,976 training and 3,244 test samples.

### Results

| Model | 5-fold CV accuracy |
|---|---|
| Logistic Regression | 32.1% |
| LinearSVC (calibrated) | **34.3%** |
| SGD Classifier (calibrated) | 33.8% |

**Test accuracy of the selected model: 33.5%** across 8 classes. For reference, random guessing gives 12.5% and always predicting the largest class gives about 18.8%.

> **Why is it this low?** Reading the training rows shows that many labels in the public dataset do not match the mood they are tagged with (for example, a neutral status update labeled "motivational"). All three models land within about two points of each other, which indicates the data, not the model choice, is the limit. See [Roadmap](#roadmap) for the plan to fix this.

Run training and see your own numbers:

```bash
cd backend
python -m app.ml.train_model
```

This writes `ml_models/mood_model.pkl`, `ml_models/vectorizer.pkl` and `ml_models/model_metadata.json`.

## Project Structure

```
moodtunes-ai/
├── backend/
│   ├── app/
│   │   ├── database/        # SQLAlchemy engine and session
│   │   ├── ml/              # mood_detector.py, train_model.py, data.csv
│   │   ├── models/          # ORM models (User, SearchHistory, Favorite, Song)
│   │   ├── routes/          # auth, mood, music, history, favorites
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # spotify_service, youtube_service, song_catalog, song_seeder
│   │   └── utils/           # config (settings) and auth (JWT, bcrypt)
│   ├── ml_models/           # generated .pkl files and metadata (not committed)
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # cards, layout, ui
│   │   ├── context/         # AuthContext
│   │   ├── pages/           # Home, Recommend, Catalog, History, Favorites, Login, Register
│   │   ├── services/        # api.js (Axios instance and API calls)
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11
- Node.js 18 or newer
- A PostgreSQL database (local, or a free [Neon](https://neon.tech) project)
- Optional: Spotify and YouTube API credentials

### 1. Clone

```bash
git clone https://github.com/<your-username>/moodtunes-ai.git
cd moodtunes-ai
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python -c "import nltk; [nltk.download(r) for r in ['punkt','stopwords','wordnet','punkt_tab','omw-1.4']]"

cp .env.example .env        # Windows: copy .env.example .env
# edit .env and fill in your values (see Environment Variables)

python -m app.ml.train_model
uvicorn main:app --reload --port 8000
```

The API is now at `http://localhost:8000` and the interactive docs are at `http://localhost:8000/docs`. Tables are created automatically on startup.

### 3. Seed the song catalog

In a second terminal, with the virtual environment active:

```bash
cd backend
python -m app.services.song_seeder              # insert songs
python -m app.services.song_seeder --youtube    # insert songs and fetch YouTube links
python -m app.services.song_seeder --backfill   # add YouTube links to songs that lack one
```

Check the result at `http://localhost:8000/api/catalog/stats`.

### 4. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env` containing exactly this line (no quotation marks):

```
VITE_API_URL=http://localhost:8000/api
```

```bash
npm run dev
```

Open `http://localhost:5173`.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string. For Neon, end it with `?sslmode=require` |
| `SECRET_KEY` | Long random string used to sign JWTs. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (default `43200`, 30 days) |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | From the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard). Used only for the live-search fallback |
| `YOUTUBE_API_KEY` | From Google Cloud Console with YouTube Data API v3 enabled |
| `ENVIRONMENT`, `DEBUG` | `development` or `production`, and `True` or `False` |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Base URL of the backend API, ending in `/api` |

> Never commit `.env` files or API keys. They are listed in `.gitignore`. If a key is ever exposed, rotate it immediately.

## API Reference

Interactive documentation is available at `/docs` (Swagger UI) and `/redoc`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | No | Create an account and receive a JWT |
| POST | `/api/auth/login` | No | Log in and receive a JWT |
| GET | `/api/auth/me` | Yes | Current user profile |
| PUT | `/api/auth/me` | Yes | Update display name |
| POST | `/api/predict-mood` | Optional | Detect mood from text |
| POST | `/api/recommend` | Optional | Detect mood and return 10 songs |
| GET | `/api/songs/{mood}` | No | Browse the catalog by mood (`limit`, `skip`) |
| GET | `/api/catalog/stats` | No | Song count per mood |
| GET | `/api/youtube/test` | No | Check that the YouTube API key works |
| POST | `/api/admin/songs?mood=` | Yes | Add a song to the catalog |
| GET | `/api/history` | Yes | Search history |
| DELETE | `/api/history/{id}` | Yes | Delete one history entry |
| DELETE | `/api/history` | Yes | Clear all history |
| GET | `/api/favorites` | Yes | List favorites |
| POST | `/api/favorites` | Yes | Add a favorite |
| DELETE | `/api/favorites/{id}` | Yes | Remove a favorite |

Example request:

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"text": "I need to focus on my exam tomorrow"}'
```

Example response (shortened):

```json
{
  "mood": "study",
  "confidence": 0.41,
  "emoji": "📚",
  "description": "Focus mode activated. Here's some music to help you concentrate.",
  "color": "#20B2AA",
  "songs": [
    {
      "song_name": "Clair de Lune",
      "artist": "Claude Debussy",
      "spotify_url": "https://open.spotify.com/track/...",
      "youtube_url": "https://www.youtube.com/watch?v=...",
      "popularity": 74
    }
  ]
}
```

## Database Schema

| Table | Key columns |
|---|---|
| `users` | `id`, `name`, `email` (unique), `hashed_password`, `is_active`, timestamps |
| `search_history` | `id`, `user_id` (FK, cascade), `text`, `mood`, `confidence`, `created_at` |
| `favorites` | `id`, `user_id` (FK, cascade), `song_name`, `artist`, `album`, `spotify_url`, `youtube_url`, `mood` |
| `songs` | `id`, `song_name`, `artist`, `album`, `spotify_id` (unique), `youtube_url`, `popularity`, `mood` (indexed), `genre` |

## Deployment

The project runs on free tiers: **Render** for the frontend and backend, **Neon** for PostgreSQL.

### Backend (Render Web Service)

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt && python -c "import nltk; [nltk.download(r) for r in ['punkt','stopwords','wordnet','punkt_tab','omw-1.4']]" && python -m app.ml.train_model` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

Add the backend environment variables from the table above in the Render dashboard. The training data (`backend/app/ml/data.csv`) must be committed because the model is trained during the build.

### Frontend (Render Static Site)

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Build command | `npm install && npm run build` |
| Publish directory | `dist` |
| Environment variable | `VITE_API_URL=https://<your-backend>.onrender.com/api` |

Add `frontend/public/_redirects` with this line so client-side routes work on refresh:

```
/*    /index.html   200
```

### Database (Neon)

Create a Neon project, copy its connection string into `DATABASE_URL` (keep `?sslmode=require`), then seed the songs from your computer:

```bash
cd backend
# set DATABASE_URL to the Neon string first
python -m app.services.song_seeder
```

### Docker (backend)

```bash
cd backend
docker build -t moodtunes-backend .
docker run -p 8000:8000 --env-file .env moodtunes-backend
```

### Production checklist

- Restrict CORS in `backend/main.py` to your frontend URL instead of `*`.
- Use a strong `SECRET_KEY` and keep `DEBUG=False`.
- Rotate any API key that has ever appeared in logs or commits.
- Confirm `/api/catalog/stats` shows songs for all 8 moods.

## Known Limitations

Being upfront about what this project does not do yet:

- **Low classifier accuracy (33.5% test).** The main cause is inconsistent labels in the public training dataset, not the model.
- **Mood overlap.** Some moods are close (happy and party, relaxed and study), and each text maps to a single mood.
- **English only.** Other languages and mixed-language text are not handled.
- **Catalog quality.** Spotify track IDs were curated by hand and some may need verification. Songs from the database have no album art, so cards show a placeholder.
- **Security tradeoffs.** JWTs are stored in `localStorage` and last 30 days, CORS is open by default, and the admin song route only requires a login, not an admin role.
- **No automated tests, no rate limiting, no database migrations.**
- **Synchronous database calls** inside async routes can block under heavy load.
- **Free-tier hosting** means cold starts of about a minute.

## Roadmap

- [ ] Retrain on a cleanly labeled emotion dataset plus more hand-written examples, and report per-class precision and recall
- [ ] Try a pretrained transformer for emotion detection
- [ ] Return the top 2 or 3 moods instead of one
- [ ] Verify Spotify IDs through the API and store album art
- [ ] Add pytest tests and a GitHub Actions workflow
- [ ] Refresh tokens, rate limiting and an admin role
- [ ] Alembic migrations and async database access
- [ ] User feedback button so people can correct a wrong mood

## Troubleshooting

| Problem | Fix |
|---|---|
| Registration returns 500 with "password cannot be longer than 72 bytes" | Install the pinned version: `pip install bcrypt==4.0.1` |
| Tailwind error "`@apply` should not be used with the `group` utility" | Put `group` on the element in JSX, not inside `@apply` |
| Some moods return no songs | Run `python -m app.services.song_seeder` and check `/api/catalog/stats` |
| Browser shows CORS errors | Check the allowed origins in `backend/main.py` and that `VITE_API_URL` is correct |
| YouTube links missing | Open `/api/youtube/test`. Free quota is about 100 searches per day, so use `--backfill` over several days |
| Neon connection fails | Make sure `DATABASE_URL` ends with `?sslmode=require` |

## License

Released under the MIT License. See `LICENSE` for details.

## Author

**Tushar**, B.Tech Computer Engineering, NIT Kurukshetra.
[GitHub](https://github.com/tushharsiingh19) · [LinkedIn](https://linkedin.com/in/tushharsiingh)
