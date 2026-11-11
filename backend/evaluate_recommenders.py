"""
Leakage-safe offline evaluation for DeepCine recommenders.

Run from backend/:
    python evaluate_recommenders.py --ks 5,10,20 --test-ratio 0.2

The final interactions per user are held out chronologically. ALS is fitted
only on the training interactions created by this split. Content embeddings
are catalog metadata features; no held-out interaction is used to build a
user profile.
"""
import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares
from sqlalchemy import func

from app.database.connection import SessionLocal
from app.models import Movie, MovieGenre, WatchHistory
from ai.ranking import reciprocal_rank_fusion

OUTPUT_DIR = Path(__file__).resolve().parent / "evaluation" / "results"


def temporal_holdout(events, test_ratio=0.2):
    """Split unique (user, item) interactions by each user's event time."""
    by_user = defaultdict(dict)
    for event in events:
        # Keep the latest event for repeated watches of the same movie.
        previous = by_user[event.user_id].get(event.tmdb_id)
        key = (event.watched_at or datetime.min, event.id or 0)
        if previous is None or key > previous[0]:
            by_user[event.user_id][event.tmdb_id] = (key, event)

    train, test = {}, {}
    for user_id, item_events in by_user.items():
        ordered = sorted(
            item_events.items(),
            key=lambda pair: (pair[1][0][0], pair[1][0][1]),
        )
        if len(ordered) < 2:
            continue
        n_test = max(1, int(math.ceil(len(ordered) * test_ratio)))
        n_test = min(n_test, len(ordered) - 1)
        train[user_id] = {item for item, _ in ordered[:-n_test]}
        test[user_id] = {item for item, _ in ordered[-n_test:]}
    return train, test


def precision_at_k(recommended, relevant, k):
    recs = recommended[:k]
    return len(set(recs) & relevant) / k if k else 0.0


def recall_at_k(recommended, relevant, k):
    if not relevant or not k:
        return 0.0
    return len(set(recommended[:k]) & relevant) / len(relevant)


def ndcg_at_k(recommended, relevant, k):
    if not relevant or not k:
        return 0.0
    dcg = sum(
        1.0 / math.log2(rank + 2)
        for rank, item in enumerate(recommended[:k])
        if item in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
    return dcg / idcg if idcg else 0.0


def evaluate_rankings(rankings, test, catalog, ks):
    """Macro-average ranking metrics over users with at least one test item."""
    results = {}
    evaluated_users = [
        user_id for user_id, relevant in test.items() if relevant
    ]
    for k in ks:
        rows = []
        recommended_union = set()
        for user_id in evaluated_users:
            recs = rankings.get(user_id, [])[:k]
            relevant = test[user_id]
            rows.append((
                precision_at_k(recs, relevant, k),
                recall_at_k(recs, relevant, k),
                ndcg_at_k(recs, relevant, k),
            ))
            recommended_union.update(recs)
        if rows:
            values = np.asarray(rows, dtype=float).mean(axis=0)
        else:
            values = np.zeros(3)
        results[str(k)] = {
            "precision": round(float(values[0]), 6),
            "recall": round(float(values[1]), 6),
            "ndcg": round(float(values[2]), 6),
            "coverage": round(
                len(recommended_union) / len(catalog), 6
            ) if catalog else 0.0,
            "users_evaluated": len(rows),
        }
    return results


def _normalize_rows(matrix):
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, 1e-12)


