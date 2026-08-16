"""
Powers "browse by mood / genre / language" - the discover experience.

TMDB doesn't have a native "mood" concept, so moods are defined here as
curated combinations of genre IDs + sort/rating heuristics, mapped onto
TMDB's `/discover/movie` endpoint (which supports arbitrary genre and
language filtering natively - unlike the popular/trending/top-rated
lists already used elsewhere in the app, which don't accept filters).
"""

from app.services.tmdb.client import tmdb_get, LIST_TTL

# TMDB's official genre IDs (stable, documented at
# https://developer.themoviedb.org/reference/genre-movie-list)
GENRE_IDS = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "science_fiction": 878,
    "thriller": 53,
    "war": 10752,
    "western": 37,
}

# Each mood maps to a genre combination + a sort/quality heuristic.
# `genres` are OR'd together by TMDB's with_genres param when
# pipe-separated (comma = AND, pipe = OR) - moods want "any of these
# genres", so pipes.
MOODS = {
    "feel_good": {
        "label": "😊 Feel Good",
        "description": "Comedy, family, and animated picks to lift your mood.",
        "genres": [GENRE_IDS["comedy"], GENRE_IDS["family"], GENRE_IDS["animation"]],
        "sort_by": "popularity.desc",
    },
    "intense": {
        "label": "🔥 Intense",
        "description": "Action, thrillers, and crime to keep you on edge.",
        "genres": [GENRE_IDS["action"], GENRE_IDS["thriller"], GENRE_IDS["crime"]],
        "sort_by": "popularity.desc",
    },
    "romantic": {
        "label": "💕 Romantic",
        "description": "Love stories, front and center.",
        "genres": [GENRE_IDS["romance"]],
        "sort_by": "popularity.desc",
    },
    "scary": {
        "label": "👻 Scary",
        "description": "Horror movies for when you want to be spooked.",
        "genres": [GENRE_IDS["horror"], GENRE_IDS["mystery"]],
        "sort_by": "popularity.desc",
    },
    "mind_bending": {
        "label": "🧠 Mind-Bending",
        "description": "Sci-fi and mystery that make you think.",
        "genres": [GENRE_IDS["science_fiction"], GENRE_IDS["mystery"]],
        "sort_by": "vote_average.desc",
        "min_votes": 200,
    },
    "emotional": {
        "label": "😢 Emotional",
        "description": "Dramas that hit deep.",
        "genres": [GENRE_IDS["drama"]],
        "sort_by": "vote_average.desc",
        "min_votes": 200,
    },
    "chill": {
        "label": "🌙 Chill",
        "description": "Easy watching - animation, family, music.",
        "genres": [GENRE_IDS["animation"], GENRE_IDS["family"], GENRE_IDS["music"]],
        "sort_by": "popularity.desc",
    },
    "epic_adventure": {
        "label": "🗺️ Epic Adventure",
        "description": "Fantasy, adventure, and sweeping journeys.",
        "genres": [GENRE_IDS["adventure"], GENRE_IDS["fantasy"]],
        "sort_by": "popularity.desc",
    },
}

# A curated set of common languages, since TMDB doesn't offer a clean
# "languages with enough movies to be worth browsing" endpoint. ISO
# 639-1 codes, used directly as TMDB's `with_original_language` param.
LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "hi", "label": "Hindi"},
    {"code": "es", "label": "Spanish"},
    {"code": "fr", "label": "French"},
    {"code": "ko", "label": "Korean"},
    {"code": "ja", "label": "Japanese"},
    {"code": "zh", "label": "Chinese"},
    {"code": "de", "label": "German"},
    {"code": "it", "label": "Italian"},
    {"code": "ta", "label": "Tamil"},
    {"code": "te", "label": "Telugu"},
    {"code": "pt", "label": "Portuguese"},
    {"code": "ru", "label": "Russian"},
    {"code": "tr", "label": "Turkish"},
]


async def discover_movies(
    genres: list[int] | None = None,
    language: str | None = None,
    mood: str | None = None,
    sort_by: str = "popularity.desc",
    page: int = 1,
):
    """
    Queries TMDB's /discover/movie endpoint with whatever combination of
    filters is provided. `mood`, if given, supplies its own genres/sort
    defaults, which explicit `genres`/`sort_by` args override.
    """
    params: dict = {
        "page": page,
        "include_adult": False,
        "sort_by": sort_by,
    }

    effective_genres = list(genres) if genres else []
    min_votes = None

    if mood and mood in MOODS:
        mood_config = MOODS[mood]
        if not effective_genres:
            effective_genres = mood_config["genres"]
        if sort_by == "popularity.desc":
            # only take the mood's sort default if caller didn't ask for
            # something specific
            params["sort_by"] = mood_config["sort_by"]
        min_votes = mood_config.get("min_votes")

    if effective_genres:
        params["with_genres"] = "|".join(str(g) for g in effective_genres)

    if language:
        params["with_original_language"] = language

    if min_votes:
        params["vote_count.gte"] = min_votes

    data = await tmdb_get("discover/movie", params, ttl_seconds=LIST_TTL)
    return data.get("results", [])


def list_moods():
    return [
        {"key": key, "label": v["label"], "description": v["description"]}
        for key, v in MOODS.items()
    ]