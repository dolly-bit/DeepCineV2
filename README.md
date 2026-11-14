# DeepCine

**A full-stack movie discovery and personalized recommendation platform.**

DeepCine combines TMDB-powered movie discovery with user-specific recommendation signals. It uses a React + Vite frontend, FastAPI backend, PostgreSQL persistence, semantic content retrieval, implicit-feedback collaborative filtering, genre affinity, popularity signals, and reciprocal rank fusion (RRF).

> **Project status:** Active portfolio project. The repository includes the application, offline recommendation training/evaluation workflows, and backend tests. A successful local build or offline benchmark does not by itself establish production reliability or recommendation quality for real users.

## Features

### Movie discovery
- Home dashboard with trending, top-rated, and upcoming movies.
- Movie Collections with **Top Trending**, **Top Rated**, **Upcoming**, and **Recently Added** sections.
- Search modal with trending suggestions, live search, and personalized-pick navigation.
- Discover page with genre, language, mood, and sort filters.
- Movie details including metadata, cast, trailers, and related discovery.
- TMDB-backed movie catalog, metadata, and images.

### Accounts and personal library
- Registration and login with JWT-backed authentication.
- Account profile and logout.
- Watch history and search history for signed-in users.
- Personal ratings and watchlist management.
- Library page for personal movie activity.

### Recommendation system
- **Content-based retrieval:** SentenceTransformer embeddings indexed with FAISS.
- **Collaborative filtering:** offline Alternating Least Squares (ALS) trained from implicit watch-history interactions.
- **Genre affinity:** candidates derived from genres associated with a user's activity and feedback.
- **Popularity fallback:** a candidate ranking signal when personal signals are limited.
- **Rank fusion:** reciprocal rank fusion combines ranked candidate lists without assuming their raw scores are directly comparable.

The collaborative model is trained offline; it is not retrained on every API request. Personalization depends on user interactions, catalog coverage, and the availability of model/index artifacts. New or low-activity accounts may receive weaker recommendations.

## Architecture

```text
React + Vite
    | HTTP / JSON + JWT
    v
FastAPI application
    |-- Authentication and account routes
    |-- TMDB movie, search, discovery, and detail routes
    |-- Watch history and search history
    |-- Ratings and watchlist
    |-- Recommendation orchestration
    |
    +--> PostgreSQL
    +--> SentenceTransformers -> embeddings -> FAISS index
    +--> implicit ALS -> collaborative model artifact
    +--> TMDB API -> movie metadata and images
```

### Recommendation flow
1. Retrieve content-similar candidates from the embedding index.
2. Retrieve collaborative candidates when a trained ALS artifact and sufficient interaction data are available.
3. Derive genre-affinity candidates from the user's recorded activity.
4. Add a popularity-based candidate list as a fallback signal.
5. Fuse ranked lists with reciprocal rank fusion.
6. Apply the recommendation service's exclusion rules to previously consumed items.

The production recommendation service is implemented in `backend/app/services/ai_recommendation_services.py` and `backend/ai/`. The offline MovieLens benchmark is a separate evaluation workflow; its metrics must not be presented as measured production-user performance.

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | React 19, Vite 8, React Router, Tailwind CSS 4 |
| UI | Framer Motion, Lucide React, Swiper, React Fast Marquee |
| API | Python 3.11.9, FastAPI, Pydantic, Uvicorn |
| Persistence | PostgreSQL, SQLAlchemy, Alembic |
| Authentication | JWT, bcrypt |
| Content retrieval | SentenceTransformers, FAISS, NumPy |
| Collaborative filtering | `implicit` ALS, SciPy sparse matrices |
| Movie metadata | The Movie Database (TMDB) API |
| Evaluation | MovieLens, pandas, ranking metrics, bootstrap confidence intervals |
| Quality checks | pytest, ESLint, Vite production build |

## Repository structure

```text
DeepCineV2/
├── backend/
│   ├── ai/                    # Embeddings, FAISS, ALS, ranking, recommender
│   ├── app/
│   │   ├── auth/              # JWT and password helpers
│   │   ├── core/              # Application configuration
│   │   ├── database/          # SQLAlchemy engine and session
│   │   ├── models/            # User, movie, feedback and library models
│   │   ├── routes/            # FastAPI route modules
│   │   ├── services/          # TMDB and recommendation services
│   │   └── schedular/         # Catalog refresh scheduler
│   ├── evaluation/            # MovieLens benchmark protocol
│   ├── tests/                 # Backend and ranking/evaluation tests
│   ├── evaluate_movielens.py  # Offline MovieLens benchmark
│   ├── evaluate_recommenders.py
│   ├── import_movies.py       # TMDB catalog import (target: 10,000)
│   ├── import_genres.py
│   ├── generate_embeddings.py # Build content retrieval artifacts
│   ├── train_collaborative_model.py
│   ├── run.py                 # API entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/             # Landing, Home, Discover, Library, Profile, etc.
│   │   └── services/          # API clients
│   └── package.json
├── PORTFOLIO_DEMO.md
└── README.md
```

## Local setup

### Prerequisites
- Python **3.11.9** (pinned in `backend/.python-version`).
- Node.js compatible with the Vite version in `frontend/package.json`.
- PostgreSQL, unless you intentionally configure another supported SQLAlchemy database URL for development.
- TMDB API credentials for live movie metadata features.

### 1. Configure the backend

