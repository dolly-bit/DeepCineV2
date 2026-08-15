# 🎬 DeepCine

A personalized movie recommendation system that actually explains itself:
content-based matching, collaborative filtering, and watch-history-driven
suggestions, all visible in the UI rather than hidden behind the scenes.

Built with **FastAPI + PostgreSQL** on the backend and **React + Vite +
Tailwind v4** on the frontend, backed by TMDB for movie data.

---

## ✨ Features

- **Personalized recommendations** — a blend of content similarity
  (sentence-transformer embeddings + FAISS) and genre affinity, learned
  from what you actually watch
- **Collaborative filtering** — an ALS matrix-factorization model
  (`implicit`) trained on cross-user watch history, surfaced as "Viewers
  Like You Also Watched"
- **Watch history & search history** — every movie you open and every
  search you make feeds back into your recommendations
- **Auto-updating catalog** — a daily background job re-imports TMDB's
  popular list (up to 500 movies), refreshes ratings on existing movies,
  and rebuilds the recommendation index automatically
- **Full auth flow** — JWT-based register/login, a real `/auth/me`
  validation endpoint, and a profile page with logout
- **Trending / Top Rated / Upcoming** browsing, live search, movie
  details with cast, trailer, and similar movies

---

## 🧱 Tech stack

**Backend**
- FastAPI (async) + SQLAlchemy + PostgreSQL (SQLite for local dev)
- JWT auth (`python-jose`) with `bcrypt` password hashing
- `sentence-transformers` (MiniLM) + `faiss-cpu` for content-based recs
- `implicit` (ALS) for collaborative filtering
- `httpx` for async TMDB API calls with in-memory TTL caching
- `APScheduler` for the daily catalog auto-update job

**Frontend**
- React 18 + Vite
- Tailwind CSS v4 (`@tailwindcss/vite`, theme defined via `@theme` in `index.css`)
- React Router, Axios, Framer Motion, `lucide-react` icons

---

## 📁 Project structure

```
DeepCine/
├── backend/
│   ├── app/
│   │   ├── auth/            # JWT handling, password hashing, get_current_user
│   │   ├── core/             # Settings (env vars)
│   │   ├── database/        # SQLAlchemy engine/session
│   │   ├── models/           # User, Movie, Genre, WatchHistory, SearchHistory
│   │   ├── routes/           # auth, movies, recommend, watch-history, search-history
│   │   ├── schedular/        # Daily auto-update job (APScheduler)
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── services/         # TMDB client + AI recommendation orchestration
│   │   └── main.py           # App entrypoint, CORS, startup/shutdown hooks
│   ├── ai/                   # Embeddings, FAISS index, collaborative model
│   ├── import_movies.py      # Seed script: import up to 500 movies from TMDB
│   ├── import_genres.py      # Seed script: import genre list
│   ├── link_movie_genres.py  # Seed script: link movies <-> genres
│   ├── generate_embeddings.py # Build the content-recommendation index
│   ├── train_collaborative_model.py # Train the ALS collaborative model
│   └── run.py                 # Local dev entrypoint (uvicorn)
└── frontend/
    └── src/
        ├── components/        # Navbar, MovieCard, RecommendationSection, etc.
        ├── pages/              # Home, MovieDetails, Login, Signup, Profile, etc.
        └── services/           # api.js, auth.js, movies.js
```

---

## 🚀 Getting started

### Run it locally
See **[RUN_LOCALLY.md](./RUN_LOCALLY.md)** for full step-by-step setup
(Python venv, TMDB keys, seeding the database, starting both servers).

Quick version:
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
python import_movies.py
python import_genres.py
python link_movie_genres.py
python generate_embeddings.py
python run.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Deploy it
See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for a full Render (backend) +
Vercel (frontend) deployment walkthrough, including the operational
gotchas around ephemeral disk and free-tier sleep that affect the
auto-update job.

---

## 🔑 Environment variables

**`backend/.env`** (see `backend/.env.example`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL (prod) or SQLite (local) connection string |
| `SECRET_KEY` | Random secret for signing JWTs |
| `ALGORITHM` | JWT algorithm, `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry window |
| `TMDB_API_KEY` | TMDB v3 API key |
| `TMDB_ACCESS_TOKEN` | TMDB v4 **Read Access Token** (long token — not the short API key) |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins for CORS (defaults to `*`) |

**`frontend/.env`** (see `frontend/.env.example`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | URL of the running backend, no trailing slash |

---

## 🧠 How the recommendations actually work

1. **Content-based** (`/recommend/content`) — every movie's title +
   overview is embedded with a sentence-transformer model, indexed in
   FAISS, and queried by nearest-neighbor similarity.
2. **Collaborative filtering** (`/recommend/collaborative/{user_id}`) —
   an ALS matrix-factorization model is trained offline
   (`train_collaborative_model.py`) on the watch-history table across
   all users, then queried per-user at request time.
3. **Personalized** (`/recommend/personalized/{user_id}`) — blends the
   above with the user's genre-watch affinity.
4. **Auto-refresh** — a daily job (`app/schedular/`) re-imports TMDB's
   popular list, updates existing movies' stats, and rebuilds the FAISS
   index so new movies become recommendable without a manual step.

---

## 📖 API reference (key endpoints)

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Log in, returns a JWT |
| `GET` | `/auth/me` | Validate token, return current user |
| `GET` | `/movies/trending` | TMDB trending this week |
| `GET` | `/movies/top-rated` | TMDB top rated |
| `GET` | `/movies/upcoming` | Upcoming releases |
| `GET` | `/movies/search?query=` | Search TMDB |
| `GET` | `/movies/{id}` | Movie details |
| `GET` | `/movies/{id}/cast` | Cast list |
| `GET` | `/movies/{id}/similar` | Similar movies |
| `GET` | `/movies/{id}/trailer` | YouTube trailer link |
| `GET` | `/recommend/content?movie_name=` | Content-based recommendations |
| `GET` | `/recommend/collaborative/{user_id}` | Collaborative-filtering recommendations |
| `GET` | `/recommend/personalized/{user_id}` | Blended personalized recommendations |
| `POST` | `/watch-history/` | Record a watched movie |
| `POST` | `/search-history/` | Record a search |

Full interactive docs are available at `/docs` (Swagger UI) on any
running instance.

---

## 📝 Changelog

See **[CHANGES.md](./CHANGES.md)** for a detailed history of bug fixes
and improvements made during development (performance fixes, auth
hardening, design-system consolidation, etc.).

---

## ⚠️ Known limitations

- Free-tier hosting (Render free web services) sleeps after inactivity,
  which can prevent the daily auto-update job from firing reliably —
  see `DEPLOYMENT.md` for workarounds.
- The FAISS index and embeddings are stored on local disk, not in the
  database — on ephemeral hosting they need regenerating after a
  redeploy unless a persistent disk is attached.
- Collaborative filtering needs a meaningful amount of cross-user watch
  history to produce good results; on a fresh install it may return
  nothing until enough usage accumulates.