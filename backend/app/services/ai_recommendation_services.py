from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import WatchHistory, Movie, MovieGenre, Rating, WatchlistItem
from ai import collaborative
from ai.recommender import recommend_for_user_content
from ai.ranking import reciprocal_rank_fusion


def _rank_by_genre_affinity(db: Session, genre_weights, excluded_movie_ids, top_k=100):
    """Rank unseen catalog movies using positive and negative genre feedback."""
    if not genre_weights:
        return []

    rows = (
        db.query(
            Movie.tmdb_id,
            Movie.id,
            Movie.popularity,
            Movie.vote_average,
            MovieGenre.genre_id,
        )
        .join(MovieGenre, MovieGenre.movie_id == Movie.id)
        .filter(~Movie.id.in_(excluded_movie_ids) if excluded_movie_ids else True)
        .all()
    )

    scores = defaultdict(float)
    popularity = {}
    for tmdb_id, movie_id, movie_popularity, vote_average, genre_id in rows:
        scores[tmdb_id] += genre_weights.get(genre_id, 0.0)
        popularity[tmdb_id] = (
            max(float(movie_popularity or 0), 0.0),
            float(vote_average or 0),
        )

    ranked = [
        tmdb_id for tmdb_id, score in scores.items()
        if score > 0
    ]
    ranked.sort(
        key=lambda tmdb_id: (
            scores[tmdb_id],
            popularity[tmdb_id][0],
            popularity[tmdb_id][1],
        ),
        reverse=True,
    )
    return ranked[:top_k]


def get_personalized_recommendations(user_id: int, db: Session, top_k: int = 20):
    """Fuse behavioral, rating, watchlist, collaborative and popularity signals.

    Explicit 4-5 star ratings and watchlist saves strengthen genre preferences.
    1-2 star ratings weaken those genres and suppress the rated title. Neutral
    3-star ratings are excluded from preference learning.
    """
    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id
    ).order_by(WatchHistory.watched_at.desc()).all()
    ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    watchlist_items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user_id
    ).all()

    interacted_movie_ids = {event.tmdb_id for event in history}
    rated_movie_ids = {rating.movie_id for rating in ratings}
    watchlist_movie_ids = {item.movie_id for item in watchlist_items}
    excluded_db_ids = set(rated_movie_ids) | set(watchlist_movie_ids)

    if interacted_movie_ids:
        history_movie_ids = {
            movie.id for movie in db.query(Movie).filter(
                Movie.tmdb_id.in_(interacted_movie_ids)
            ).all()
        }
        excluded_db_ids.update(history_movie_ids)

    # Genre affinity combines implicit watches with explicit user feedback.
    genre_weights = defaultdict(float)

    if interacted_movie_ids:
        watched_genres = (
            db.query(MovieGenre.genre_id)
            .join(Movie, Movie.id == MovieGenre.movie_id)
            .filter(Movie.tmdb_id.in_(interacted_movie_ids))
            .all()
        )
        for (genre_id,) in watched_genres:
            genre_weights[genre_id] += 1.0

    feedback_movie_ids = rated_movie_ids | watchlist_movie_ids
    feedback_genres = defaultdict(list)
    if feedback_movie_ids:
        feedback_rows = db.query(
            MovieGenre.movie_id, MovieGenre.genre_id
        ).filter(MovieGenre.movie_id.in_(feedback_movie_ids)).all()
        for movie_id, genre_id in feedback_rows:
            feedback_genres[movie_id].append(genre_id)

    for rating in ratings:
        # 4-5 stars strengthen a genre; 1-2 stars weaken it; 3 is neutral.
        weight = float(rating.value - 3) * 1.5
        for genre_id in feedback_genres.get(rating.movie_id, []):
            genre_weights[genre_id] += weight

    for item in watchlist_items:
        for genre_id in feedback_genres.get(item.movie_id, []):
            genre_weights[genre_id] += 1.5

    # Disliked titles are never recommended back to the user.
    disliked_movie_ids = {
        rating.movie_id for rating in ratings if rating.value <= 2
    }
    excluded_db_ids.update(disliked_movie_ids)

    # Convert excluded local catalog IDs to TMDB IDs before fusion. Filtering
    # only after top_k selection can waste slots on already-interacted movies.
    excluded_tmdb_ids = set(interacted_movie_ids)
    if excluded_db_ids:
        excluded_tmdb_ids.update(
            row[0] for row in db.query(Movie.tmdb_id).filter(
                Movie.id.in_(excluded_db_ids)
            ).all()
        )

    content = [
        tmdb_id for tmdb_id in recommend_for_user_content(user_id, db, top_k=100)
        if tmdb_id not in excluded_tmdb_ids
    ]
    collaborative_ranking = [
        tmdb_id
        for tmdb_id, _score in collaborative.recommendation_scores_for_user(
            user_id, top_k=100
        )
        if tmdb_id not in excluded_tmdb_ids
    ]

    preference_ranking = _rank_by_genre_affinity(
        db, genre_weights, excluded_db_ids, top_k=100
    )

    # Popularity is a fallback signal, not the dominant personalization input.
    popular_query = db.query(Movie)
    if excluded_db_ids:
        popular_query = popular_query.filter(~Movie.id.in_(excluded_db_ids))
    popular = popular_query.order_by(
        func.coalesce(Movie.popularity, 0).desc(),
        func.coalesce(Movie.vote_average, 0).desc(),
    ).limit(100).all()
    popularity_ranking = [movie.tmdb_id for movie in popular]

    fused_ids = reciprocal_rank_fusion(
        {
            "content": content,
            "collaborative": collaborative_ranking,
            "explicit_preferences": preference_ranking,
            "popularity": popularity_ranking,
        },
        weights={
            "content": 1.0,
            "collaborative": 1.0,
            "explicit_preferences": 1.25,
            "popularity": 0.2,
        },
        top_k=top_k,
    )
    if not fused_ids:
        return []

    # Final safety filter: never return titles already watched, rated or saved.
    excluded_tmdb_ids = set(interacted_movie_ids)
    excluded_tmdb_ids.update(
        movie.tmdb_id for movie in db.query(Movie).filter(
            Movie.id.in_(excluded_db_ids)
        ).all()
    )
    fused_ids = [mid for mid in fused_ids if mid not in excluded_tmdb_ids]
    if not fused_ids:
        return []

    movies = db.query(Movie).filter(Movie.tmdb_id.in_(fused_ids)).all()
    by_tmdb_id = {movie.tmdb_id: movie for movie in movies}
    return [by_tmdb_id[mid] for mid in fused_ids if mid in by_tmdb_id]
