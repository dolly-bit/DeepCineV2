"""
Trains a collaborative-filtering recommender using ALS matrix factorization
over implicit watch-history feedback.

Run manually after enough WatchHistory rows exist:
    python train_collaborative_model.py
"""

import hashlib
import json
import os
import pickle
import tempfile
from collections import Counter
from pathlib import Path

from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares

from app.database.connection import SessionLocal
from app.models import WatchHistory

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "cf_model.pkl"
MANIFEST_PATH = BASE_DIR / "cf_model_manifest.json"

N_FACTORS = 64
REGULARIZATION = 0.05
ITERATIONS = 20
MIN_INTERACTIONS_PER_USER = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_interaction_matrix(db):
    """Build a confidence-weighted sparse user/movie interaction matrix."""
    watch_events = db.query(WatchHistory).all()
    if not watch_events:
        raise ValueError(
            "No WatchHistory rows found - collaborative filtering needs "
            "interaction data to train on. Seed some watch history first."
        )

    user_ids = sorted({w.user_id for w in watch_events})
    tmdb_ids = sorted({w.tmdb_id for w in watch_events})
    user_to_idx = {user_id: idx for idx, user_id in enumerate(user_ids)}
    item_to_idx = {tmdb_id: idx for idx, tmdb_id in enumerate(tmdb_ids)}
    interaction_counts = Counter((w.user_id, w.tmdb_id) for w in watch_events)

    rows, cols, confidence = [], [], []
    for (user_id, tmdb_id), count in interaction_counts.items():
        rows.append(user_to_idx[user_id])
        cols.append(item_to_idx[tmdb_id])
        confidence.append(1.0 + 2.0 * count)

    matrix = csr_matrix(
        (confidence, (rows, cols)),
        shape=(len(user_ids), len(tmdb_ids)),
        dtype="float32",
    )
    return matrix, user_to_idx, item_to_idx


def _publish_artifacts(artifacts, matrix):
    """Write the model atomically and publish its manifest last."""
    staged_model = None
    staged_manifest = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=BASE_DIR, prefix=".cf_model.", suffix=".tmp", delete=False
        ) as temp_model:
            staged_model = Path(temp_model.name)
            pickle.dump(artifacts, temp_model, protocol=pickle.HIGHEST_PROTOCOL)
            temp_model.flush()
            os.fsync(temp_model.fileno())

        manifest = {
            "schema_version": 1,
            "n_users": matrix.shape[0],
            "n_items": matrix.shape[1],
            "n_factors": N_FACTORS,
            "interaction_count": int(matrix.nnz),
            "artifact_sha256": _sha256(staged_model),
        }
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=BASE_DIR,
            prefix=".cf_manifest.", suffix=".tmp", delete=False
        ) as temp_manifest:
            staged_manifest = Path(temp_manifest.name)
            json.dump(manifest, temp_manifest, indent=2)
            temp_manifest.flush()
            os.fsync(temp_manifest.fileno())

        os.replace(staged_model, MODEL_PATH)
        os.replace(staged_manifest, MANIFEST_PATH)
    finally:
        for staged in (staged_model, staged_manifest):
            if staged is not None and staged.exists():
                staged.unlink()


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
    model.fit(matrix)

    artifacts = {
        "user_to_idx": user_to_idx,
        "item_to_idx": item_to_idx,
        "idx_to_item": {idx: tmdb_id for tmdb_id, idx in item_to_idx.items()},
        "user_factors": model.user_factors,
        "item_factors": model.item_factors,
        "interaction_matrix": matrix,
    }
    _publish_artifacts(artifacts, matrix)

    print(
        f"Trained ALS collaborative-filtering model: "
        f"{matrix.shape[0]} users x {matrix.shape[1]} movies, "
        f"{matrix.nnz} interactions, {N_FACTORS} latent factors."
    )
    print(f"Saved to {MODEL_PATH}")
    print(f"Manifest saved to {MANIFEST_PATH}")


if __name__ == "__main__":
    train()
