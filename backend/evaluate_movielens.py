"""
MovieLens offline benchmark for the current DeepCine catalog.

Run from backend/:
    python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv \
        --links-path ../datasets/movielens/links.csv --ks 5,10,20

This benchmark is deliberately separate from production watch_history.
It maps MovieLens movieId -> TMDB ID, restricts candidates and ground truth
to the catalog overlap, keeps each user's latest rating per movie, treats
ratings >= the configured threshold as positive, and performs a per-user
chronological holdout. ALS and all interaction-derived signals use train only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares

from app.database.connection import SessionLocal
from app.models import Movie, MovieGenre
from ai.ranking import reciprocal_rank_fusion

OUTPUT_DIR = Path(__file__).resolve().parent / "evaluation" / "results"


def load_movie_mapping(links_path: str | Path, catalog_tmdb_ids: set[int]):
    """Return MovieLens movieId -> catalog TMDB ID for valid overlap only."""
    links = pd.read_csv(links_path, usecols=["movieId", "tmdbId"])
    links["movieId"] = pd.to_numeric(links["movieId"], errors="coerce")
    links["tmdbId"] = pd.to_numeric(links["tmdbId"], errors="coerce")
    links = links.dropna(subset=["movieId", "tmdbId"])
    links["movieId"] = links["movieId"].astype("int64")
    links["tmdbId"] = links["tmdbId"].astype("int64")
    links = links[links["tmdbId"].isin(catalog_tmdb_ids)]
    # A MovieLens movieId should map to one TMDB ID. Keep first defensively.
    links = links.drop_duplicates(subset=["movieId"], keep="first")
    return dict(zip(links["movieId"], links["tmdbId"]))


def load_latest_ratings(
    ratings_path: str | Path,
    movie_mapping: dict[int, int],
    chunksize: int = 500_000,
):
    """
    Stream ratings and retain the latest rating for each user/TMDB pair.

    Latest rating is selected before applying the positive threshold so an
    older 5-star rating cannot override a later negative rating.
    """
    latest = {}
    total_rows = 0
    matched_rows = 0
    for chunk in pd.read_csv(
        ratings_path,
        usecols=["userId", "movieId", "rating", "timestamp"],
        chunksize=chunksize,
    ):
        total_rows += len(chunk)
        chunk["movieId"] = pd.to_numeric(chunk["movieId"], errors="coerce")
        chunk = chunk.dropna(subset=["movieId"])
        chunk["movieId"] = chunk["movieId"].astype("int64")
        chunk = chunk[chunk["movieId"].isin(movie_mapping)]
        matched_rows += len(chunk)
        if chunk.empty:
            continue
        chunk["tmdb_id"] = chunk["movieId"].map(movie_mapping)
        chunk = chunk.sort_values("timestamp").drop_duplicates(
            ["userId", "tmdb_id"], keep="last"
        )
        for row in chunk.itertuples(index=False):
            key = (int(row.userId), int(row.tmdb_id))
            timestamp = int(row.timestamp)
            previous = latest.get(key)
            if previous is None or timestamp >= previous[0]:
                latest[key] = (timestamp, float(row.rating))
    return latest, {
        "ratings_rows_scanned": total_rows,
        "ratings_rows_matching_catalog": matched_rows,
        "latest_user_movie_pairs": len(latest),
    }


def build_temporal_split(latest_ratings, positive_threshold=4.0, test_ratio=0.2):
    """Create positive-only per-user chronological train/test item sets."""
    by_user = defaultdict(list)
    positive_pairs = 0
    for (user_id, tmdb_id), (timestamp, rating) in latest_ratings.items():
        if rating >= positive_threshold:
            by_user[user_id].append((timestamp, tmdb_id))
            positive_pairs += 1

    train, test = {}, {}
    for user_id, events in by_user.items():
        events.sort(key=lambda item: (item[0], item[1]))
        # One interaction per movie is already guaranteed by latest_ratings.
        if len(events) < 2:
            continue
        n_test = max(1, int(math.ceil(len(events) * test_ratio)))
        n_test = min(n_test, len(events) - 1)
        train[user_id] = {item for _, item in events[:-n_test]}
        test[user_id] = {item for _, item in events[-n_test:]}
    return train, test, {
        "users_with_at_least_two_positive_movies": len(train),
        "positive_user_movie_pairs": positive_pairs,
        "train_interactions": sum(map(len, train.values())),
        "test_interactions": sum(map(len, test.values())),
    }


def precision_at_k(recommended, relevant, k):
    return len(set(recommended[:k]) & relevant) / k if k > 0 else 0.0


def recall_at_k(recommended, relevant, k):
    if not relevant or k <= 0:
        return 0.0
    return len(set(recommended[:k]) & relevant) / len(relevant)


def ndcg_at_k(recommended, relevant, k):
    if not relevant or k <= 0:
        return 0.0
    dcg = sum(
        1.0 / math.log2(rank + 2)
        for rank, item in enumerate(recommended[:k])
        if item in relevant
    )
    ideal = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal))
    return dcg / idcg if idcg else 0.0


def evaluate_rankings(rankings, test, candidate_catalog, ks):
    """Macro-average user metrics; coverage denominator is overlap catalog."""
    users = [user for user, relevant in test.items() if relevant]
    output = {}
    for k in ks:
        metric_rows = []
        recommended_union = set()
        for user in users:
            recs = rankings.get(user, [])[:k]
            relevant = test[user]
            metric_rows.append((
                precision_at_k(recs, relevant, k),
                recall_at_k(recs, relevant, k),
                ndcg_at_k(recs, relevant, k),
            ))
            recommended_union.update(recs)
        means = np.asarray(metric_rows, dtype=float).mean(axis=0) if metric_rows else np.zeros(3)
        output[str(k)] = {
            "precision": round(float(means[0]), 6),
            "recall": round(float(means[1]), 6),
            "ndcg": round(float(means[2]), 6),
            "coverage": round(len(recommended_union) / len(candidate_catalog), 6)
            if candidate_catalog else 0.0,
            "users_evaluated": len(users),
        }
    return output


def _normalize_rows(matrix):
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, 1e-12)


def build_model_rankings(db, train, catalog_movies, ks_max, als_factors=64):
    """Build four recommenders using only the temporal training interactions."""
    catalog_ids = {movie.tmdb_id for movie in catalog_movies}
    movies = {movie.tmdb_id: movie for movie in catalog_movies}
    train = {
        user: items & catalog_ids for user, items in train.items()
    }
    train = {user: items for user, items in train.items() if items}

    # MovieLens popularity baseline: positive training interaction count.
    item_counts = Counter(item for items in train.values() for item in items)
    popularity_order = sorted(
        catalog_ids,
        key=lambda item: (item_counts[item], float(movies[item].popularity or 0), item),
        reverse=True,
    )

    # Metadata embeddings are item features; user profiles use train items only.
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    ordered_ids = sorted(catalog_ids)
    texts = [
        f"Title: {movies[item].title}\nOverview: {movies[item].overview or ''}\n"
        f"Language: {movies[item].original_language or ''}"
        for item in ordered_ids
    ]
    embeddings = encoder.encode(
        texts, batch_size=64, show_progress_bar=True
    ).astype("float32")
    embeddings = _normalize_rows(embeddings)
    item_pos = {item: index for index, item in enumerate(ordered_ids)}

    # ALS fit on training interactions only. Unseen candidates are not scored
    # by ALS, so hybrid/content/popularity provide cold-start coverage.
    users = sorted(train)
    als_items = sorted(set().union(*train.values())) if users else []
    user_pos = {user: idx for idx, user in enumerate(users)}
    als_item_pos = {item: idx for idx, item in enumerate(als_items)}
    rows, cols = [], []
    for user, items in train.items():
        for item in items:
            rows.append(user_pos[user])
            cols.append(als_item_pos[item])
    matrix = csr_matrix(
        (np.ones(len(rows), dtype=np.float32), (rows, cols)),
        shape=(len(users), len(als_items)),
    )
    als = None
    if len(users) >= 2 and len(als_items) >= 2 and matrix.nnz:
        als = AlternatingLeastSquares(
            factors=als_factors, regularization=0.05,
            iterations=20, random_state=42, num_threads=1,
        )
        als.fit(matrix)

    genre_rows = db.query(Movie.tmdb_id, MovieGenre.genre_id).join(
        MovieGenre, MovieGenre.movie_id == Movie.id
    ).filter(Movie.tmdb_id.in_(catalog_ids)).all()
    genres_by_item = defaultdict(set)
    for tmdb_id, genre_id in genre_rows:
        genres_by_item[tmdb_id].add(genre_id)

    names = ("popularity", "content", "collaborative", "hybrid")
    rankings = {name: {} for name in names}
    candidate_limit = min(len(catalog_ids), max(ks_max * 10, 100))

    for user, watched in train.items():
        unseen = catalog_ids - watched
        pop = [item for item in popularity_order if item in unseen][:candidate_limit]

        positions = [item_pos[item] for item in watched]
        profile = _normalize_rows(embeddings[positions].mean(axis=0, keepdims=True))[0]
        scores = embeddings @ profile
        content = sorted(
            unseen, key=lambda item: float(scores[item_pos[item]]), reverse=True
        )[:candidate_limit]

        collaborative = []
        if als is not None and user in user_pos:
            user_vector = als.user_factors[user_pos[user]]
            item_scores = als.item_factors @ user_vector
            collaborative = [
                item for item, _ in sorted(
                    ((item, float(item_scores[als_item_pos[item]]))
                     for item in als_items if item not in watched),
                    key=lambda pair: pair[1], reverse=True,
                )[:candidate_limit]
            ]

        genre_counts = Counter()
        for item in watched:
            genre_counts.update(genres_by_item.get(item, set()))
        preferred_genres = set(genre_counts)
        genre_ranked = [
            item for item in unseen
            if genres_by_item.get(item, set()) & preferred_genres
        ]
        genre_ranked.sort(
            key=lambda item: (
                sum(genre_counts[g] for g in genres_by_item[item]),
                item_counts[item],
            ),
            reverse=True,
        )
        genre_ranked = genre_ranked[:candidate_limit]

        rankings["popularity"][user] = pop
        rankings["content"][user] = content
        rankings["collaborative"][user] = collaborative
        rankings["hybrid"][user] = reciprocal_rank_fusion(
            {
                "content": content,
                "collaborative": collaborative,
                "genre": genre_ranked,
                "popularity": pop,
            },
            weights={"content": 1.0, "collaborative": 1.0,
                     "genre": 0.65, "popularity": 0.25},
            top_k=candidate_limit,
        )
    return rankings


def run(args):
    db = SessionLocal()
    try:
        catalog_movies = db.query(Movie).filter(Movie.tmdb_id.isnot(None)).all()
        catalog_by_id = {int(movie.tmdb_id): movie for movie in catalog_movies}
        catalog_ids = set(catalog_by_id)
        if not catalog_ids:
            raise RuntimeError("DeepCine catalog is empty; import movies first.")

        mapping = load_movie_mapping(args.links_path, catalog_ids)
        if not mapping:
            raise RuntimeError("No MovieLens/TMDB IDs overlap with the DeepCine catalog.")

        latest, scan_stats = load_latest_ratings(
            args.ratings_path, mapping, chunksize=args.chunksize
        )
        train, test, split_stats = build_temporal_split(
            latest, args.positive_threshold, args.test_ratio
        )
        overlap_ids = set(mapping.values())
        train = {u: items & overlap_ids for u, items in train.items()}
        test = {u: items & overlap_ids for u, items in test.items()}
        eligible = {
            u for u in train.keys() & test.keys()
            if train[u] and test[u]
        }
        train = {u: train[u] for u in eligible}
        test = {u: test[u] for u in eligible}
        if not eligible:
            raise RuntimeError(
                "No eligible users remain after catalog-overlap filtering. "
                "Lower the positive threshold or expand the catalog."
            )

        overlap_movies = [catalog_by_id[item] for item in sorted(overlap_ids)]
        rankings = build_model_rankings(db, train, overlap_movies, max(args.ks))
        metrics = {
            name: evaluate_rankings(model_rankings, test, overlap_ids, args.ks)
            for name, model_rankings in rankings.items()
        }

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at_utc": timestamp,
            "dataset": {
                "ratings_file": str(args.ratings_path),
                "links_file": str(args.links_path),
                "positive_rating_threshold": args.positive_threshold,
                "chunksize": args.chunksize,
            },
            "catalog": {
                "deepcine_catalog_movies": len(catalog_ids),
                "movielens_movies_with_tmdb_id_in_catalog": len(overlap_ids),
                "catalog_overlap_fraction": round(len(overlap_ids) / len(catalog_ids), 6),
                "candidate_catalog_size": len(overlap_ids),
            },
            "scan": scan_stats,
            "split": {
                "method": "per-user chronological holdout after latest-rating deduplication",
                "test_ratio": args.test_ratio,
                **split_stats,
                "eligible_users": len(eligible),
                "eligible_train_interactions": sum(map(len, train.values())),
                "eligible_test_interactions": sum(map(len, test.values())),
            },
            "evaluation": {
                "metrics": ["precision", "recall", "ndcg", "coverage"],
                "ks": args.ks,
                "averaging": "macro average over eligible users",
                "coverage_denominator": "MovieLens/DeepCine overlapping catalog",
                "als_training_data": "positive training interactions only",
                "user_profiles": "positive training interactions only",
            },
            "models": metrics,
            "limitations": [
                "Only 197 overlapping movies were present in the observed catalog; "
                "results do not represent the full DeepCine catalog.",
                "Ratings >= threshold are treated as implicit positives; this is "
                "not explicit rating prediction.",
                "MovieLens users and interactions are external benchmark data, not "
                "production DeepCine users or watch history.",
                "The RRF weights are fixed configuration values and have not been tuned.",
            ],
        }

        json_path = OUTPUT_DIR / f"movielens_metrics_{timestamp}.json"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        csv_path = OUTPUT_DIR / f"movielens_metrics_{timestamp}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["model", "k", "precision", "recall", "ndcg",
                             "coverage", "users_evaluated"])
            for model, by_k in metrics.items():
                for k, values in by_k.items():
                    writer.writerow([model, k, values["precision"], values["recall"],
                                     values["ndcg"], values["coverage"],
                                     values["users_evaluated"]])
        print(json.dumps(payload, indent=2))
        print(f"\nSaved JSON: {json_path}")
        print(f"Saved CSV:  {csv_path}")
    finally:
        db.close()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ratings-path", default="../datasets/movielens/ratings.csv")
    parser.add_argument("--links-path", default="../datasets/movielens/links.csv")
    parser.add_argument("--positive-threshold", type=float, default=4.0)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--ks", default="5,10,20")
    args = parser.parse_args()
    if not 0.05 <= args.test_ratio <= 0.5:
        parser.error("--test-ratio must be between 0.05 and 0.5")
    if args.chunksize <= 0:
        parser.error("--chunksize must be positive")
    args.ks = tuple(sorted({int(value) for value in args.ks.split(",")}))
    if not args.ks or any(k <= 0 for k in args.ks):
        parser.error("--ks must contain positive integers")
    if args.positive_threshold < 0 or args.positive_threshold > 5:
        parser.error("--positive-threshold must be between 0 and 5")
    return args


if __name__ == "__main__":
    run(parse_args())
