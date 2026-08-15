from collections import Counter
from sqlalchemy.orm import Session

from app.models import (
    WatchHistory,
    SearchHistory,
    Movie,
    MovieGenre,
)
from ai import collaborative


def get_personalized_recommendations(user_id: int, db: Session):
    """
    Hybrid personalization pipeline, tried in order:

      1. Collaborative filtering (ALS matrix factorization on watch-history
         interactions across ALL users) - the strongest signal once a user
         has enough history, because it captures "people like you also
         watched..." patterns that content/genre features can't see.

      2. Genre-affinity heuristic - a lighter-weight fallback for users the
         CF model hasn't learned about yet (e.g. trained before they signed
         up, or too few interactions to be reliable).

      3. Global popularity - cold-start fallback for brand-new users with
         no history at all.
    """

    # --------------------------------------------------
    # 0. Try genuine collaborative filtering first
    # --------------------------------------------------

    cf_recommendations = collaborative.recommend_for_user(
        user_id,
        top_k=20,
    )

    if cf_recommendations:
        return cf_recommendations

    # --------------------------------------------------
    # 1. Get user's watch history
    # --------------------------------------------------

    history = (
        db.query(WatchHistory)
        .filter(WatchHistory.user_id == user_id)
        .order_by(WatchHistory.watched_at.desc())
        .all()
    )

    # --------------------------------------------------
    # 2. Cold-start fallback
    # --------------------------------------------------

    if not history:

        return (
            db.query(Movie)
            .filter(Movie.vote_average.isnot(None))
            .order_by(
                Movie.popularity.desc(),
                Movie.vote_average.desc()
            )
            .limit(20)
            .all()
        )

    # --------------------------------------------------
    # 3. Get watched TMDB IDs
    # --------------------------------------------------

    watched_tmdb_ids = [
        h.tmdb_id
        for h in history
    ]

    # --------------------------------------------------
    # 4. Get watched movies from database
    # --------------------------------------------------

    watched_movies = (
        db.query(Movie)
        .filter(
            Movie.tmdb_id.in_(watched_tmdb_ids)
        )
        .all()
    )

    if not watched_movies:

        return (
            db.query(Movie)
            .order_by(Movie.popularity.desc())
            .limit(20)
            .all()
        )

    watched_movie_ids = [
        movie.id
        for movie in watched_movies
    ]

    # --------------------------------------------------
    # 5. Find user's favorite genres
    # --------------------------------------------------

    genre_counter = Counter()

    for movie in watched_movies:

        movie_genres = (
            db.query(MovieGenre)
            .filter(
                MovieGenre.movie_id == movie.id
            )
            .all()
        )

        for relation in movie_genres:
            genre_counter[relation.genre_id] += 1

    # --------------------------------------------------
    # 6. If no genre data exists
    # --------------------------------------------------

    if not genre_counter:

        return (
            db.query(Movie)
            .filter(
                ~Movie.id.in_(watched_movie_ids)
            )
            .order_by(
                Movie.popularity.desc(),
                Movie.vote_average.desc()
            )
            .limit(20)
            .all()
        )

    # --------------------------------------------------
    # 7. Select top genres
    # --------------------------------------------------

    favorite_genres = [
        genre_id
        for genre_id, count
        in genre_counter.most_common(3)
    ]

    # --------------------------------------------------
    # 8. Recommend unseen movies
    # --------------------------------------------------

    recommendations = (
        db.query(Movie)
        .join(MovieGenre)
        .filter(
            MovieGenre.genre_id.in_(favorite_genres),
            ~Movie.id.in_(watched_movie_ids),
        )
        .order_by(
            Movie.popularity.desc(),
            Movie.vote_average.desc()
        )
        .limit(20)
        .all()
    )

    return recommendations