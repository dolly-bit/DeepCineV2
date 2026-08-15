import time
import asyncio

import httpx

from app.core.config import settings

BASE_URL = "https://api.themoviedb.org/3"


class TMDBNotConfigured(Exception):
    """Raised when TMDB_ACCESS_TOKEN is blank - this always means the
    server operator hasn't filled in backend/.env yet. Raising this
    explicitly gives a clear, actionable error instead of the cryptic
    'Illegal header value' httpx throws when asked to send
    `Authorization: Bearer ` with nothing after it."""


def _get_headers():
    token = (settings.TMDB_ACCESS_TOKEN or "").strip()

    if not token:
        raise TMDBNotConfigured(
            "TMDB_ACCESS_TOKEN is not set in backend/.env. Get the 'API "
            "Read Access Token' from "
            "https://www.themoviedb.org/settings/api, paste it in as "
            "TMDB_ACCESS_TOKEN (no quotes), and restart the backend."
        )

    return {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }


# A single shared async client, reused across requests (connection pooling).
_CLIENT: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.AsyncClient(
            base_url=BASE_URL,
            headers=_get_headers(),
            timeout=10,
        )
    return _CLIENT


async def aclose_client():
    global _CLIENT
    if _CLIENT is not None:
        await _CLIENT.aclose()
        _CLIENT = None


class _TMDBCache:
    """
    Simple in-memory TTL cache, keyed per-endpoint.

    Endpoints like trending/top-rated/upcoming barely change minute to
    minute, so they get a much longer TTL than the previous 300s - this
    means most home-page loads are served entirely from memory instead of
    round-tripping to TMDB on every request, which is the other big
    contributor to "movies take forever to load".
    """

    def __init__(self):
        self._entries = {}
        self._locks = {}
        self._global_lock = asyncio.Lock()

    async def get_or_set(self, key, ttl_seconds, factory):
        now = time.time()
        entry = self._entries.get(key)

        if entry and now - entry["timestamp"] <= ttl_seconds:
            return entry["value"]

        async with self._global_lock:
            lock = self._locks.setdefault(key, asyncio.Lock())

        async with lock:
            # Re-check in case another coroutine already refreshed it
            # while we were waiting on the lock (avoids duplicate
            # concurrent calls to TMDB for the same endpoint).
            entry = self._entries.get(key)
            now = time.time()
            if entry and now - entry["timestamp"] <= ttl_seconds:
                return entry["value"]

            value = await factory()
            self._entries[key] = {"value": value, "timestamp": time.time()}
            return value

    def peek(self, key):
        """Return a cached value even if stale, or None. Used as a
        last-resort fallback if a live TMDB call fails."""
        entry = self._entries.get(key)
        return entry["value"] if entry else None

    def clear(self):
        """Drops every cached entry. Called after the daily auto-update
        job changes the underlying data, so stale trending/top-rated/
        upcoming responses aren't served for up to their full TTL after
        the catalog has actually changed."""
        self._entries.clear()


TMDB_CACHE = _TMDBCache()

# Different endpoints change at different rates - cache them accordingly.
DEFAULT_TTL = 60 * 15        # 15 min - general default
LIST_TTL = 60 * 30           # 30 min - trending / top-rated / upcoming
SEARCH_TTL = 60 * 10         # 10 min - search results
DETAILS_TTL = 60 * 60 * 6    # 6 hours - a given movie's details rarely change


def _normalize_params(params):
    if not params:
        return ()

    if isinstance(params, dict):
        return tuple(sorted(params.items()))

    return tuple(params.items()) if hasattr(params, "items") else tuple(params)


async def tmdb_get(endpoint: str, params=None, ttl_seconds: int = DEFAULT_TTL):
    cache_key = (endpoint, _normalize_params(params))

    async def _fetch():
        client = _get_client()
        response = await client.get(f"/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    try:
        return await TMDB_CACHE.get_or_set(cache_key, ttl_seconds, _fetch)
    except (httpx.HTTPError, httpx.TimeoutException):
        # If TMDB is slow/unreachable, serve a stale cached copy if we
        # have one rather than failing the whole request.
        stale = TMDB_CACHE.peek(cache_key)
        if stale is not None:
            return stale
        raise
