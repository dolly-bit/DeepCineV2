# DeepCine deployment runbook

DeepCine uses:
- **Frontend:** Vercel (Vite SPA)
- **API:** Google Cloud Run (FastAPI container, request-based billing, scale to zero)
- **Database:** Neon PostgreSQL (pooled connection string)
- **Movie metadata/posters:** TMDB

The frontend and API are separate deployments. A green CI run or successful Vercel build does not prove the production API, database, TMDB credentials, or model artifacts work.

## 1. Deploy the frontend on Vercel

1. Use the existing Vercel project or import `dolly-bit/DeepCineV2`.
2. Production branch: `main`.
3. Root directory: `frontend`.
4. Build command: `npm run build`.
5. Output directory: `dist`.
6. Set `VITE_API_BASE_URL` to the public HTTPS Cloud Run service URL (no trailing slash).
7. Redeploy after changing this variable; Vite embeds it at build time.

Do not put backend secrets in variables prefixed with `VITE_`; those values are exposed in the browser bundle.

## 2. Create the Neon PostgreSQL database

1. Create or select a Neon project and production branch.
2. Copy the **pooled** connection string from Neon's Connect dialog. Keep the password private.
3. Ensure the URL uses SSL (normally `sslmode=require`).
4. Store the connection string in Google Secret Manager; do not commit it or paste it into source code.

For this deployment, use the Neon pooled endpoint and set `DB_POOL_MODE=null`. The application uses SQLAlchemy `NullPool` so it does not retain idle connections while Neon is suspended.

