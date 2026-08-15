# What changed, and why

## 🚀 Performance / boot-time fixes

1. **`backend/ai/recommender.py` + `backend/ai/embeddings.py`** — `sentence-transformers`
   (which pulls in torch) and `faiss` were imported at *module level*. Since
   `ai.recommender` is imported by `app.routes.recommend`, which is wired up in
   `app.main` at server startup, **every cold boot paid the full torch-load cost
   before Uvicorn could accept a single request.** This is almost certainly your
   #1 "backend takes forever to boot up" cause, especially on a free-tier host.
   Fixed by deferring these imports to first actual use (lazy singletons). Verified
   locally: server now reaches a healthy `/health` response in ~1.3s.

2. **`backend/app/services/tmdb/client.py`** — was using the synchronous `requests`
   library *inside `async def` route handlers*. A blocking call inside an `async`
   function blocks FastAPI's entire event loop, so concurrent requests were
   effectively serialized — this is your "takes so much time to fetch movies"
   symptom under any real traffic. Rewrote as an `httpx.AsyncClient` with:
   - per-endpoint TTL caching (list endpoints cached 30 min, details 6 hrs,
     search 10 min — up from a blanket 5 min for everything)
   - de-duplication of concurrent identical requests
   - a stale-cache fallback if TMDB is slow/down, instead of failing outright

3. **`backend/app/services/tmdb/movies.py` / `genres.py` / `details.py`** — converted
   to `async def` to match the new async client. Updated the offline import
   scripts (`import_movies.py`, `import_genres.py`, `link_movie_genres.py`) to run
   via `asyncio.run(...)`.

4. **`backend/app/main.py`** — added a **non-blocking** startup task that
   pre-warms the trending/top-rated/upcoming caches in the background (fire-and-
   forget `asyncio.create_task`), so the very first visitor after a deploy
   usually gets cache hits instead of a cold TMDB round-trip. This does not
   delay server startup.

5. **`backend/app/schedular/schedular.py`** — fixed an import typo
   (`app.scheduler...` → `app.schedular...`, matching the actual folder name)
   that would have crashed if the scheduler was ever wired up.

## 🐞 Real bugs fixed

- **`backend/app/routes/movies.py`** — `/movies/recommended/{user_id}` did
  `movie['poster_path']` on a SQLAlchemy ORM object (not a dict), guaranteed to
  raise `TypeError` / 500 on every call. Fixed.
- **`frontend/src/components/layout/Navbar.jsx`** — destructured `accesstoken`
  (lowercase) from `getAuthState()`, which actually returns `accessToken`. The
  navbar therefore *always* thought you were logged out (showing Login/Sign Up
  even while authenticated). Fixed, and it now also shows your username.
- **`frontend/src/components/RecommendationSection.jsx`** — accepted `movies`/
  `loading`/`title` props but silently ignored them and did its own internal
  fetch of `/recommend/personalized/{user_id}`. Combined with
  `PersonalizedMovies.jsx` (which also fetched the same data to pass down as
  props), personalized recommendations were being fetched **twice** on every
  home page load for no reason. Rewrote it as a pure, reusable presentational
  component driven by props.

## ✨ Feature completion: making it visibly a personalized/CF system

- **Search history was dead code.** `saveSearchHistory` existed in
  `services/movies.js` but was never called from any page. Added a
  `recordSearch()` helper and wired it into `Search.jsx`, `SearchModal.jsx`,
  `FilterBar.jsx`, and the landing page `Hero.jsx` search boxes.
- **Watch history** (already correctly recorded when a movie detail page loads —
  i.e. whenever a user clicks "More Info" / a poster anywhere in the app) was
  cleaned up into a shared `recordWatch()` helper for consistency.
- **New `CollaborativeMovies.jsx`** component: a home-page row that calls
  `/recommend/collaborative/{user_id}` and surfaces genuine ALS-based
  collaborative filtering output ("Viewers Like You Also Watched"),
  previously only reachable on the `/recommend` page.
- **`Home.jsx`** now has an explicit "How this works" section explaining, in
  plain terms, that DeepCine is a personalized recommendation system built on
  content matching + collaborative filtering + watch history — this was the
  "doesn't show the main point that it's a personalized system" issue.
- **`Search.jsx` / `SearchModal.jsx`** now show a "Personalized & collaborative-
  filtering picks based on '<query>'" call-to-action after a search, linking to
  the full `/recommend` experience (which already combines personalized,
  content-based "because you searched", and collaborative sections).

