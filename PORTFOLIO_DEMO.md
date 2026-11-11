# DeepCine — portfolio demo checklist

Use this checklist for a live walkthrough. Do not claim a step passed until you have performed it on the target machine.

## 1. Start the system

- Start PostgreSQL and confirm the configured database is reachable.
- Start the FastAPI backend and open `/health`.
- Open `/docs` and confirm the expected routers are registered.
- Start the Vite frontend and verify it can call the backend.

## 2. Demonstrate the user journey

1. Register a new account.
2. Log in and confirm the JWT-backed session is retained.
3. Browse trending and top-rated movies.
4. Search for a title and open its details.
5. Add a catalog movie to the watchlist and remove it.
6. Submit a 1–5 star rating and retrieve the user's ratings.
7. Open a movie detail page and verify whether watch history is recorded.
8. Visit personalized recommendations and explain the candidate sources.
9. Log out; verify protected pages redirect to login.

## 3. Explain the recommendation architecture

- Content: sentence embeddings and FAISS nearest-neighbor retrieval.
- Collaborative: offline implicit ALS model.
- Genre affinity: preference derived from recorded watch history.
- Popularity: fallback ranking signal.
- Fusion: reciprocal rank fusion combines ranked candidate lists.

Be precise: the production API's personalized endpoint uses the current catalog and user's history. The offline MovieLens benchmark is a separate evaluation pipeline with its own candidate overlap and split protocol.

## 4. Show engineering evidence

- Backend automated tests: `cd backend; python -m pytest -q`.
- Frontend static checks: `cd frontend; npm run lint`.
- Frontend production build: `cd frontend; npm run build`.
- MovieLens evaluation methodology: `backend/evaluation/MOVIELENS_BENCHMARK.md`.
- Include the exact benchmark output file and run seeds when discussing metrics.

## 5. Disclose limitations

- The MovieLens candidate set is restricted to the intersection with the current DeepCine catalog.
- MovieLens users are not production users; transfer to a new deployment is not established.
- Collaborative quality depends on sufficient interaction history and a trained model artifact.
- Filesystem model/index assets need persistent storage or a regeneration process in ephemeral hosting.
- The in-process scheduler is not a safe multi-replica job orchestration strategy.
- SQLAlchemy `create_all` is not a substitute for production Alembic migrations.

## Evidence to capture

- Home/discovery page.
- Movie details page.
- Watchlist and rating flow.
- Personalized recommendations page.
- Swagger UI with health/auth/recommendation endpoints.
- Terminal output for backend tests, frontend lint, and production build.
- Benchmark JSON/CSV and its exact configuration.
