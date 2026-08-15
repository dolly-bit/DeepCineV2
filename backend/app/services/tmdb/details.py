from app.services.tmdb.client import tmdb_get, DETAILS_TTL


async def get_movie_details(movie_id: int):
    return await tmdb_get(f"movie/{movie_id}", ttl_seconds=DETAILS_TTL)
