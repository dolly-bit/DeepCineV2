# DeepCine deployment runbook

This repository's frontend is a Vite SPA and the backend is a FastAPI service. The frontend can be deployed on Vercel; the API needs a persistent PostgreSQL database and a Python host such as Render.

## 1. Deploy the frontend on Vercel

1. Import the GitHub repository `dolly-bit/DeepCineV2` into Vercel, or use the existing Vercel project.
2. Set the production branch to `main`.
3. Set **Root Directory** to `frontend`.
4. Build command: `npm run build`.
5. Output directory: `dist`.
6. Add environment variable `VITE_API_BASE_URL` with the public HTTPS URL of the deployed FastAPI service (no trailing slash).
7. Redeploy after changing the environment variable. Vite embeds this value at build time.

The frontend deployment does not include the backend or database. A successful Vercel build alone does not mean API requests work.

## 2. Deploy the API and PostgreSQL

Create a Python 3.11.9 web service and a managed PostgreSQL database on your chosen host. The repository's `docker-compose.yml` is for local development only; it is not a production database host. A PostgreSQL container running on your laptop is not reachable by Render and should never be used as Render's production `DATABASE_URL`.

For Render:
- Repository: `dolly-bit/DeepCineV2`
- Branch: `main`
- Root directory: `backend`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `python run.py`
- Health check path: `/health`
- Use one API instance initially. The in-process APScheduler is not protected by a distributed lock; multiple instances can run duplicate catalog refresh jobs.

Set these backend environment variables in the host dashboard:

| Key | Value |
|---|---|
| `DATABASE_URL` | Managed PostgreSQL connection string |
| `SECRET_KEY` | Long random secret; never reuse the example value |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `TMDB_API_KEY` | Your TMDB API key |
| `TMDB_ACCESS_TOKEN` | Your TMDB API Read Access Token |
| `ALLOWED_ORIGINS` | Exact Vercel production origin, e.g. `https://deepcine-v2.vercel.app` |
| `ADMIN_TASK_TOKEN` | Long random operator-only secret |

Do not put backend secrets in Vercel variables prefixed with `VITE_`; Vite variables are public in the browser bundle. Keep `ADMIN_TASK_TOKEN` private.

## 3. Seed the production catalog and content index

The database starts with tables but no movie catalog. After the API is healthy and TMDB credentials are configured:

1. Generate a long random `ADMIN_TASK_TOKEN` and set it in the API host environment.
2. Redeploy/restart the API so the setting is loaded.
3. Call `POST /admin/seed` with the same value in the `X-Admin-Token` header.
4. Confirm the response reports successful catalog import and `movies_indexed` greater than zero.
5. Check the home, search, detail, and recommendation routes against the public API.

Example PowerShell:

```powershell
$api = "https://YOUR-API-HOST"
$token = "YOUR_ADMIN_TASK_TOKEN"
Invoke-RestMethod -Method Post -Uri "$api/admin/seed" -Headers @{
  "X-Admin-Token" = $token
}
```

The seed operation can take several minutes and may exceed request timeouts or memory limits on small instances. If it fails, use the host's shell/console to run `python import_genres.py`, `python import_movies.py`, then `python generate_embeddings.py` from the backend directory. Do not repeatedly retry a timed-out seed request without checking the database and index first.

The content index and ALS model artifacts live on the service filesystem. Many hosts use ephemeral filesystems, so they can disappear on redeploy/restart. Persist the artifacts on a mounted persistent disk or rebuild them after deployment. The admin endpoint `POST /admin/refresh-index` rebuilds the content index from the database; it does not train ALS.

## 4. Collaborative filtering

A newly seeded catalog does not contain user interactions, so collaborative filtering will not immediately provide meaningful recommendations.

Collect watch-history events from multiple independent users first. Then run `python train_collaborative_model.py` in the backend environment. Training requires at least five users with at least three distinct watched movies each. Persist both `cf_model.pkl` and `cf_model_manifest.json` together; the manifest verifies the model artifact.

Until enough interaction data exists, content, genre-affinity, and popularity signals are the expected fallbacks. Do not claim ALS is active just because its code is deployed.

## 5. Verify the release

- `GET /health` returns `{"status":"ok"}`.
- `GET /` returns the API welcome message.
- `/docs` loads and exposes the API routes.
- TMDB-backed trending, search, details, and discover endpoints return data.
- Signup/login works against the production database.
- Watch history, ratings, and watchlist persist after a new login.
- Personalized recommendations exclude already watched/rated/saved items as intended.
- Content artifacts load and pass their manifest/hash checks.
- Test from the actual Vercel domain, not only localhost.
- Check API logs for CORS, database, TMDB, model-loading, and memory errors.

## 6. Resource and operational limits

SentenceTransformers/PyTorch inference and the FAISS index require materially more memory than a static frontend. A 512 MB API instance is not a reliable target for loading the embedding model and serving personalized recommendations; plan for a larger memory tier and verify under real requests. The service also needs persistent storage or an artifact rebuild strategy.

The scheduler currently runs inside the API process. Use one instance for this portfolio deployment; move scheduled catalog updates to a dedicated worker or managed cron before scaling horizontally. SQLAlchemy `create_all` at startup is not a substitute for versioned database migrations. Back up the production database before catalog/schema changes.

## 7. CI

GitHub Actions runs the backend test suite and frontend lint/build checks on pushes and pull requests targeting `feature/deepcine-2.0`. A green CI run validates those automated checks only; it does not validate secrets, database connectivity, TMDB access, model artifacts, or live hosting.
