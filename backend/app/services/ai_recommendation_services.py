from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    WatchHistory, Movie, MovieGenre, Genre, Rating, WatchlistItem
)
from ai import collaborative
from ai.recommender import recommend_for_user_content
from ai.ranking import reciprocal_rank_fusion, diversify_by_genre


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
    """Fuse behavioral, rating, watchlist, collaborative and popularity signals."""
    if top_k <= 0:
        return []

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
        weight = float(rating.value - 3) * 1.5
        for genre_id in feedback_genres.get(rating.movie_id, []):
            genre_weights[genre_id] += weight

    for item in watchlist_items:
        for genre_id in feedback_genres.get(item.movie_id, []):
            genre_weights[genre_id] += 1.5

    disliked_movie_ids = {
        rating.movie_id for rating in ratings if rating.value <= 2
    }
    excluded_db_ids.update(disliked_movie_ids)

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
        top_k=max(top_k * 5, top_k),
    )
    fused_ids = [
        mid for mid in fused_ids if mid not in excluded_tmdb_ids
    ]
    if not fused_ids:
        return []

    # MMR-style reranking trades a controlled amount of rank relevance for
    # genre variety. Missing genre metadata contributes no redundancy penalty.
    genre_rows = (
        db.query(Movie.tmdb_id, MovieGenre.genre_id)
        .join(MovieGenre, MovieGenre.movie_id == Movie.id)
        .filter(Movie.tmdb_id.in_(fused_ids))
        .all()
    )
    genres_by_item = defaultdict(set)
    for tmdb_id, genre_id in genre_rows:
        genres_by_item[tmdb_id].add(genre_id)

    diversified_ids = diversify_by_genre(
        fused_ids,
        genres_by_item,
        top_k=top_k,
        relevance_weight=0.8,
    )
    movies = db.query(Movie).filter(Movie.tmdb_id.in_(diversified_ids)).all()
    by_tmdb_id = {movie.tmdb_id: movie for movie in movies}
    return [by_tmdb_id[mid] for mid in diversified_ids if mid in by_tmdb_id]


def build_recommendation_explanations(user_id: int, movies, db: Session):
    """Explain recommendations using observed positive user signals and genres."""
    if not movies:
        return {}

    positive_movie_ids = set(
        row[0] for row in db.query(Movie.id)
        .join(WatchHistory, WatchHistory.tmdb_id == Movie.tmdb_id)
        .filter(WatchHistory.user_id == user_id)
        .all()
    )
    positive_movie_ids.update(
        row[0] for row in db.query(Rating.movie_id).filter(
            Rating.user_id == user_id,
            Rating.value >= 4,
        ).all()
    )
    positive_movie_ids.update(
        row[0] for row in db.query(WatchlistItem.movie_id).filter(
            WatchlistItem.user_id == user_id
        ).all()
    )
    # Do not use explicitly disliked titles as positive evidence for an explanation.
    negative_movie_ids = {
        row[0] for row in db.query(Rating.movie_id).filter(
            Rating.user_id == user_id,
            Rating.value <= 2,
        ).all()
    }
    positive_movie_ids.difference_update(negative_movie_ids)

    positive_genre_ids = set()
    if positive_movie_ids:
        preference_rows = (
            db.query(Genre.id, Genre.name)
            .join(MovieGenre, MovieGenre.genre_id == Genre.id)
            .filter(MovieGenre.movie_id.in_(positive_movie_ids))
            .distinct()
            .all()
        )
        positive_genre_ids = {genre_id for genre_id, _name in preference_rows}
        genre_names.update({genre_id: name for genre_id, name in preference_rows})

    candidate_ids = [movie.id for movie in movies]
    candidate_genres = defaultdict(list)
    rows = (
        db.query(Movie.id, Genre.id, Genre.name)
        .join(MovieGenre, MovieGenre.movie_id == Movie.id)
        .join(Genre, Genre.id == MovieGenre.genre_id)
        .filter(Movie.id.in_(candidate_ids))
        .all()
    )
    for movie_id, genre_id, genre_name in rows:
        candidate_genres[movie_id].append((genre_id, genre_name))

    explanations = {}
    for movie in movies:
        matched = [
            name for genre_id, name in candidate_genres.get(movie.id, [])
            if genre_id in positive_genre_ids
        ]
        if matched:
            explanations[movie.tmdb_id] = (
                "Matches genres from your watched, highly rated, or saved movies: "
                + ", ".join(matched[:2])
            )
        else:
            explanations[movie.tmdb_id] = (
                "Selected by the personalized ranking model using the available signals."
            )
    return explanations