## 📦 Housekeeping

- Added `backend/.env.example` and `frontend/.env.example` since neither
  existed — makes redeploying from a fresh clone much less error-prone.

## Verified

- `python -m py_compile` on every changed backend file — clean.
- Booted the FastAPI app locally end-to-end (SQLite, dummy TMDB token) —
  loads and serves `/health` in ~1.3s, no crashes.
- `npm run build` on the frontend — clean production build, no errors.

## Not done (ran out of scope for this pass — flagging honestly)

- No automated test suite exists in the repo; verification above was manual/
  structural, not a full integration test against a live TMDB key + Postgres.
- Further visual redesign (e.g. deeper motion/micro-interaction work) is
  possible but the existing Tailwind design system was already fairly
  polished — I focused effort on the things that were actually broken.


---

# Pass 3: Design system rebuild + poster/import fixes

## The real root cause of "it looks messed up"

This project uses **Tailwind v4** (via `@tailwindcss/vite`), which does
**not** read a `tailwind.config.js` file automatically — it needs an
`@theme` block in CSS instead. The config defining every `cm-*` color
token (`cm-bg`, `cm-purple`, `cm-line`, etc.) was also sitting at the
wrong path (`src/tailwind.config.js` instead of the project root).

**Net effect: every component using those classes was rendering with
zero styling.** That included `TopBar.jsx`, `FilterBar.jsx`, and the
entire `/recommend` page.

On top of that, the app had **two parallel, inconsistent component
sets**:
- Home page: `Navbar` / `DashboardHero` / `MovieCard`
- `/recommend` page: a separate, broken `TopBar` / `FilterBar` /
  `PosterCard` / `MovieRow` set — including a hardcoded
  `username = "Ayush"` fallback shown regardless of who was actually
  logged in.

### Fix
- Moved the real design tokens into a working Tailwind v4 `@theme` block
  in `src/index.css` — verified the compiled CSS now actually contains
  rules like `.bg-cm-bg{background-color:var(--color-cm-bg)}`.
- Deleted the dead/broken component set entirely: `TopBar.jsx`,
  `FilterBar.jsx`, `PosterCard.jsx`, `MovieRow.jsx`, and the unused
  `HeroCarousel.jsx`.
- Rebuilt `RecommendPage.jsx` on the same shared components as the Home
  page (`Navbar`, `DashboardHero`, `RecommendationSection`) — one design
  system, used consistently everywhere, instead of two.
- Removed the leftover dead-button "Watch Now" (had no `onClick` handler
  at all) and unified all accent colors (previously a mix of purple *and*
  red across different components).

## Poster bug — actual root causes found and fixed

1. `MovieCard.jsx` did `src={movie.poster_url || movie.poster_path}` —
   when `poster_url` was empty it fell back to a raw TMDB path fragment
   like `/abc123.jpg`, which is not a full URL and 404s against the
   frontend's own origin.
2. Cast photos and one recommendation row depended on
   `via.placeholder.com`, an external placeholder-image service with
   known reliability issues, with no local fallback.
3. Nothing anywhere had an `onError` handler, so any image that failed
   to load (broken URL, network issue, missing poster) just showed the
   browser's broken-image icon permanently.

### Fix
Built `components/ui/PosterImage.jsx` and `components/ui/BackdropImage.jsx`
— robust, dependency-free image components with a themed gradient +
title-initial fallback and `onError` handling. Used everywhere an image
renders: `MovieCard`, `DashboardHero`, `MovieDetails` (poster, backdrop,
and cast avatars), and `RecommendationSection`.

## "Some movies importing" — actual root cause found and fixed

`import_popular_movies()` only called `db.commit()` once, after the
entire 5-page loop. Any single page failing partway through (rate limit,
network blip, bad token) meant the whole import silently saved nothing —
not even the pages that had already succeeded.

### Fix
- Commits after each page now, so partial progress survives a later
  page failing.
- A 401 (bad/missing `TMDB_ACCESS_TOKEN`) now fails fast with a specific,
  actionable message instead of continuing to retry or silently
  returning 0.
- Other transient errors (network blips, non-401 TMDB errors) are logged
  per-page and skipped, with a summary of which pages to retry.
