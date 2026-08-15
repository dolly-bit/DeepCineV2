from sqlalchemy.orm import Session
import httpx

from app.models.movie import Movie
from app.services.tmdb.client import tmdb_get, LIST_TTL, SEARCH_TTL


class TMDBAuthError(Exception):
    """Raised when TMDB rejects our credentials (401) - this is always a
    configuration problem (missing/incorrect TMDB_ACCESS_TOKEN), never a
    transient issue, so callers should stop immediately and surface a
    clear message instead of retrying or silently importing 0 movies."""


async def import_popular_movies(db: Session, pages: int = 25):
    """
    Imports up to `pages` pages (20 movies each) of TMDB's popular list -
    default 25 pages = 500 movies.

    Each page is committed as soon as it succeeds, so a failure on a
    later page still leaves earlier pages saved instead of losing
    everything - and a 401 (bad/missing TMDB_ACCESS_TOKEN) fails fast
    with a clear message instead of quietly returning 0 with no
    explanation.

    Movies already in the DB are UPDATED (rating, popularity, etc.)
    rather than skipped - this is what makes re-running this safe to
    call repeatedly (e.g. from the daily auto-update job) instead of it
    only ever adding the handful of movies that are new to the list
    since last time.
    """
    count_new = 0
    count_updated = 0
    seen_tmdb_ids = set()
    failed_pages = []

    for page in range(1, pages + 1):
        try:
            data = await tmdb_get("movie/popular", {"page": page})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise TMDBAuthError(
                    "TMDB rejected the request (401 Unauthorized). This "
                    "means TMDB_ACCESS_TOKEN in backend/.env is missing, "
                    "invalid, or is the short API Key instead of the long "
                    "'API Read Access Token' from "
                    "https://www.themoviedb.org/settings/api. Fix that "
                    "value and restart the backend before re-running this "
                    "script."
                ) from e

            print(f"  Page {page}: TMDB error {e.response.status_code}, skipping.")
            failed_pages.append(page)
            continue
        except httpx.HTTPError as e:
            print(f"  Page {page}: network error ({e}), skipping.")
            failed_pages.append(page)
            continue

        if not data.get("results"):
            # Ran past the last page TMDB actually has - stop early
            # instead of burning through the rest of the range.
            break

        page_new = 0
        page_updated = 0

        for item in data.get("results", []):
            tmdb_id = item["id"]

            if tmdb_id in seen_tmdb_ids:
                continue
            seen_tmdb_ids.add(tmdb_id)

            existing = db.query(Movie).filter(
                Movie.tmdb_id == tmdb_id
            ).first()

            fields = dict(
                title=item["title"],
                original_title=item.get("original_title"),
                overview=item.get("overview"),
                poster_path=item.get("poster_path"),
                backdrop_path=item.get("backdrop_path"),
                vote_average=item.get("vote_average"),
                vote_count=item.get("vote_count"),
                popularity=item.get("popularity"),
                original_language=item.get("original_language"),
                adult=item.get("adult", False),
            )

            if existing:
                for key, value in fields.items():
                    setattr(existing, key, value)
                count_updated += 1
                page_updated += 1
            else:
                db.add(Movie(tmdb_id=tmdb_id, **fields))
                count_new += 1
                page_new += 1

        # Commit after each page so partial progress survives a later
        # page failing, instead of an all-or-nothing single commit.
        db.commit()
        print(
            f"  Page {page}: +{page_new} new, {page_updated} updated "
            f"(running total: {count_new} new)"
        )

    if failed_pages:
        print(
            f"  Note: {len(failed_pages)} page(s) failed and were skipped: "
            f"{failed_pages}. Re-run the script to retry them - already-"
            f"imported movies won't be duplicated."
        )

    print(f"  Refreshed stats for {count_updated} already-imported movies.")

    return count_new


async def get_trending_movies():
    data = await tmdb_get("trending/movie/week", ttl_seconds=LIST_TTL)
    return data.get("results", [])


async def get_top_rated_movies():
    data = await tmdb_get("movie/top_rated", ttl_seconds=LIST_TTL)
    return data.get("results", [])


async def get_upcoming_movies():
    """
    TMDB's `movie/upcoming` endpoint is region-scoped and a single page
    (20 results) very often doesn't leave much after filtering to strictly
    future release dates - especially without a `region` param, where
    TMDB's default selection can skew toward movies that, from a given
    caller's calendar day, have already been released somewhere. Fetching
    a few pages with an explicit region gives a much more reliable pool.
    """
    all_results = []
    seen_ids = set()

    for page in (1, 2, 3):
        data = await tmdb_get(
            "movie/upcoming",
            {"region": "US", "page": page},
            ttl_seconds=LIST_TTL,
        )

        for movie in data.get("results", []):
            if movie["id"] not in seen_ids:
                seen_ids.add(movie["id"])
                all_results.append(movie)

    return all_results


async def search_movies(query: str):
    data = await tmdb_get(
        "search/movie",
        {
            "query": query,
            "include_adult": False,
        },
        ttl_seconds=SEARCH_TTL,
    )
    return data.get("results", [])