Neon Free compute suspends after inactivity, but it is not unlimited free compute. Check the current [Neon pricing and limits](https://neon.com/pricing). The first query after suspension can be slower while the database resumes.

This plan assumes a **fresh Neon database**. Existing Render data is not migrated. The API currently calls SQLAlchemy `Base.metadata.create_all()` during startup to create missing tables. This does not apply schema alterations to existing tables and is not a replacement for versioned Alembic migrations. Back up data before any future schema migration.

## 3. Prepare Google Cloud

1. Create/select a Google Cloud project and attach a billing account.
2. Enable the Cloud Run, Cloud Build, Artifact Registry, and Secret Manager APIs.
3. Choose a region close to the Neon database. If Neon is in Singapore, use `asia-southeast1` for the API to reduce database round-trip latency.
4. Create an Artifact Registry Docker repository, for example:
   `gcloud artifacts repositories create deepcine --repository-format=docker --location=asia-southeast1`
5. Create secrets in Secret Manager for:
   - `DATABASE_URL` — Neon pooled connection string
   - `SECRET_KEY` — long, randomly generated JWT signing secret
   - `TMDB_API_KEY` and `TMDB_ACCESS_TOKEN` — TMDB credentials
   - `ADMIN_TASK_TOKEN` — long, random operator-only token

Grant the Cloud Run service identity access to these secrets. Do not put secret values in GitHub, Docker build arguments, or the frontend.

Cloud Run requires a billing account. Scale-to-zero and request-based billing reduce idle costs, but they do **not** guarantee a zero bill. Set a Google Cloud budget alert; budget alerts notify you and are not a hard spending cap.

## 4. Build and deploy the API container

The repository-root `Dockerfile` builds the backend from `backend/`. The root `.dockerignore` excludes local secrets, virtual environments, frontend files, datasets, and generated model artifacts.

From the repository root, after installing and authenticating the Google Cloud CLI:

```powershell
$PROJECT_ID = "YOUR_GCP_PROJECT_ID"
$REGION = "asia-southeast1"
$IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/deepcine/deepcine-api"

gcloud config set project $PROJECT_ID
gcloud builds submit --tag $IMAGE .
```

Deploy with request-based billing, scale-to-zero, and a single maximum instance initially:

```powershell
gcloud run deploy deepcine-api `
  --image $IMAGE `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --memory 2Gi `
  --cpu 2 `
  --min 0 `
  --max 1 `
  --concurrency 10 `
  --timeout 300 `
  --cpu-throttling `
  --set-env-vars "DB_POOL_MODE=null,ENABLE_SCHEDULER=false,ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=60,ALLOWED_ORIGINS=https://deepcine-v2.vercel.app" `
  --set-secrets "DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,TMDB_API_KEY=TMDB_API_KEY:latest,TMDB_ACCESS_TOKEN=TMDB_ACCESS_TOKEN:latest,ADMIN_TASK_TOKEN=ADMIN_TASK_TOKEN:latest"
```

The command assumes the service identity has permission to access those secrets. If your Vercel production domain differs, change `ALLOWED_ORIGINS` to the exact origin.

The initial 2 GiB memory setting is a starting point, not a proven capacity guarantee. Sentence Transformers/PyTorch and FAISS consume substantially more memory than a basic FastAPI service. Watch Cloud Run memory and logs during model inference; increase memory if the container is OOM-killed. Keep max instances at 1 until load and cost are understood.

Cloud Run injects the `PORT` environment variable. `backend/run.py` binds Uvicorn to `0.0.0.0:$PORT`.

## 5. Important: recommendation artifact persistence

The content recommender expects these four files under the backend directory:
- `movie_embeddings.npy`
- `movie_ids.npy`
- `movie_index.faiss`
- `movie_artifact_manifest.json`

They are intentionally excluded from Git and Docker build context. The current index builder writes them to the container's local filesystem. **Cloud Run's writable container filesystem is ephemeral**: files can disappear when an instance stops, is replaced, or a new revision is deployed. With min instances set to zero, do not assume a generated FAISS index will still exist after scale-to-zero.

Therefore, the API container can be deployed and the database/API flows can be verified, but a durable production content-recommendation rollout is not complete until artifacts are stored in durable object storage (for example, Google Cloud Storage) and downloaded/validated when an instance starts, or a different durable artifact delivery strategy is implemented. Do not treat a one-time `/admin/seed` or `/admin/refresh-index` call as a permanent fix: both currently build files on the local container filesystem.

The existing recommender returns no content-based recommendations when all content artifacts are absent. If artifacts are only partially present, it raises an integrity/validation error rather than silently using a broken index.

The embedding model `sentence-transformers/all-MiniLM-L6-v2` is loaded lazily and may need to download from Hugging Face on first inference. That can increase cold-start latency and requires outbound access. Monitor memory and startup/request latency before deciding whether to bake the model into the image.

## 6. Scheduler behaviour

Set `ENABLE_SCHEDULER=false` on Cloud Run. The code in `main.py` honours this setting. An in-process APScheduler job cannot be relied on while Cloud Run scales an instance to zero. Run catalog refreshes manually or move them to a separate scheduled job after the artifact persistence design is in place.

## 7. Verify the deployed API

After deployment, get the service URL:

```powershell
gcloud run services describe deepcine-api --region $REGION --format "value(status.url)"
```

Then verify:

- `GET /health/live` returns `{"status":"alive"}` without querying Neon.
- `GET /health` returns `{"status":"ok"}` when Neon is reachable.
- `GET /` returns the API welcome message.
- `/docs` loads and exposes the API routes.
- TMDB-backed trending, search, details, and discover endpoints return data.
- Signup/login works against the fresh Neon database.
- Watch history, ratings, and watchlist persist after a new login.
- CORS works from the actual Vercel production origin.
- Cloud Run logs show no database, TMDB, model-loading, or memory errors.

Keep the existing Render service available until the Cloud Run API and Vercel frontend have passed these checks. Only then remove the old service.

## 8. CI scope

GitHub Actions checks backend tests and frontend lint/build. Passing CI validates those automated checks only; it does not validate Google Cloud permissions, secret configuration, Neon connectivity, TMDB credentials, container memory, or persistent model artifact storage.
