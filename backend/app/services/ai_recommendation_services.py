from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import WatchHistory, Movie, MovieGenre
from ai import collaborative
from ai.recommender import recommend_for_user_content
from ai.ranking import reciprocal_rank_fusion


def get_personalized_recommendations(user_id: int, db: Session, top_k: int = 20):
    """Fuse content, ALS, genre-affinity and popularity candidate rankings.

    Reciprocal-rank fusion is used because FAISS distances, ALS dot products
    and TMDB popularity are not calibrated to a shared numeric scale.
    """
    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id
    ).order_by(WatchHistory.watched_at.desc()).all()
    watched_tmdb_ids = {event.tmdb_id for event in history}
    watched_db_ids = set()

    if watched_tmdb_ids:
        watched_db_ids = {
            movie.id for movie in db.query(Movie).filter(
                Movie.tmdb_id.in_(watched_tmdb_ids)
            ).all()
        }

    content = recommend_for_user_content(user_id, db, top_k=100)
    collaborative_ranking = [
        tmdb_id for tmdb_id, _score
        in collaborative.recommendation_scores_for_user(user_id, top_k=100)
    ]

    genre_ranking = []
    if watched_db_ids:
        rows = db.query(MovieGenre.genre_id).filter(
            MovieGenre.movie_id.in_(watched_db_ids)
        ).all()
        counts = {}
        for (genre_id,) in rows:
            counts[genre_id] = counts.get(genre_id, 0) + 1
        favorite_genres = sorted(
            counts, key=counts.get, reverse=True
        )[:5]
        if favorite_genres:
            genre_rows = (
                db.query(Movie.tmdb_id)
                .join(MovieGenre, MovieGenre.movie_id == Movie.id)
                .filter(
                    MovieGenre.genre_id.in_(favorite_genres),
                    ~Movie.id.in_(watched_db_ids),
                )
                .group_by(Movie.id, Movie.tmdb_id, Movie.popularity)
                .order_by(
                    func.count(MovieGenre.genre_id).desc(),
                    func.coalesce(Movie.popularity, 0).desc(),
                )
                .limit(100).all()
            )
            genre_ranking = [tmdb_id for (tmdb_id,) in genre_rows]

    popular_query = db.query(Movie)
    if watched_db_ids:
        popular_query = popular_query.filter(~Movie.id.in_(watched_db_ids))
    popular = popular_query.order_by(
        func.coalesce(Movie.popularity, 0).desc(),
        func.coalesce(Movie.vote_average, 0).desc(),
    ).limit(100).all()
    popularity_ranking = [movie.tmdb_id for movie in popular]

    fused_ids = reciprocal_rank_fusion(
        {
            "content": content,
            "collaborative": collaborative_ranking,
            "genre": genre_ranking,
            "popularity": popularity_ranking,
        },
        weights={
            "content": 1.0,
            "collaborative": 1.0,
            "genre": 0.65,
            "popularity": 0.25,
        },
        top_k=top_k,
    )
    if not fused_ids:
        return []

    movies = db.query(Movie).filter(Movie.tmdb_id.in_(fused_ids)).all()
    by_tmdb_id = {movie.tmdb_id: movie for movie in movies}
    return [by_tmdb_id[mid] for mid in fused_ids if mid in by_tmdb_id]