From PowerShell at the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env`. The checked-in example uses PostgreSQL on port **5433**:

```dotenv
DATABASE_URL=postgresql://deepcine:deepcine_dev@127.0.0.1:5433/deepcine
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
TMDB_API_KEY=your_tmdb_api_key
TMDB_ACCESS_TOKEN=your_tmdb_v4_read_access_token
ALLOWED_ORIGINS=http://localhost:5173
ADMIN_TASK_TOKEN=
```

Create the PostgreSQL database and role to match the URL, or change the URL to match your local PostgreSQL configuration. Never commit real credentials or `.env`.

### 2. Import catalog data and build recommendation artifacts

With the backend virtual environment active and the database configured:

```powershell
python import_genres.py
python import_movies.py
python generate_embeddings.py
```

The catalog import targets up to **10,000** TMDB movies. It reports whether the target was reached; rerun if the import is incomplete. Rebuild the embedding/index artifacts after changing the local movie catalog.

For older catalog records that do not have movie-genre relationships, run:

```powershell
python link_movie_genres.py
```

Collaborative filtering requires watch-history interactions. After interactions have been collected, train the model:

```powershell
python train_collaborative_model.py
```

This creates a collaborative model artifact under the backend directory. A fresh database with no interactions or trained artifact cannot provide meaningful collaborative recommendations.

### 3. Start the backend

From the `backend` directory:

```powershell
python run.py
```

The API listens on `http://127.0.0.1:8000` by default.
- Liveness: `http://127.0.0.1:8000/health/live` (legacy `/health` remains supported).
- Readiness: `http://127.0.0.1:8000/health/ready` (returns HTTP 503 when the database is unavailable).
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 4. Configure and start the frontend

Open a second PowerShell terminal at the repository root:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
```

Set the frontend environment variable:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start Vite:

```powershell
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`).

## API areas

The FastAPI application registers route groups for authentication, movie browsing/search/discovery/details, recommendations, watch history, search history, ratings, watchlist, and admin catalog/index tasks. Use `/docs` on a running backend as the authoritative runtime endpoint reference. Protected routes require authentication, and user-scoped routes enforce access to the current user's data.

## Tests and quality checks

Run backend tests from the `backend` directory:

```powershell
python -m pytest -q
```

Run frontend checks from the `frontend` directory:

```powershell
npm run lint
npm run build
```

A passing test suite, lint run, or production build does not verify the complete application. Separately test database connectivity, TMDB credentials and rate limits, authentication, watchlist/rating persistence, recommendation behavior, and deployment configuration.

## Offline MovieLens evaluation

The repository includes a separate MovieLens evaluation pipeline:
- Runner: `backend/evaluate_movielens.py`
- Protocol and interpretation: `backend/evaluation/MOVIELENS_BENCHMARK.md`
- Supporting recommender evaluation: `backend/evaluate_recommenders.py`

The benchmark maps MovieLens movie IDs to TMDB IDs and evaluates only the catalog intersection. It is an implicit top-N retrieval evaluation, not rating prediction and not an evaluation with DeepCine production users. Catalog overlap changes when the imported catalog changes; rerun the overlap diagnostic and benchmark instead of treating an old overlap count as permanent.

When reporting results, include the dataset/catalog snapshot, split protocol, candidate universe, random seeds, metrics, and uncertainty intervals. Keep validation-based tuning separate from final test evaluation; do not cherry-pick favorable seeds.

## Configuration and security
- Keep backend and frontend environment files out of Git.
- Use a long, random, unique `SECRET_KEY`.
- Set `ALLOWED_ORIGINS` to explicit trusted frontend origins in deployed environments.
- Keep `ADMIN_TASK_TOKEN` server-side; never expose it in Vite variables or browser code.
- Use HTTPS and managed secret storage in production.
- Define database permissions and backup/restore procedures before storing real user data.

## Known limitations and engineering work
- **Cold start:** personalized and collaborative recommendations are constrained by limited user interactions.
- **Model lifecycle:** collaborative training is offline; retrain and deploy the model deliberately as interaction data changes.
- **Index lifecycle:** embedding/FAISS artifacts must be rebuilt after catalog changes and persisted or regenerated in ephemeral hosting.
- **Scheduler deployment:** the catalog scheduler runs inside the API process. Multiple API workers or replicas can trigger duplicate jobs; a dedicated worker/scheduler is preferable for multi-instance deployments.
- **Database migrations:** schema changes are versioned with Alembic. Fresh databases run `alembic upgrade head`; databases created before Alembic must be backed up, schema-checked, and baselined with `alembic stamp 0001_initial_schema` before applying future migrations. See [backend/MIGRATIONS.md](./backend/MIGRATIONS.md).
- **External dependency:** live catalog and movie-detail features depend on TMDB availability, credentials, and rate limits.
- **Evaluation transfer:** offline MovieLens results do not establish recommendation performance for new DeepCine users.

## Portfolio walkthrough

Use [PORTFOLIO_DEMO.md](./PORTFOLIO_DEMO.md) for a repeatable demonstration checklist, validation steps, and evidence to capture. Do not claim a workflow, deployment, benchmark, or quality check passed unless it has been run and verified in the target environment.

## Attribution

Movie metadata and images are provided by [The Movie Database (TMDB)](https://www.themoviedb.org/). DeepCine is an independent project and is not endorsed or certified by TMDB. MovieLens data is provided by [GroupLens](https://grouplens.org/datasets/movielens/); follow the dataset's terms of use.

---

**DeepCine is a portfolio engineering project. Its credibility should come from reproducible tests, transparent offline evaluation, verified end-to-end workflows, and honest disclosure of operational limitations—not feature claims alone.**
