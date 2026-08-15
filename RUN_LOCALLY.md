# Running DeepCine locally

This folder is pre-configured for **localhost** — `backend/.env` uses a
local SQLite database (no Postgres server needed) and `frontend/.env`
points at `http://localhost:8000`. You still need to add your own TMDB
API keys.

## Prerequisites

- Python 3.11 (matches `backend/runtime.txt`)
- Node.js 18+ and npm
- A free TMDB account: https://www.themoviedb.org/settings/api

## 1. Get your TMDB keys

1. Sign up / log in at themoviedb.org, go to Settings → API, request a key
   (choose "Developer").
2. Open `backend/.env` and fill in:
   ```
   TMDB_API_KEY=your_key_here
   TMDB_ACCESS_TOKEN=your_read_access_token_here
   ```
   (The "API Read Access Token" on that same page is what `TMDB_ACCESS_TOKEN`
   needs — it's the long token, not the short v3 key.)

## 2. Backend setup

```bash
cd backend
python3 -m venv venv

# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

> Note: `sentence-transformers`, `torch`, and `faiss-cpu` are sizeable
> (~1–2GB combined) and the install can take several minutes the first
> time — that's normal and only happens once.

### Seed the local database

These populate your local `deepcine.db` (SQLite file, created automatically)
with real movies from TMDB, and build the recommendation index:

```bash
python import_movies.py       # imports ~100 popular movies
python import_genres.py       # imports the genre list
python link_movie_genres.py   # links each movie to its genres
python generate_embeddings.py # builds the content-based FAISS index
```

Each prints progress and a final count — expect `import_movies.py` to add
roughly 100 movies (5 pages × 20), and `generate_embeddings.py` to take
under a minute on CPU for that many.

> Collaborative filtering (`python train_collaborative_model.py`) needs
> real watch-history rows first — skip it for now. Once you've clicked
> into a few movies while using the app (which logs watch history
> automatically), come back and run it, then restart the backend. Until
> then, the "Viewers Like You Also Watched" row just won't appear, which
> is expected on a fresh install.

### Run the backend

```bash
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify it's alive: open http://localhost:8000/health in a browser — you
should get `{"status":"ok"}`. Interactive API docs are at
http://localhost:8000/docs.

**Leave this terminal running** and open a new one for the frontend.

## 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Vite will print a local URL, typically:
```
Local:   http://localhost:5173/
```

Open that in your browser. Sign up for an account, browse movies, click
into a few — watch history starts building immediately, and personalized
recommendations improve as you go.

## 4. Everyday restart (after the first-time setup above)

Two terminals, every time:

```bash
# Terminal 1
cd backend && source venv/bin/activate && python run.py

# Terminal 2
cd frontend && npm run dev
```

## Troubleshooting

- **`ModuleNotFoundError` on backend start** — you're not inside the
  activated venv, or `pip install -r requirements.txt` didn't finish
  successfully. Re-run it and check for errors.
- **Movies/search return errors** — almost always missing/incorrect
  `TMDB_ACCESS_TOKEN` in `backend/.env`. Restart the backend after editing
  `.env` (env vars are only read at startup).
- **Frontend loads but nothing shows up** — check the browser console;
  if you see CORS or connection errors, confirm the backend is actually
  running on port 8000 and `frontend/.env` still points at
  `http://localhost:8000`.
- **Personalized/collaborative rows are empty** — expected for a brand
  new account with no watch history yet. Click into a handful of movies,
  then reload the home page.
- **Want a clean slate?** Delete `backend/deepcine.db` and re-run the
  seed scripts from step 2.
