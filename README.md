# DeepCine

**Discover films. Build your watchlist. Get recommendations shaped by your taste.**

DeepCine is a full-stack movie discovery and personalized recommendation application. It combines a React frontend, FastAPI backend, PostgreSQL persistence, TMDB movie data, semantic content retrieval, and multiple recommendation signals.

> **Project status:** Active portfolio project. The repository includes the application, offline model-building and evaluation workflows, and automated backend/frontend checks. Production reliability and recommendation quality must be verified against a deployed environment and real user activity; this README does not claim otherwise.

---

## Contents

- [Product overview](#product-overview)
- [Features](#features)
- [Recommendation system](#recommendation-system)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Local setup](#local-setup)
- [API overview](#api-overview)
- [Testing](#testing)
- [Offline evaluation](#offline-evaluation)
- [Deployment](#deployment)
- [Security](#security)
- [Known limitations](#known-limitations)
- [Attribution](#attribution)

## Product overview

DeepCine is designed around a simple user journey:

1. Discover films through trending collections, search, and filters.
2. Open a movie to explore its available details.
3. Save titles to a watchlist, rate films, and build a watch history.
4. Receive recommendations using the signals available from your activity.

The interface includes a cinematic landing page, login and signup, home dashboard, movie collections, search, discovery, movie details, personal library, profile, and AI recommendation views.

## Features

### Discovery and browsing
- Home page with movie discovery sections.
- Movie Collections: **Top Trending**, **Top Rated**, **Upcoming**, and **Recently Added**.
- Search modal with live search and trending suggestions.
- Discover page with genre, language, mood, and sorting controls.
- Movie detail pages with available metadata, cast, trailers, and related discovery.
- TMDB-powered movie metadata and artwork.

### Accounts and personal library
- User registration and login.
- JWT-based API authentication.
- User profile and logout.
- User-specific watch history and search history.
- Movie ratings.
- Watchlist management and a personal library view.

### Personalized recommendations
The recommendation service combines several candidate sources when the required data and artifacts are available:

- Semantic content similarity.
- Implicit-feedback collaborative filtering.
- Explicit preference and genre affinity from ratings and saved titles.
- Popularity-based candidates as a fallback.
- Co-view candidates from distinct user/movie history pairs, ranked by viewer overlap.

Candidate lists are combined using **Reciprocal Rank Fusion (RRF)**. A genre-aware, MMR-style reranking step then trades some rank relevance for variety. Personalization depends on the user's activity and on the availability of the required model/index artifacts.

## Recommendation system

### Candidate generation

| Signal | Implementation | Purpose |
|---|---|---|
| Content-based | SentenceTransformer embeddings + FAISS | Retrieve semantically similar movie candidates |
| Collaborative | Implicit-feedback ALS (implicit) | Use patterns across users' watch-history interactions |
| Explicit preferences | Rating, watchlist, and genre-affinity weights | Reflect positive and negative feedback |
| Popularity | Catalog popularity and vote-average ordering | Provide a fallback candidate source |
| Co-view | Distinct viewer overlap across movie-detail history events | Find catalog movies explored by users with overlapping interests |

The content embedding model is **all-MiniLM-L6-v2**. The generated content artifact set includes:

- movie_embeddings.npy
- movie_ids.npy
- movie_index.faiss
- movie_artifact_manifest.json

The manifest stores model/schema information and SHA-256 hashes. The API validates the artifact set before loading it; partial or mismatched files are rejected.

### Similar-film and co-view discovery

- Movie detail pages expose a dedicated paginated similar-films page backed by TMDB similar-movie results.
- The authenticated `/recommend/co-watch/{user_id}` endpoint finds other users who opened at least one movie in the current user's history, then ranks other catalog movies by cosine-style viewer overlap.
- Repeated detail-page opens by the same viewer for the same movie count once. The endpoint excludes the current user's history, ratings, and watchlist titles, supports a minimum shared-viewer threshold, and returns support counts plus an explanation.
- **Important data limitation:** the existing `watch_history` event is written when a user opens a movie detail page. It measures interest/detail-page views, not confirmed playback or completed watches. The UI therefore describes these as movies users *explored*, not movies they definitely watched.

### Ranking and explanations

1. Generate ranked candidate lists from the available signals.
2. Combine lists with weighted Reciprocal Rank Fusion.
3. Apply genre-aware diversification using an MMR-style objective and Jaccard genre overlap.
4. Return movie results with an explanation based on observed genre matches where available.

The explanation describes matching genres from watched, highly rated, or saved movies. It is not a causal explanation of the recommendation model.

### Collaborative model requirements

ALS training is an offline workflow, not a per-request operation. The current training gate requires at least **5 eligible users**, each with at least **3 distinct watched movies**. These are minimum data eligibility checks, not evidence of a particular recommendation quality.

A newly seeded catalog has no user interaction history. Collect sufficient interactions and train the collaborative model before expecting this signal to contribute.

## Architecture

~~~text
┌───────────────────────────────┐
│          React + Vite         │
│ Landing · Home · Search       │
│ Discover · Movie · Library    │
└───────────────┬───────────────┘
                │ HTTP / JSON + JWT
                ▼
┌───────────────────────────────┐
│            FastAPI            │
│ Auth · Movies · Search        │
│ Watch history · Ratings       │
│ Watchlist · Recommendations   │
│ Admin catalog/index tasks     │
└───────┬───────────┬───────────┘
        │           │
        ▼           ▼
┌─────────────┐  ┌─────────────────────────────┐
│ PostgreSQL  │  │ Recommendation artifacts   │
│ Users       │  │ SentenceTransformer         │
│ Movies      │  │ Embeddings + FAISS index    │
│ Interactions│  │ Implicit ALS model          │
└─────────────┘  └─────────────────────────────┘
        ▲
        │
        ▼
┌───────────────────────────────┐
│ TMDB API                      │
│ Movie metadata and images     │
└───────────────────────────────┘
~~~

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite 8, React Router |
| Styling and UI | Tailwind CSS 4, Framer Motion, Lucide React, Swiper |
| Backend API | Python 3.11.9, FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| Authentication | JWT, bcrypt |
| Content retrieval | SentenceTransformers, FAISS, NumPy |
| Collaborative filtering | implicit ALS, SciPy |
| Movie data | TMDB API |
| Evaluation | MovieLens, pandas, ranking metrics, bootstrap confidence intervals |
| Quality checks | pytest, ESLint, Vite production build |

## Repository structure

~~~text
DeepCineV2/
├── backend/
│   ├── ai/                 # Embeddings, FAISS, ALS, ranking, recommender
│   ├── app/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── schedular/
│   ├── evaluation/
│   ├── tests/
│   ├── evaluate_movielens.py
│   ├── evaluate_recommenders.py
│   ├── generate_embeddings.py
│   ├── import_genres.py
│   ├── import_movies.py
│   ├── link_movie_genres.py
│   ├── train_collaborative_model.py
│   ├── run.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── package-lock.json
├── DEPLOYMENT.md
├── PORTFOLIO_DEMO.md
└── README.md
~~~

## Local setup

### Prerequisites
- Python **3.11.9** (specified in backend/.python-version and backend/runtime.txt).
- Node.js and npm compatible with the Vite version in frontend/package.json.
- PostgreSQL.
- TMDB API credentials for live movie-data features.

There is no root-level Docker Compose file in this repository. Start PostgreSQL separately and make sure the database connection string points to a reachable database.

### 1. Clone the repository

~~~powershell
git clone https://github.com/dolly-bit/DeepCineV2.git
cd DeepCineV2
git switch feature/deepcine-2.0
~~~

### 2. Set up the backend

~~~powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
~~~

Edit backend/.env:

~~~dotenv
DATABASE_URL=postgresql://deepcine:deepcine_dev@127.0.0.1:5433/deepcine
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
TMDB_API_KEY=your_tmdb_api_key
TMDB_ACCESS_TOKEN=your_tmdb_v4_read_access_token
ALLOWED_ORIGINS=http://localhost:5173
ADMIN_TASK_TOKEN=
~~~

The example URL expects PostgreSQL on port **5433**, with a database and role matching the URL. Change it to match your own PostgreSQL setup if needed. Never commit real credentials or your .env file.

### 3. Import catalog data and build content artifacts

With PostgreSQL running, the backend virtual environment active, and TMDB credentials configured, run these commands from backend/:

~~~powershell
python import_genres.py
python import_movies.py
python generate_embeddings.py
~~~

The movie import targets up to 10,000 records. Check the script output to confirm how many were actually imported.

If existing movie records need their genre relationships populated, run:

~~~powershell
python link_movie_genres.py
~~~

Build the collaborative model only after enough watch-history interactions have been collected:

~~~powershell
python train_collaborative_model.py
~~~

See [Collaborative model requirements](#collaborative-model-requirements) for the minimum training-data gate.

### 4. Start the backend API

From backend/:

~~~powershell
python run.py
~~~

By default, the API runs at:

- API root: http://127.0.0.1:8000
- Readiness check: http://127.0.0.1:8000/health
- Liveness check: http://127.0.0.1:8000/health/live
- Interactive API docs: http://127.0.0.1:8000/docs

### 5. Set up and start the frontend

Open a second terminal at the repository root:

~~~powershell
cd frontend
npm ci
Copy-Item .env.example .env
~~~

Set VITE_API_BASE_URL in frontend/.env:

~~~dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
~~~

Start Vite:

~~~powershell
npm run dev
~~~

Open the local URL printed by Vite (normally http://localhost:5173).

## API overview

The FastAPI app registers these route groups:

| Route group | Responsibility |
|---|---|
| /auth | Registration, login, and current-user authentication |
| Movie routes | Catalog browsing, search, discovery, and movie details |
| /recommend | Content, collaborative, personalized, and co-view recommendations |
| Watch-history routes | User watch activity |
| Search-history routes | User search activity |
| Ratings routes | User movie ratings |
| Watchlist routes | Saved movies |
| /admin | Token-protected catalog seeding and content-index refresh |

Use the running Swagger UI at /docs as the authoritative reference for exact paths, parameters, request bodies, and response schemas. User-specific endpoints require a valid bearer token. Admin tasks require the server-side ADMIN_TASK_TOKEN in the X-Admin-Token header.

## Testing

Run backend tests from backend/:

~~~powershell
python -m pytest -q
~~~

Run frontend checks from frontend/:

~~~powershell
npm run lint
npm run build
~~~

These checks cover automated tests, static linting, and frontend compilation. They do not, by themselves, prove that the complete application works with a live database, TMDB credentials, valid model artifacts, or production hosting. Verify those dependencies separately.

## Offline evaluation

The repository includes an offline MovieLens evaluation workflow:

- Runner: backend/evaluate_movielens.py
- Protocol and interpretation: backend/evaluation/MOVIELENS_BENCHMARK.md
- Supporting evaluation: backend/evaluate_recommenders.py

The benchmark maps MovieLens movie IDs to TMDB IDs and evaluates only the catalog intersection. It is an implicit top-N retrieval evaluation—not rating prediction and not an evaluation with DeepCine production users.

When reporting benchmark results, include the dataset/catalog snapshot, split protocol, candidate universe, random seeds, metrics, and uncertainty intervals. Keep validation-based tuning separate from final test evaluation. Do not present offline MovieLens metrics as measured production-user performance.

## Deployment

Deployment instructions are maintained separately:

- [Deployment runbook](./DEPLOYMENT.md) — Vercel frontend, FastAPI hosting, environment variables, production seeding, model artifacts, and release verification.
- [Portfolio demo checklist](./PORTFOLIO_DEMO.md) — user journey, recommendation architecture, engineering evidence, and limitations to disclose.

The frontend and backend are separate deployable services. A successful frontend deployment does not prove the API, database, TMDB integration, or recommendation artifacts are working.

## Security

- Keep .env files and credentials out of version control.
- Generate a long, random, unique SECRET_KEY.
- Set ALLOWED_ORIGINS to the exact trusted frontend origins in production.
- Keep ADMIN_TASK_TOKEN on the backend only. Never expose it through a VITE_ variable.
- Use HTTPS and managed secret storage in production.
- Configure database backups and a tested restore procedure before storing real user data.

## Known limitations

- **Cold start:** new users have limited interaction history, so recommendations may rely more heavily on content, genre, and popularity signals.
- **ALS lifecycle:** collaborative filtering is trained offline. The model must be trained and deployed deliberately as interaction data changes.
- **Artifact lifecycle:** embedding and FAISS files must be rebuilt after catalog changes and persisted or regenerated after deployments that use ephemeral filesystems.
- **Scheduler:** catalog refresh scheduling currently runs inside the API process. Multiple API instances can run duplicate jobs; use a dedicated worker or managed scheduler before scaling horizontally.
- **Database migrations:** application startup currently calls SQLAlchemy create_all. This does not replace a versioned Alembic migration process for production schema changes.
- **External dependency:** live movie data depends on TMDB availability, credentials, and rate limits.
- **Evaluation transfer:** offline MovieLens results do not establish recommendation quality for new DeepCine users.

## Portfolio walkthrough

For a repeatable project demonstration, follow [PORTFOLIO_DEMO.md](./PORTFOLIO_DEMO.md). It covers the user journey, recommendation architecture, engineering evidence, and limitations to disclose.

## Attribution

- Movie metadata and images are provided by [The Movie Database (TMDB)](https://www.themoviedb.org/). DeepCine is an independent project and is not endorsed or certified by TMDB.
- MovieLens datasets are provided by [GroupLens](https://grouplens.org/datasets/movielens/). Follow the dataset's terms of use.

---

**DeepCine is a portfolio engineering project. Its credibility should come from reproducible tests, transparent evaluation, verified end-to-end workflows, and honest disclosure of operational limitations—not feature claims alone.**