- **Also fixed**: an *empty* `TMDB_ACCESS_TOKEN` (the state of a freshly
  cloned `.env` before you fill it in) previously caused a cryptic httpx
  `Illegal header value` error. `app/services/tmdb/client.py` now
  validates the token before ever making a request and raises a clear,
  specific message pointing at the fix — verified via a direct test hit
  to `/movies/trending` with a blank token.

## Verified

- `npm run build` — clean.
- `npx eslint src` — **0 errors** (down from 26 at the start of this
  cleanup), 3 remaining warnings are standard `exhaustive-deps` notices
  for intentional mount-only effects.
- Confirmed compiled CSS actually contains the `cm-*` utility classes
  (previously silently absent).
- Full backend boot test with the shipped `.env` — healthy in ~1.3s.
- Tested the TMDB-auth-error path directly (both background warm-up and
  a live route hit) with a blank token — confirmed the clear error
  message appears in both places instead of a stack trace.


---

# Pass 4: Auth crash fix, profile page, similar-movies filtering, upcoming-movies fix

## Critical bug found during verification: registration crashed on every call

While testing the new `/auth/me` endpoint end-to-end, found that
`POST /auth/register` (and therefore login too, since both hash/verify
passwords) returned a 500 on literally every request. Root cause: this
is a well-known, widespread `passlib` + `bcrypt` incompatibility -
`passlib` (unmaintained since ~2020) probes `bcrypt.__about__.__version__`
to detect the backend version, and that attribute was removed starting
in `bcrypt` 4.1. Any environment that ends up with a newer `bcrypt` than
the exact pin (a very common situation - dependency resolvers routinely
drift) hits this.

### Fix
Rewrote `app/auth/hashing.py` to use the `bcrypt` library directly,
removing the fragile `passlib` abstraction layer entirely. Removed the
now-unused `passlib` pin from `requirements.txt`. Verified with a full
register → login → `/auth/me` → wrong-password → invalid-token
integration test - all four cases now behave correctly.

## Navbar showing "Logout" when not logged in

The auth code itself (`services/auth.js`) was already correct - this was
almost certainly stale `localStorage` from earlier testing, since
tokens never expired or got validated client-side. Fixed properly, not
just patched around:
- Added a global axios response interceptor (`services/api.js`) that
  clears auth state automatically on any 401 response.
- Added a real backend `GET /auth/me` endpoint (previously **nothing**
  in the backend actually validated the JWT on any route) via a new
  `get_current_user` dependency that decodes the token and confirms the
  user still exists in the DB.
- The new Profile page calls `/auth/me` on load, so a stale/dead token
  now self-heals on the very next page load instead of lingering
  indefinitely.

## Show password on Login

Added a show/hide toggle to `Login.jsx`, matching the pattern
`Signup.jsx` already used.

## "No upcoming movies"

`get_upcoming_movies()` only fetched TMDB's page 1 (20 results) with no
`region` param. TMDB's `movie/upcoming` endpoint is region-scoped, and
without an explicit region the results are often skewed such that, after
filtering to strictly future release dates, little or nothing survived.

### Fix
Now fetches 3 pages with `region=US`, deduplicated, giving a much larger
and more reliable pool before the existing future-date filter runs.

## Dec 2026 movie showing in Trending

TMDB's trending data is actually correct here - a movie can legitimately
trend before release (buzz, trailers, festival premieres). Rather than
hide accurate data by filtering it out, added a "Coming Soon" badge to
`MovieCard` and `RecommendationSection` for any movie with a future
release date, so it's clearly labeled instead of confusing.

## "Similar Movies" showing junk (no poster, odd titles)

`GET /movies/{id}/similar` sliced to the first 10 raw TMDB results
*before* filtering, so obscure/junk entries with no poster and no votes
could crowd out better matches. Fixed: filter first (require a poster
and at least one vote), then take the top 10 from what's left.

## New: Profile page with logout

Built `pages/Profile.jsx` - shows the real account (username, email,
session status) fetched from the new `/auth/me` endpoint, with a logout
button. Wired into the route table at `/profile` and made the Navbar's
account chip clickable to reach it (previously just a static display).

## Verified

- Full register → login → `/auth/me` → wrong-password → invalid-token
  integration test against a live local server - all correct.
- `python -m py_compile` across the full backend tree - clean.
- `npm run build` - clean.
- `npx eslint src` - **0 errors**, 3 harmless pre-existing warnings.
