# MoodTunes AI - Bug Hunt and Learning Notes

## Already fixed in this copy
1. Anonymous users got 401 on /predict-mood and /recommend (get_current_user requires a token). Now get_optional_user + OAuth2PasswordBearer(auto_error=False).
2. Seeder crashed with UniqueViolation when one spotify_id appeared twice in the catalog. Now skips IDs repeated in the same run (a song that sits in two moods is stored once).
3. HomePage.jsx had an apostrophe inside a single-quoted string (syntax error).

## Bugs and weak spots for you to find and fix
- song_catalog.py: Spotify IDs were typed by hand. Verify each against the Spotify API (GET /v1/tracks?ids=...) and drop wrong ones.
- DB songs have album_image = None, so cards show a placeholder. Fetch images from Spotify with the track ids and store them.
- async def routes call the synchronous SQLAlchemy session, which blocks the event loop. Use def routes or async SQLAlchemy.
- MoodInput picks a random placeholder on every render, so it changes while typing. Use useState/useMemo.
- HomePage has an unused loading state.
- auth.py: passlib 1.7.4 can misbehave with bcrypt >= 4.1. Pin bcrypt==4.0.1 if you see a version warning.
- train_model.py: LogisticRegression(multi_class=...) is deprecated in newer scikit-learn. Remove the argument if your version complains.
- update_profile takes name as a query parameter; use a JSON body schema.
- POST /admin/songs only needs a login, not an admin role.
- CORS is allow_origins=["*"]; restrict to your frontend URL in production.
- JWT lives in localStorage (XSS risk) and lasts 30 days. Consider short expiry plus refresh tokens.
- No tests, no Alembic migrations, no rate limiting.
- Songs that appear in two moods are stored under only the first one.

## Suggested reading order
backend/main.py -> utils/config.py -> database/connection.py -> models/models.py -> schemas/schemas.py -> utils/auth.py -> routes/* -> ml/mood_detector.py -> ml/train_model.py -> services/* -> frontend/src/main.jsx -> App.jsx -> services/api.js -> context/AuthContext.jsx -> pages/* -> components/*
