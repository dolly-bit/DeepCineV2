# DeepCine

**An explainable, full-stack movie discovery and recommendation system.**

DeepCine combines semantic content retrieval, implicit-feedback collaborative filtering, genre affinity, and popularity ranking in a FastAPI + PostgreSQL backend with a React + Vite frontend.

> **Project status:** Active portfolio project. The application includes browsing, authentication, watch history, ratings, watchlist, and recommendation endpoints. The MovieLens benchmark is an offline research evaluation; it is not evidence that the deployed application has the same ranking quality. See [the benchmark protocol](backend/evaluation/MOVIELENS_BENCHMARK.md).

## Product capabilities

- Browse trending, top-rated, upcoming, and discoverable movies through TMDB.
- Search movie titles and open movie details, cast, trailers, and similar titles.
- Register and log in with JWT-backed authentication.
- Record watch history and search history for signed-in users.
- Save personal ratings and a watchlist.
- Generate content-based recommendations using SentenceTransformer embeddings and FAISS.
- Generate collaborative recommendations using an ALS model trained offline.
- Blend content, collaborative, genre-affinity, and popularity rankings with reciprocal rank fusion (RRF).
- Refresh the local catalog and content index through a scheduled TMDB update job; an admin endpoint can trigger seeding/index refresh when configured.

## Architecture

```text
React + Vite
    |
    | HTTP + JWT
    v
FastAPI application
    |-- Auth and user endpoints
    |-- TMDB browsing/search endpoints
    |-- Watch history, ratings, watchlist
    |-- Recommendation orchestration
    |
    +--> PostgreSQL (users, movies, genres, feedback)
    +--> SentenceTransformers -> embeddings -> FAISS
    +--> implicit ALS model (offline training)
    +--> TMDB API
```

### Recommendation pipeline

1. **Content retrieval:** movie metadata is encoded into sentence embeddings and indexed with FAISS.
2. **Collaborative retrieval:** an implicit ALS model learns user/movie interaction factors from available watch-history interactions.
3. **Genre affinity:** genres associated with a user's watched movies produce a ranked candidate list.
4. **Popularity:** catalog popularity and vote average provide a fallback candidate ranking.
5. **Fusion:** reciprocal rank fusion combines ranked lists without assuming their raw scores share a common scale. Watched titles are excluded from the personalized candidate lists.

The collaborative model is trained offline. It does not retrain on every request. A fresh installation with little user feedback may have limited personalized/collaborative signal.

## Technology

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite 8, React Router, Tailwind CSS 4, Axios, Framer Motion |
| API | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL (SQLite supported by the connection layer for local development) |
| Content retrieval | SentenceTransformers, FAISS, NumPy |
| Collaborative filtering | implicit ALS |
| External metadata | TMDB API |
| Evaluation | MovieLens, pandas, ranking metrics, user-level bootstrap confidence intervals |

## Repository layout

- `backend/app/`: API routes, models, authentication, database, TMDB services, scheduler.
- `backend/ai/`: embedding, FAISS, collaborative filtering, ranking, and recommendation logic.
- `backend/tests/`: automated backend and evaluation tests.
- `backend/evaluate_movielens.py`: offline MovieLens benchmark.
- `backend/evaluation/`: benchmark methodology and interpretation.
- `frontend/src/`: React pages, components, and API clients.

## Run locally

### Prerequisites

- Python version specified by `backend/.python-version`.
- Node.js compatible with Vite 8.
- PostgreSQL (or SQLite for a lightweight backend development setup).
- TMDB API credentials for live movie catalog functionality.

### Backend

From PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env` and replace the placeholders (never commit the real `.env`):

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/deepcine
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
TMDB_API_KEY=your_tmdb_api_key
TMDB_ACCESS_TOKEN=your_tmdb_v4_read_access_token
ALLOWED_ORIGINS=http://localhost:5173
ADMIN_TASK_TOKEN=
```

The database must be created before starting the API. Then seed the catalog and build the content index:

```powershell
python import_movies.py
python import_genres.py
python link_movie_genres.py
python generate_embeddings.py
python run.py
```

The API is served at `http://127.0.0.1:8000`; interactive OpenAPI docs are at `http://127.0.0.1:8000/docs`.

Train the collaborative model after collecting suitable watch-history interactions:

```powershell
python train_collaborative_model.py
```

### Frontend

In a second PowerShell terminal:

```powershell
cd frontend
npm ci
```

Copy `frontend/.env.example` to `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```powershell
npm run dev
```

Vite prints the local frontend URL (normally `http://localhost:5173`).

## Tests and quality checks

Backend:

```powershell
cd backend
python -m pytest -q
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

A passing test suite does not prove the external TMDB integration, database migrations, production deployment, or recommendation quality. Verify those separately in the target environment.

## Offline recommendation evaluation

The MovieLens evaluation is intentionally separate from production user history. It maps MovieLens movie IDs to TMDB IDs and evaluates only the catalog overlap. The current catalog/benchmark overlap has previously been measured at 197 of 414 catalog movies (47.6%); rerun the diagnostic after changing the catalog.

See [MovieLens benchmark protocol](backend/evaluation/MOVIELENS_BENCHMARK.md) for the Phase 5 split, validation-only tuning, independent cohort seeds, bootstrap intervals, run command, and limitations.

Important interpretation limits:
- The benchmark's candidate universe is the MovieLens/DeepCine overlap, not every movie in the catalog.
- The evaluation is implicit top-N retrieval, not rating prediction.
- MovieLens users are not DeepCine production users; results may not transfer to a new deployment.
- Validation-selected weights must remain frozen before test evaluation.
- Report the exact run configuration and uncertainty; do not cherry-pick random seeds.

## Configuration and security notes

- Keep `.env`, API credentials, database passwords, and admin tokens out of Git.
- Set `ALLOWED_ORIGINS` to explicit frontend origins in production; do not leave wildcard CORS as a production default.
- Set a strong, unique `SECRET_KEY` and `ADMIN_TASK_TOKEN` where admin tasks are enabled.
- Use HTTPS and managed secrets in deployment. Do not expose admin tokens in frontend code.

## Known limitations

- Recommendation quality depends on catalog coverage and real user feedback. Collaborative filtering is weak on a cold-start installation.
- The benchmark has a limited catalog intersection and cannot establish production-user performance.
- FAISS/embedding/model artifacts are filesystem assets. Ephemeral hosting can discard them unless they are regenerated or stored on persistent storage.
- The scheduler runs inside the API process. Multiple API workers/replicas can schedule duplicate jobs; use a dedicated worker/scheduler for a multi-instance deployment.
- Startup currently creates missing tables with SQLAlchemy metadata. A production deployment should use versioned Alembic migrations rather than relying on `create_all`.
- External TMDB availability, rate limits, credentials, and hosting sleep affect live catalog features.

## Portfolio walkthrough\n\nUse [PORTFOLIO_DEMO.md](./PORTFOLIO_DEMO.md) as a repeatable live-demo checklist and evidence-capture guide.\n\n## Attribution

Movie metadata and images are provided by [The Movie Database (TMDB)](https://www.themoviedb.org/). DeepCine is an independent project and is not endorsed or certified by TMDB. MovieLens data is provided by [GroupLens](https://grouplens.org/datasets/movielens/); follow the dataset's terms of use.

---

**DeepCine is a portfolio engineering project, not a claim of production readiness.** Its strongest evidence is reproducible evaluation, working end-to-end user flows, tests, deployment verification, and clear disclosure of limitations.
