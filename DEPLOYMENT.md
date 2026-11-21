# DeepCine deployment runbook

This repository's frontend is a Vite SPA and the backend is a FastAPI service. The frontend can be deployed on Vercel; the API can run on Render Free and use Neon PostgreSQL Free for persistent storage with automatic compute scale-to-zero.

## 1. Deploy the frontend on Vercel

1. Import the GitHub repository `dolly-bit/DeepCineV2` into Vercel, or use the existing Vercel project.
2. Set the production branch to `main`.
3. Set **Root Directory** to `frontend`.
4. Build command: `npm run build`.
5. Output directory: `dist`.
6. Add environment variable `VITE_API_BASE_URL` with the public HTTPS URL of the deployed FastAPI service (no trailing slash).
7. Redeploy after changing the environment variable. Vite embeds this value at build time.

The frontend deployment does not include the backend or database. A successful Vercel build alone does not mean API requests work.

## 2. Create a Neon PostgreSQL database

1. Create a project at [Neon](https://neon.com/).
2. Create or select the production branch/database.
3. Copy the **pooled** connection string from the Connect dialog. Keep the password private.
4. Confirm the URL uses SSL (Neon's connection string normally includes `sslmode=require`).
5. Back up/export the existing Render PostgreSQL database and restore it into Neon before switching production traffic. Do not delete the old database until the restore and application checks succeed.

Neon's Free plan currently includes 100 compute-hours per project each month, 5 GB public network transfer, and automatic compute suspension after five minutes of inactivity. Compute usage is not zero while the database is active; the free quota can be exhausted. Check the current [Neon pricing and limits](https://neon.com/pricing) before relying on the free tier.

The repository's `docker-compose.yml` is for local development only; it is not a production database host. A PostgreSQL container running on your laptop is not reachable by Render and must never be used as Render's production `DATABASE_URL`.

## 3. Deploy the API on Render Free

For Render:
- Repository: `dolly-bit/DeepCineV2`
- Branch: `main`
- Root directory: `backend`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `python run.py`
- Health check path: `/health/live` (process liveness only; does not query Neon)
- Use one API instance initially. Free services sleep after 15 minutes without inbound traffic and take about one minute to wake on the next request.
- Set `ENABLE_SCHEDULER=false`; an in-process scheduler cannot reliably run while a free service is asleep.

Set these backend environment variables in the host dashboard:

| Key | Value |
|---|---|
| `DATABASE_URL` | Neon pooled PostgreSQL connection string (keep `sslmode=require`) |
| `DB_POOL_MODE` | `null` (close connections instead of retaining idle SQLAlchemy pool connections) |
| `ENABLE_SCHEDULER` | `false` (do not run an in-process job on a sleeping free service) |
| `SECRET_KEY` | Long random secret; never reuse the example value |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `TMDB_API_KEY` | Your TMDB API key |
| `TMDB_ACCESS_TOKEN` | Your TMDB API Read Access Token |
| `ALLOWED_ORIGINS` | Exact Vercel production origin, e.g. `https://deepcine-v2.vercel.app` |
| `ADMIN_TASK_TOKEN` | Long random operator-only secret |

Do not put backend secrets in Vercel variables prefixed with `VITE_`; Vite variables are public in the browser bundle. Keep `ADMIN_TASK_TOKEN` private.

## 4. Seed the production catalog and content index

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

## 5. Collaborative filtering

A newly seeded catalog does not contain user interactions, so collaborative filtering will not immediately provide meaningful recommendations.

Collect watch-history events from multiple independent users first. Then run `python train_collaborative_model.py` in the backend environment. Training requires at least five users with at least three distinct watched movies each. Persist both `cf_model.pkl` and `cf_model_manifest.json` together; the manifest verifies the model artifact.

Until enough interaction data exists, content, genre-affinity, and popularity signals are the expected fallbacks. Do not claim ALS is active just because its code is deployed.

## 6. Verify the release

- `GET /health/live` returns `{"status":"alive"}` without waking the database.
- `GET /health` returns `{"status":"ok"}` when Neon is reachable; the first database request after scale-to-zero can be slower.
- `GET /` returns the API welcome message.
- `/docs` loads and exposes the API routes.
- TMDB-backed trending, search, details, and discover endpoints return data.
- Signup/login works against the production database.
- Watch history, ratings, and watchlist persist after a new login.
- Personalized recommendations exclude already watched/rated/saved items as intended.
- Content artifacts load and pass their manifest/hash checks.
- Test from the actual Vercel domain, not only localhost.
- Check API logs for CORS, database, TMDB, model-loading, and memory errors.

## 7. Resource and operational limits

SentenceTransformers/PyTorch inference and the FAISS index require materially more memory than a static frontend. A 512 MB API instance is not a reliable target for loading the embedding model and serving personalized recommendations; plan for a larger memory tier and verify under real requests. The service also needs persistent storage or an artifact rebuild strategy.

The scheduler runs inside the API process and is disabled on the recommended Render Free configuration (`ENABLE_SCHEDULER=false`). Free services sleep after 15 minutes without inbound traffic, so scheduled work is not reliable there. Run catalog refreshes manually through the protected admin endpoint or move them to a separate scheduled worker/cron service. SQLAlchemy `create_all` at startup is retained for the current project setup, but is not a substitute for versioned database migrations. Back up the production database before catalog/schema changes.

For Neon, set `DB_POOL_MODE=null`. This uses SQLAlchemy `NullPool`, which closes each database connection when its unit of work ends instead of leaving idle connections in the API process. Neon can then suspend compute after its idle window. The first query after suspension wakes the database and adds latency. Do not add uptime-monitoring pings that repeatedly call database-backed endpoints; use `/health/live` for process liveness.

## 8. CI

GitHub Actions runs the backend test suite and frontend lint/build checks on pushes and pull requests targeting `feature/deepcine-2.0`. A green CI run validates those automated checks only; it does not validate secrets, database connectivity, TMDB access, model artifacts, or live hosting.
