"""
Trains a collaborative-filtering recommender using Alternating Least Squares
(ALS) matrix factorization over implicit feedback (watch history).

This is genuine collaborative filtering: the model only ever sees a
(user, movie, interaction_strength) matrix. It never looks at a movie's
title, overview, genre, or embedding - it purely learns latent taste
vectors for users and movies from *co-watching patterns* across all users.
That's what distinguishes it from ai/recommender.py (content-based, via
sentence-transformer embeddings + FAISS).

Run manually after enough WatchHistory rows exist:
    python train_collaborative_model.py

Re-run periodically (e.g. nightly, alongside the existing TMDB sync job in
app/schedular) as new watch events accumulate, so the model stays current.
"""

import pickle
from collections import Counter
from pathlib import Path

from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares

from app.database.connection import SessionLocal
from app.models import WatchHistory

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "cf_model.pkl"

# ALS hyperparameters. Kept small/fast since this is a portfolio-scale
# dataset; documented here so the choice is explicit rather than accidental.
N_FACTORS = 64
REGULARIZATION = 0.05
ITERATIONS = 20
MIN_INTERACTIONS_PER_USER = 1  # raise this once you have real usage data


def build_interaction_matrix(db):
    """
    Turns raw WatchHistory rows into a sparse (users x movies) matrix of
    implicit "confidence" scores. Re-watching / repeated logs of the same
    movie count as a stronger signal, same idea as the original
    Hu/Koren/Volinsky implicit-feedback ALS paper.
    """
    watch_events = db.query(WatchHistory).all()

    if not watch_events:
        raise ValueError(
            "No WatchHistory rows found - collaborative filtering needs "
            "interaction data to train on. Seed some watch history first."
        )

    user_ids = sorted({w.user_id for w in watch_events})
    tmdb_ids = sorted({w.tmdb_id for w in watch_events})

    user_to_idx = {u: i for i, u in enumerate(user_ids)}
    item_to_idx = {t: i for i, t in enumerate(tmdb_ids)}

    interaction_counts = Counter(
        (w.user_id, w.tmdb_id) for w in watch_events
    )

    rows, cols, confidence = [], [], []
    for (user_id, tmdb_id), count in interaction_counts.items():
        rows.append(user_to_idx[user_id])
        cols.append(item_to_idx[tmdb_id])
        # 1 + alpha * count is the standard implicit-feedback confidence
        # weighting: a single watch counts, repeats count more.
        confidence.append(1.0 + 2.0 * count)

    matrix = csr_matrix(
        (confidence, (rows, cols)),
        shape=(len(user_ids), len(tmdb_ids)),
    )

    return matrix, user_to_idx, item_to_idx


def train():
    db = SessionLocal()
    try:
        matrix, user_to_idx, item_to_idx = build_interaction_matrix(db)
    finally:
        db.close()

    model = AlternatingLeastSquares(
        factors=N_FACTORS,
        regularization=REGULARIZATION,
        iterations=ITERATIONS,
        random_state=42,
    )

    # implicit expects a (users x items) confidence-weighted sparse matrix.
    model.fit(matrix)

    artifacts = {
        "user_to_idx": user_to_idx,
        "item_to_idx": item_to_idx,
        "idx_to_item": {idx: tmdb_id for tmdb_id, idx in item_to_idx.items()},
        "user_factors": model.user_factors,
        "item_factors": model.item_factors,
        "interaction_matrix": matrix,
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(artifacts, f)

    print(
        f"Trained ALS collaborative-filtering model: "
        f"{matrix.shape[0]} users x {matrix.shape[1]} movies, "
        f"{matrix.nnz} interactions, {N_FACTORS} latent factors."
    )
    print(f"Saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
