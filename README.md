# 🎵 MoodTunes AI – Emotion-Based Music Recommendation Platform

> **AI-powered web app** that detects your emotional state from text and recommends music from Spotify, with YouTube links for every track.

![MoodTunes AI](https://img.shields.io/badge/MoodTunes-AI-1DB954?style=for-the-badge&logo=spotify&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)

---
## 👨‍💻 Author

**Tushar Singh**  
B.Tech Computer Science & Engineering (2027)  
National Institute of Technology Kurukshetra (NIT Kurukshetra)

## ✨ Features

- 🧠 **AI Mood Detection** — NLP pipeline (TF-IDF + Logistic Regression) classifies text into 8 moods
- 🎵 **Spotify Integration** — Real-time song recommendations via Spotify Web API
- 📺 **YouTube Links** — Every song linked to YouTube via Data API v3
- 🔐 **JWT Authentication** — Register, login, protected routes
- 📜 **Search History** — All mood checks saved and visualized
- ❤️ **Favorites** — Save songs, filter by mood category
- 📊 **Mood Analytics** — Charts and stats on your emotional patterns
- 🌑 **Dark Spotify-Style UI** — Glassmorphism, animations, fully responsive

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Framer Motion |
| Backend | Python, FastAPI, Uvicorn |
| ML | Scikit-Learn, NLTK, TF-IDF, Logistic Regression |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Auth | JWT (python-jose + bcrypt) |
| APIs | Spotify Web API, YouTube Data API v3 |
| Deployment | Vercel (frontend), Render (backend), Neon (DB) |

---

## 📁 Project Structure

```
moodtunes-ai/
├── backend/
│   ├── app/
│   │   ├── database/       # SQLAlchemy connection
│   │   ├── ml/             # Mood detector + training script
│   │   ├── models/         # ORM models (User, History, Favorites)
│   │   ├── routes/         # FastAPI routers
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Spotify & YouTube service layers
│   │   └── utils/          # Auth (JWT) + Config (Settings)
│   ├── ml_models/          # Trained .pkl files (auto-generated)
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/
    └── src/
        ├── components/     # Reusable UI components
        ├── context/        # AuthContext (global auth state)
        ├── pages/          # All page components
        └── services/       # Axios API layer
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/moodtunes-ai.git](https://github.com/tushharsiingh19/MoodTune.git
cd moodtunes-ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; [nltk.download(r) for r in ['punkt','stopwords','wordnet','punkt_tab']]"

# Train the mood ML model
python -m app.ml.train_model

# Create .env file
cp .env.example .env
# → Fill in your API keys in .env

# Start server
uvicorn main:app --reload --port 8000
```

API docs at: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend
npm install

# Create .env
echo "VITE_API_URL=http://localhost:8000/api" > .env

npm run dev
```

App at: **http://localhost:5173**

---

## 🔑 Environment Variables

### Backend `.env`

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/moodtunes
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

YOUTUBE_API_KEY=your_youtube_api_key
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000/api
```

---

## 🔧 Getting API Keys

### Spotify
1. Go to [developer.spotify.com](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy **Client ID** and **Client Secret**

### YouTube
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Enable **YouTube Data API v3**
3. Create credentials → **API Key**

### PostgreSQL
- **Local**: Install PostgreSQL, create a database named `moodtunes`
- **Cloud**: Use [Neon](https://neon.tech) (free tier available)

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/predict-mood` | Optional | Detect mood from text |
| POST | `/api/recommend` | Optional | Mood detection + song recommendations |
| POST | `/api/auth/register` | — | Create account |
| POST | `/api/auth/login` | — | Login, get JWT |
| GET | `/api/auth/me` | ✅ | Current user profile |
| GET | `/api/history` | ✅ | Search history |
| DELETE | `/api/history/{id}` | ✅ | Delete history entry |
| GET | `/api/favorites` | ✅ | Get saved songs |
| POST | `/api/favorites` | ✅ | Save a song |
| DELETE | `/api/favorites/{id}` | ✅ | Remove a song |

---

## 🤖 ML Pipeline

```
User Text
    ↓
Text Cleaning (lowercase, remove special chars)
    ↓
Tokenization (NLTK word_tokenize)
    ↓
Stopword Removal
    ↓
Lemmatization (WordNetLemmatizer)
    ↓
TF-IDF Vectorization (5000 features, bigrams)
    ↓
Logistic Regression Classifier
    ↓
Mood + Confidence Score
```

**Supported Moods:** Happy · Sad · Angry · Romantic · Relaxed · Motivational · Party · Study

---

## 🚢 Deployment

### Frontend → Vercel
```bash
cd frontend
npm run build
# Deploy dist/ folder to Vercel
# Set VITE_API_URL to your Render backend URL
```

### Backend → Render
1. Push backend to GitHub
2. Create a new Web Service on [render.com](https://render.com)
3. Set build command: `pip install -r requirements.txt && python -m app.ml.train_model`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables

### Database → Neon
1. Create a free project at [neon.tech](https://neon.tech)
2. Copy the connection string to `DATABASE_URL`