def build_rankings(db, train, catalog_movies, candidate_limit=200):
    """Build popularity, content, ALS, genre and RRF rankings from train only."""
    catalog_ids = [movie.tmdb_id for movie in catalog_movies]
    catalog_set = set(catalog_ids)
    movie_by_tmdb = {movie.tmdb_id: movie for movie in catalog_movies}

    train_items = {
        user_id: items & catalog_set for user_id, items in train.items()
    }
    train_items = {u: items for u, items in train_items.items() if items}

    popularity = sorted(
        catalog_movies,
        key=lambda m: (
            float(m.popularity or 0),
            float(m.vote_average or 0),
            int(m.tmdb_id),
        ),
        reverse=True,
    )
    popularity_ids = [m.tmdb_id for m in popularity]

    # Build user profiles from metadata embeddings of training movies only.
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [
        f"Title: {m.title}\nOverview: {m.overview or ''}\n"
        f"Language: {m.original_language or ''}"
        for m in catalog_movies
    ]
    embeddings = encoder.encode(
        texts, batch_size=64, show_progress_bar=True
    ).astype("float32")
    embeddings = _normalize_rows(embeddings)
    item_position = {tmdb_id: i for i, tmdb_id in enumerate(catalog_ids)}

    # Train ALS strictly on the temporal training partition.
    users = sorted(train_items)
    als_items = sorted(set().union(*train_items.values())) if users else []
    user_to_idx = {u: i for i, u in enumerate(users)}
    item_to_idx = {item: i for i, item in enumerate(als_items)}
    rows, cols, vals = [], [], []
    for user_id, items in train_items.items():
        for item in items:
            rows.append(user_to_idx[user_id])
            cols.append(item_to_idx[item])
            vals.append(1.0)
    interactions = csr_matrix(
        (vals, (rows, cols)), shape=(len(users), len(als_items))
    )

    als = None
    if len(users) >= 2 and len(als_items) >= 2 and interactions.nnz:
        als = AlternatingLeastSquares(
            factors=64, regularization=0.05, iterations=20,
            random_state=42, num_threads=1,
        )
        als.fit(interactions)

    # Genre affinity derived only from training movies.
    genre_rows = db.query(Movie.tmdb_id, MovieGenre.genre_id).join(
        MovieGenre, MovieGenre.movie_id == Movie.id
    ).all()
    genres_by_item = defaultdict(set)
    for tmdb_id, genre_id in genre_rows:
        genres_by_item[tmdb_id].add(genre_id)

    output = {name: {} for name in (
        "popularity", "content", "collaborative", "hybrid"
    )}
    for user_id, watched in train_items.items():
        unseen = catalog_set - watched
        output["popularity"][user_id] = [
            item for item in popularity_ids if item in unseen
        ][:candidate_limit]

        positions = [item_position[item] for item in watched
                     if item in item_position]
        if positions:
            profile = _normalize_rows(
                embeddings[positions].mean(axis=0, keepdims=True)
            )[0]
            scores = embeddings @ profile
            content_ids = sorted(
                unseen, key=lambda item: scores[item_position[item]],
                reverse=True,
            )
        else:
            content_ids = []
        output["content"][user_id] = content_ids[:candidate_limit]

        als_ids = []
        if als is not None and user_id in user_to_idx:
            user_idx = user_to_idx[user_id]
            scores = als.item_factors @ als.user_factors[user_idx]
            als_ids = [
                item for item, _ in sorted(
                    ((item, float(scores[idx]))
                     for item, idx in item_to_idx.items()
                     if item not in watched),
                    key=lambda pair: pair[1], reverse=True,
                )
            ][:candidate_limit]
        output["collaborative"][user_id] = als_ids

        genre_counts = Counter()
        for item in watched:
            genre_counts.update(genres_by_item.get(item, set()))
        genre_ids = [
            item for item in unseen
            if genres_by_item.get(item, set()) & set(genre_counts)
        ]
        genre_ids.sort(
            key=lambda item: (
                sum(genre_counts[g] for g in genres_by_item[item]),
                float(movie_by_tmdb[item].popularity or 0),
            ),
            reverse=True,
        )
        genre_ids = genre_ids[:candidate_limit]

        output["hybrid"][user_id] = reciprocal_rank_fusion(
            {
                "content": output["content"][user_id],
                "collaborative": als_ids,
                "genre": genre_ids,
                "popularity": output["popularity"][user_id],
            },
            weights={
                "content": 1.0,
                "collaborative": 1.0,
                "genre": 0.65,
                "popularity": 0.25,
            },
            top_k=candidate_limit,
        )
    return output


def run_evaluation(test_ratio=0.2, ks=(5, 10, 20)):
    db = SessionLocal()
    try:
        events = db.query(WatchHistory).order_by(
            WatchHistory.watched_at.asc(), WatchHistory.id.asc()
        ).all()
        train, test = temporal_holdout(events, test_ratio)
        if not test:
            raise RuntimeError(
                "Not enough users with at least two distinct catalog watches. "
                "Collect more watch-history data before evaluating."
            )

        catalog_movies = db.query(Movie).filter(
            Movie.tmdb_id.isnot(None)
        ).all()
        catalog_ids = {m.tmdb_id for m in catalog_movies}
        test = {
            user_id: relevant & catalog_ids
            for user_id, relevant in test.items()
        }
        test = {u: items for u, items in test.items() if items}
        if not test:
            raise RuntimeError(
                "Held-out interactions do not match movies in the catalog."
            )

        rankings = build_rankings(db, train, catalog_movies)
        metrics = {
            model_name: evaluate_rankings(model_rankings, test, catalog_ids, ks)
            for model_name, model_rankings in rankings.items()
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        payload = {
            "generated_at_utc": timestamp,
            "methodology": {
                "split": "per-user chronological holdout",
                "test_ratio": test_ratio,
                "als_fit_data": "training interactions only",
                "user_profile_data": "training interactions only",
                "metrics": ["precision", "recall", "ndcg", "coverage"],
                "ks": list(ks),
                "candidate_universe": "movies in local catalog",
                "users_with_train_and_test": len(test),
                "catalog_size": len(catalog_ids),
                "train_interactions": sum(map(len, train.values())),
                "test_interactions": sum(map(len, test.values())),
            },
            "models": metrics,
            "notes": [
                "Coverage is the fraction of catalog items recommended "
                "across evaluated users at K.",
                "Metrics are macro-averaged across evaluated users.",
                "This evaluates watch-history retrieval, not explicit rating "
                "prediction or user satisfaction.",
                "RRF weights are current hand-set weights, not tuned values.",
            ],
        }
        json_path = OUTPUT_DIR / f"metrics_{timestamp}.json"
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        csv_path = OUTPUT_DIR / f"metrics_{timestamp}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "model", "k", "precision", "recall", "ndcg",
                "coverage", "users_evaluated",
            ])
            for model_name, by_k in metrics.items():
                for k, values in by_k.items():
                    writer.writerow([
                        model_name, k, values["precision"], values["recall"],
                        values["ndcg"], values["coverage"],
                        values["users_evaluated"],
                    ])

        print(json.dumps(payload, indent=2))
        print(f"\nSaved JSON: {json_path}")
        print(f"Saved CSV:  {csv_path}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--ks", default="5,10,20")
    args = parser.parse_args()
    if not 0.05 <= args.test_ratio <= 0.5:
        parser.error("--test-ratio must be between 0.05 and 0.5")
    ks = tuple(sorted({int(value) for value in args.ks.split(",")}))
    if not ks or any(k <= 0 for k in ks):
        parser.error("--ks must contain positive integers")
    run_evaluation(args.test_ratio, ks)
