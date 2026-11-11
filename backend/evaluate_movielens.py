"""
Leakage-aware MovieLens recommender benchmark for DeepCine.

Run from backend/:
  python evaluate_movielens.py --ratings-path ../datasets/movielens/ratings.csv \
      --links-path ../datasets/movielens/links.csv --ks 5,10,20

The benchmark is isolated from production watch_history. It uses a per-user
chronological train/validation/test split. Model fitting and user profiles
use train only; RRF weights are selected on validation only; final metrics
are computed once on the held-out test partition.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares
from threadpoolctl import threadpool_limits

from app.database.connection import SessionLocal
from app.models import Movie, MovieGenre
from ai.ranking import reciprocal_rank_fusion

OUTPUT_DIR = Path(__file__).resolve().parent / "evaluation" / "results"
DEFAULT_WEIGHTS = {
    "content": 1.0,
    "collaborative": 1.0,
    "genre": 0.65,
    "popularity": 0.25,
}
WEIGHT_GRID = (0.5, 1.0, 2.0)
DEFAULT_EVALUATION_USER_SAMPLE_SIZE = 2_000
TUNING_USER_SAMPLE_SIZE = 2_000


def load_movie_mapping(links_path: str | Path, catalog_tmdb_ids: set[int]):
    links = pd.read_csv(links_path, usecols=["movieId", "tmdbId"])
    links["movieId"] = pd.to_numeric(links["movieId"], errors="coerce")
    links["tmdbId"] = pd.to_numeric(links["tmdbId"], errors="coerce")
    links = links.dropna(subset=["movieId", "tmdbId"])
    links["movieId"] = links["movieId"].astype("int64")
    links["tmdbId"] = links["tmdbId"].astype("int64")
    links = links[links["tmdbId"].isin(catalog_tmdb_ids)]
    links = links.drop_duplicates(subset=["movieId"], keep="first")
    return dict(zip(links["movieId"], links["tmdbId"]))


def load_latest_ratings(ratings_path, movie_mapping, chunksize=500_000):
    """Stream ratings; latest timestamp wins before positive filtering."""
    latest = {}
    total_rows = matched_rows = 0
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


def build_temporal_split(
    latest_ratings, positive_threshold=4.0,
    train_ratio=0.6, validation_ratio=0.2, test_ratio=0.2,
):
    """
    Per-user chronological 3-way split.

    Users need >=3 positive catalog interactions so every partition has at
    least one item. Rounding is deterministic and leaves at least one item
    in each partition.
    """
    ratios = (train_ratio, validation_ratio, test_ratio)
    if any(value <= 0 for value in ratios) or not math.isclose(sum(ratios), 1.0):
        raise ValueError("train/validation/test ratios must be positive and sum to 1")
    by_user = defaultdict(list)
    positive_pairs = 0
    for (user_id, tmdb_id), (timestamp, rating) in latest_ratings.items():
        if rating >= positive_threshold:
            by_user[user_id].append((timestamp, tmdb_id))
            positive_pairs += 1

    train, validation, test = {}, {}, {}
    excluded_users = 0
    for user_id, events in by_user.items():
        events.sort(key=lambda item: (item[0], item[1]))
        n = len(events)
        if n < 3:
            excluded_users += 1
            continue
        n_test = max(1, int(math.floor(n * test_ratio)))
        n_validation = max(1, int(math.floor(n * validation_ratio)))
        while n_test + n_validation >= n:
            if n_test > 1:
                n_test -= 1
            else:
                n_validation -= 1
        n_train = n - n_validation - n_test
        train[user_id] = {item for _, item in events[:n_train]}
        validation[user_id] = {
            item for _, item in events[n_train:n_train + n_validation]
        }
        test[user_id] = {item for _, item in events[n_train + n_validation:]}

    return train, validation, test, {
        "positive_user_movie_pairs": positive_pairs,
        "eligible_users": len(train),
        "excluded_users_fewer_than_three_positive_items": excluded_users,
        "train_interactions": sum(map(len, train.values())),
        "validation_interactions": sum(map(len, validation.values())),
        "test_interactions": sum(map(len, test.values())),
    }


def sample_evaluation_users(user_ids, sample_size=2_000, seed=42):
    """Return a deterministic uniform sample, or all users when below the limit."""
    users = sorted(user_ids)
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if len(users) <= sample_size:
        return users
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(users, size=sample_size, replace=False).tolist())


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


def per_user_ranking_metrics(rankings, relevant_by_user, k):
    """Return aligned per-user metrics for paired statistical comparisons."""
    return {
        user: {
            "precision": precision_at_k(rankings.get(user, [])[:k], relevant, k),
            "recall": recall_at_k(rankings.get(user, [])[:k], relevant, k),
            "ndcg": ndcg_at_k(rankings.get(user, [])[:k], relevant, k),
        }
        for user, relevant in relevant_by_user.items() if relevant
    }


def bootstrap_mean_ci(values, seed=42, samples=1000, confidence=0.95):
    """Percentile bootstrap confidence interval for a mean."""
    values = np.asarray(list(values), dtype=float)
    if not len(values):
        return {"lower": 0.0, "upper": 0.0}
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(samples, len(values)))
    means = values[indices].mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    return {
        "lower": round(float(np.quantile(means, alpha)), 6),
        "upper": round(float(np.quantile(means, 1.0 - alpha)), 6),
    }


def paired_bootstrap_difference_ci(left, right, metric, seed=42, samples=1000):
    """CI for left-minus-right using paired resampling of the same users."""
    users = sorted(set(left) & set(right))
    if not users:
        return {"lower": 0.0, "upper": 0.0}
    differences = [left[user][metric] - right[user][metric] for user in users]
    return bootstrap_mean_ci(differences, seed=seed, samples=samples)


def evaluate_rankings(rankings, relevant_by_user, candidate_catalog, ks, bootstrap_seed=42):
    users = [u for u, items in relevant_by_user.items() if items]
    output = {}
    for k in ks:
        per_user = per_user_ranking_metrics(rankings, relevant_by_user, k)
        rows = list(per_user.values())
        recommended_union = {
            item for user in users for item in rankings.get(user, [])[:k]
        }
        means = np.asarray([
            [row["precision"], row["recall"], row["ndcg"]] for row in rows
        ], dtype=float).mean(axis=0) if rows else np.zeros(3)
        output[str(k)] = {
            "precision": round(float(means[0]), 6),
            "recall": round(float(means[1]), 6),
            "ndcg": round(float(means[2]), 6),
            "precision_ci95": bootstrap_mean_ci(
                (row["precision"] for row in rows), seed=bootstrap_seed + k
            ),
            "recall_ci95": bootstrap_mean_ci(
                (row["recall"] for row in rows), seed=bootstrap_seed + 100 + k
            ),
            "ndcg_ci95": bootstrap_mean_ci(
                (row["ndcg"] for row in rows), seed=bootstrap_seed + 200 + k
            ),
            "coverage": round(len(recommended_union) / len(candidate_catalog), 6)
            if candidate_catalog else 0.0,
            "users_evaluated": len(users),
        }
    return output

def _normalize_rows(matrix):
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, 1e-12)


def select_ranking_users(train, ranking_users=None):
    """Select users to score without changing the training population."""
    users = sorted(train) if ranking_users is None else sorted(set(ranking_users))
    missing = set(users) - set(train)
    if missing:
        raise ValueError(f"ranking_users contains {len(missing)} users absent from train")
    return users


def build_signal_rankings(
    db, train, catalog_movies, ks_max, als_factors=64, seed=42,
    ranking_users=None,
):
    """Fit signals on all training users; materialize rankings only for selected users."""
    catalog_ids = {int(movie.tmdb_id) for movie in catalog_movies}
    movies = {int(movie.tmdb_id): movie for movie in catalog_movies}
    train = {u: (items & catalog_ids) for u, items in train.items()}
    train = {u: items for u, items in train.items() if items}

    item_counts = Counter(item for items in train.values() for item in items)
    global_popularity_order = sorted(
        catalog_ids,
        key=lambda item: (item_counts[item], float(movies[item].popularity or 0), item),
        reverse=True,
    )

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
    item_pos = {item: idx for idx, item in enumerate(ordered_ids)}

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
            factors=als_factors, regularization=0.05, iterations=20,
            random_state=seed, num_threads=1,
        )
        # Prevent nested BLAS/OpenMP pools from oversubscribing CPU threads.
        with threadpool_limits(limits=1):
            als.fit(matrix)

    genre_rows = db.query(Movie.tmdb_id, MovieGenre.genre_id).join(
        MovieGenre, MovieGenre.movie_id == Movie.id
    ).filter(Movie.tmdb_id.in_(catalog_ids)).all()
    genres_by_item = defaultdict(set)
    for tmdb_id, genre_id in genre_rows:
        genres_by_item[int(tmdb_id)].add(genre_id)

    signal_names = (
        "global_popularity", "personalized_popularity", "content",
        "collaborative", "genre",
    )
    signals = {name: {} for name in signal_names}
    candidate_limit = min(len(catalog_ids), max(ks_max * 10, 100))

    users_to_rank = select_ranking_users(train, ranking_users)

    for user in users_to_rank:
        watched = train[user]
        unseen = catalog_ids - watched
        global_pop = [i for i in global_popularity_order if i in unseen][:candidate_limit]

        # Personalized popularity: training interaction popularity, boosted
        # by overlap with this user's training-derived genre profile.
        genre_counts = Counter()
        for item in watched:
            genre_counts.update(genres_by_item.get(item, set()))
        preferred = set(genre_counts)
        def personalized_score(item):
            item_genres = genres_by_item.get(item, set())
            affinity = sum(genre_counts[g] for g in item_genres)
            return (affinity, item_counts[item], float(movies[item].popularity or 0), item)
        personalized_pop = sorted(
            unseen, key=personalized_score, reverse=True
        )[:candidate_limit]

        positions = [item_pos[item] for item in watched]
        profile = _normalize_rows(
            embeddings[positions].mean(axis=0, keepdims=True)
        )[0]
        content_scores = embeddings @ profile
        content = sorted(
            unseen,
            key=lambda item: (float(content_scores[item_pos[item]]), item),
            reverse=True,
        )[:candidate_limit]

        collaborative = []
        if als is not None and user in user_pos:
            with threadpool_limits(limits=1):
                user_vector = als.user_factors[user_pos[user]]
                item_scores = als.item_factors @ user_vector
            collaborative = sorted(
                (item for item in als_items if item not in watched),
                key=lambda item: (float(item_scores[als_item_pos[item]]), item),
                reverse=True,
            )[:candidate_limit]

        genre_ranked = [
            item for item in unseen
            if genres_by_item.get(item, set()) & preferred
        ]
        genre_ranked.sort(
            key=lambda item: (
                sum(genre_counts[g] for g in genres_by_item[item]),
                item_counts[item],
                item,
            ),
            reverse=True,
        )
        signals["global_popularity"][user] = global_pop
        signals["personalized_popularity"][user] = personalized_pop
        signals["content"][user] = content
        signals["collaborative"][user] = collaborative
        signals["genre"][user] = genre_ranked[:candidate_limit]
    return signals


def fuse_hybrid(signal_rankings, weights, top_k, users=None):
    hybrid = {}
    selected_users = (
        users if users is not None else signal_rankings["content"].keys()
    )
    for user in selected_users:
        signals = signal_rankings["content"].get(user, [])
        hybrid[user] = reciprocal_rank_fusion(
            {
                "content": signals,
                "collaborative": signal_rankings["collaborative"].get(user, []),
                "genre": signal_rankings["genre"].get(user, []),
                "popularity": signal_rankings["global_popularity"].get(user, []),
            },
            weights=weights,
            top_k=top_k,
        )
    return hybrid


def tune_hybrid_weights(signal_rankings, validation, ks, candidate_catalog, seed=42):
    """Select RRF weights on validation NDCG@10 (or largest available K)."""
    objective_k = 10 if 10 in ks else max(ks)
    # Tuning over every validation user for every grid point is needlessly
    # expensive at MovieLens scale. Use a deterministic, sorted user sample;
    # final validation/test reporting still uses every eligible user.
    available_users = sorted(validation)
    rng = np.random.default_rng(seed)
    if len(available_users) > TUNING_USER_SAMPLE_SIZE:
        sampled_users = sorted(
            rng.choice(available_users, size=TUNING_USER_SAMPLE_SIZE, replace=False).tolist()
        )
    else:
        sampled_users = available_users
    tuning_validation = {u: validation[u] for u in sampled_users}
    best = None
    tested = 0
    for values in itertools.product(WEIGHT_GRID, repeat=4):
        weights = dict(zip(
            ("content", "collaborative", "genre", "popularity"), values
        ))
        candidate = fuse_hybrid(
            signal_rankings, weights, max(ks) * 10, users=sampled_users
        )
        metrics = evaluate_rankings(candidate, tuning_validation, candidate_catalog, [objective_k])
        score = metrics[str(objective_k)]["ndcg"]
        tested += 1
        # Deterministic tie-break: NDCG, precision, then prefer lower total weight.
        precision = metrics[str(objective_k)]["precision"]
        key = (score, precision, -sum(values))
        if best is None or key > best["key"]:
            best = {"key": key, "weights": weights, "metrics": metrics}
    return {
        "objective": f"validation_ndcg_at_{objective_k}",
        "objective_score": best["key"][0],
        "validation_precision_at_objective_k": best["key"][1],
        "weights": best["weights"],
        "weight_grid": list(WEIGHT_GRID),
        "configurations_tested": tested,
        "tuning_users_sampled": len(sampled_users),
        "tuning_user_sample_method": "seeded uniform sample without replacement",
        "tuning_seed": seed,
        "validation_metrics_at_objective_k": best["metrics"],
    }


def run(args):
    db = SessionLocal()
    try:
        catalog_movies = db.query(Movie).filter(Movie.tmdb_id.isnot(None)).all()
        catalog_by_id = {int(m.tmdb_id): m for m in catalog_movies}
        catalog_ids = set(catalog_by_id)
        if not catalog_ids:
            raise RuntimeError("DeepCine catalog is empty; import movies first.")

        mapping = load_movie_mapping(args.links_path, catalog_ids)
        if not mapping:
            raise RuntimeError("No MovieLens/TMDB IDs overlap with the DeepCine catalog.")

        latest, scan_stats = load_latest_ratings(
            args.ratings_path, mapping, chunksize=args.chunksize
        )
        train, validation, test, split_stats = build_temporal_split(
            latest, positive_threshold=args.positive_threshold,
            train_ratio=args.train_ratio,
            validation_ratio=args.validation_ratio,
            test_ratio=args.test_ratio,
        )
        overlap_ids = set(mapping.values())
        eligible = {
            user for user in train.keys() & validation.keys() & test.keys()
            if train[user] & overlap_ids
            and validation[user] & overlap_ids
            and test[user] & overlap_ids
        }
        if not eligible:
            raise RuntimeError(
                "No eligible users after overlap filtering. Expand the catalog "
                "or check the positive threshold and MovieLens mapping."
            )

        eligible_user_count = len(eligible)
        sampled_users = sample_evaluation_users(
            eligible, sample_size=args.evaluation_users, seed=args.evaluation_seed
        )
        # Fit ALS and all train-derived popularity statistics on the full
        # eligible training population. Only materialize per-user rankings for
        # the sampled evaluation users to keep ranking work bounded.
        validation = {u: validation[u] & overlap_ids for u in sampled_users}
        test = {u: test[u] & overlap_ids for u in sampled_users}

        overlap_movies = [catalog_by_id[item] for item in sorted(overlap_ids)]
        signals = build_signal_rankings(
            db, train, overlap_movies, max(args.ks),
            als_factors=args.als_factors, seed=args.als_seed,
            ranking_users=sampled_users,
        )

        # Validation-only weight selection. Test labels are not passed here.
        tuning = tune_hybrid_weights(signals, validation, args.ks, overlap_ids, seed=args.tuning_seed)
        hybrid = fuse_hybrid(signals, tuning["weights"], max(args.ks) * 10)

        final_rankings = {
            "global_popularity": signals["global_popularity"],
            "personalized_popularity": signals["personalized_popularity"],
            "content": signals["content"],
            "collaborative": signals["collaborative"],
            "hybrid_tuned": hybrid,
            "hybrid_previous_weights": fuse_hybrid(
                signals, DEFAULT_WEIGHTS, max(args.ks) * 10
            ),
        }
        validation_rankings = {
            name: rankings for name, rankings in final_rankings.items()
        }
        validation_metrics = {
            name: evaluate_rankings(rankings, validation, overlap_ids, args.ks, bootstrap_seed=args.bootstrap_seed)
            for name, rankings in validation_rankings.items()
        }
        test_metrics = {
            name: evaluate_rankings(rankings, test, overlap_ids, args.ks, bootstrap_seed=args.bootstrap_seed)
            for name, rankings in final_rankings.items()
        }

        paired_comparisons = {}
        for k in args.ks:
            hybrid_user = per_user_ranking_metrics(hybrid, test, k)
            popularity_user = per_user_ranking_metrics(
                signals["global_popularity"], test, k
            )
            paired_comparisons[str(k)] = {
                metric: paired_bootstrap_difference_ci(
                    hybrid_user, popularity_user, metric,
                    seed=args.bootstrap_seed + 300 + k + offset,
                )
                for offset, metric in enumerate(("precision", "recall", "ndcg"))
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
                "method": "per-user chronological 3-way split after latest-rating deduplication",
                "train_ratio": args.train_ratio,
                "validation_ratio": args.validation_ratio,
                "test_ratio": args.test_ratio,
                **split_stats,
                "eligible_users_all_three_partitions": eligible_user_count,
                "evaluation_users_sampled": len(sampled_users),
                "evaluation_user_sample_size_requested": args.evaluation_users,
                "evaluation_user_sample_method": "seeded uniform sample without replacement",
                "evaluation_seed": args.evaluation_seed,
                "model_fit_train_users": len(train),
                "model_fit_train_interactions": sum(map(len, train.values())),
                "evaluation_validation_interactions": sum(map(len, validation.values())),
                "evaluation_test_interactions": sum(map(len, test.values())),
            },
            "reproducibility": {
                "evaluation_seed": args.evaluation_seed,
                "als_seed": args.als_seed,
                "tuning_seed": args.tuning_seed,
                "bootstrap_seed": args.bootstrap_seed,
                "als_factors": args.als_factors,
                "als_iterations": 20,
                "als_regularization": 0.05,
                "blas_thread_limit": 1,
            },
            "hybrid_tuning": tuning,
            "evaluation": {
                "metrics": ["precision", "recall", "ndcg", "coverage"],
                "ks": args.ks,
                "averaging": "macro average over the seeded sampled evaluation users",
                "coverage_denominator": "MovieLens/DeepCine overlapping catalog",
                "model_fit_data": "full eligible training partition",
                "weight_selection_data": "validation partition only",
                "final_reporting_data": "held-out test partition only",
                "evaluation_population": "seeded uniform sample of eligible users",
                "ranking_population": "sampled evaluation users",
                "training_population": "all eligible users",
                "evaluation_users_sampled": len(sampled_users),
                "objective": tuning["objective"],
                "confidence_intervals": "95% percentile bootstrap over sampled users; 1000 resamples",
            },
            "validation_metrics": validation_metrics,
            "test_metrics": test_metrics,
            "paired_test_difference_hybrid_minus_global_popularity_ci95": paired_comparisons,
            "limitations": [
                "Results apply only to the MovieLens/DeepCine overlapping catalog, not the full DeepCine catalog.",
                "Ratings >= threshold are implicit positives; this is not explicit rating prediction.",
                "MovieLens users and interactions are external benchmark data, not production DeepCine users or watch history.",
                "Per-user chronological splitting is not a global calendar-time split.",
                "Personalized popularity uses training-only genre affinity and item interaction counts.",
                "The final test partition must not be used to select weights or model settings.",
                "Bootstrap intervals quantify uncertainty across sampled users for this run; repeated seeds are still required to assess run-to-run stability.",
                "Metrics are estimated on a seeded uniform sample of eligible users, not the full eligible population.",
            ],
        }

        json_path = OUTPUT_DIR / f"movielens_phase4_{timestamp}.json"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        csv_path = OUTPUT_DIR / f"movielens_phase4_{timestamp}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "partition", "model", "k", "precision", "recall",
                "ndcg", "coverage", "users_evaluated",
            ])
            for partition, all_models in (
                ("validation", validation_metrics), ("test", test_metrics)
            ):
                for model, by_k in all_models.items():
                    for k, values in by_k.items():
                        writer.writerow([
                            partition, model, k, values["precision"],
                            values["recall"], values["ndcg"],
                            values["coverage"], values["users_evaluated"],
                        ])
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
    parser.add_argument("--train-ratio", type=float, default=0.6)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--ks", default="5,10,20")
    parser.add_argument("--als-factors", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42, help="legacy seed; fallback for all phase-4 seeds")
    parser.add_argument("--evaluation-seed", type=int, default=None)
    parser.add_argument("--als-seed", type=int, default=None)
    parser.add_argument("--tuning-seed", type=int, default=None)
    parser.add_argument("--bootstrap-seed", type=int, default=None)
    parser.add_argument(
        "--evaluation-users", type=int,
        default=DEFAULT_EVALUATION_USER_SAMPLE_SIZE,
        help="maximum eligible users to evaluate (seeded uniform sample; default: 2000)",
    )
    args = parser.parse_args()
    args.evaluation_seed = args.seed if args.evaluation_seed is None else args.evaluation_seed
    args.als_seed = args.seed if args.als_seed is None else args.als_seed
    args.tuning_seed = args.seed if args.tuning_seed is None else args.tuning_seed
    args.bootstrap_seed = args.seed if args.bootstrap_seed is None else args.bootstrap_seed
    ratios = (args.train_ratio, args.validation_ratio, args.test_ratio)
    if any(value <= 0 for value in ratios) or not math.isclose(sum(ratios), 1.0):
        parser.error("train/validation/test ratios must be positive and sum to 1")
    if args.chunksize <= 0 or args.als_factors <= 0 or args.evaluation_users <= 0:
        parser.error("chunksize, ALS factors, and evaluation-users must be positive")
    args.ks = tuple(sorted({int(value) for value in args.ks.split(",")}))
    if not args.ks or any(k <= 0 for k in args.ks):
        parser.error("--ks must contain positive integers")
    if not 0 <= args.positive_threshold <= 5:
        parser.error("--positive-threshold must be between 0 and 5")
    return args


if __name__ == "__main__":
    run(parse_args())
