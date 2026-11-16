"""Inference helpers for the ALS collaborative-filtering model."""
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np

from app.database.connection import SessionLocal
from app.models import Movie

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "cf_model.pkl"
MANIFEST_PATH = BASE_DIR / "cf_model_manifest.json"
SCHEMA_VERSION = 1
_artifacts = None


class CollaborativeArtifactValidationError(RuntimeError):
    """Raised when the ALS model artifact is missing, corrupt, or incompatible."""


def has_model() -> bool:
    return MODEL_PATH.is_file()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_artifacts(artifacts, manifest):
    required = {
        "user_to_idx",
        "item_to_idx",
        "idx_to_item",
        "user_factors",
        "item_factors",
        "interaction_matrix",
    }
    if not isinstance(artifacts, dict) or not required.issubset(artifacts):
        raise CollaborativeArtifactValidationError(
            "ALS artifact is missing required fields."
        )

    user_to_idx = artifacts["user_to_idx"]
    item_to_idx = artifacts["item_to_idx"]
    idx_to_item = artifacts["idx_to_item"]
    user_factors = np.asarray(artifacts["user_factors"])
    item_factors = np.asarray(artifacts["item_factors"])
    matrix = artifacts["interaction_matrix"]

    if not all(isinstance(mapping, dict) for mapping in (user_to_idx, item_to_idx, idx_to_item)):
        raise CollaborativeArtifactValidationError("ALS ID mappings must be dictionaries.")

    n_users = len(user_to_idx)
    n_items = len(item_to_idx)
    n_factors = manifest.get("n_factors")
    if n_users == 0 or n_items == 0 or not isinstance(n_factors, int) or n_factors <= 0:
        raise CollaborativeArtifactValidationError("ALS manifest contains invalid dimensions.")

    if set(user_to_idx.values()) != set(range(n_users)):
        raise CollaborativeArtifactValidationError("ALS user mapping indices are not contiguous.")
    if set(item_to_idx.values()) != set(range(n_items)):
        raise CollaborativeArtifactValidationError("ALS item mapping indices are not contiguous.")
    expected_reverse = {index: tmdb_id for tmdb_id, index in item_to_idx.items()}
    if idx_to_item != expected_reverse:
        raise CollaborativeArtifactValidationError("ALS item mappings are inconsistent.")

    if user_factors.shape != (n_users, n_factors):
        raise CollaborativeArtifactValidationError("ALS user factor matrix has an invalid shape.")
    if item_factors.shape != (n_items, n_factors):
        raise CollaborativeArtifactValidationError("ALS item factor matrix has an invalid shape.")
    if not np.isfinite(user_factors).all() or not np.isfinite(item_factors).all():
        raise CollaborativeArtifactValidationError("ALS factor matrices contain non-finite values.")

    if not hasattr(matrix, "shape") or not hasattr(matrix, "tocsr"):
        raise CollaborativeArtifactValidationError("ALS interaction matrix is not sparse.")
    if matrix.shape != (n_users, n_items):
        raise CollaborativeArtifactValidationError("ALS interaction matrix shape is inconsistent.")
    if matrix.nnz != manifest.get("interaction_count"):
        raise CollaborativeArtifactValidationError("ALS interaction count does not match the manifest.")
    if not np.isfinite(matrix.data).all():
        raise CollaborativeArtifactValidationError("ALS interaction matrix contains non-finite values.")

    if manifest.get("n_users") != n_users or manifest.get("n_items") != n_items:
        raise CollaborativeArtifactValidationError("ALS dimensions do not match the manifest.")


def _load_artifacts():
    global _artifacts
    if _artifacts is not None:
        return _artifacts

    if not MODEL_PATH.is_file():
        raise CollaborativeArtifactValidationError(
            "ALS model artifact is missing. Train it with python train_collaborative_model.py."
        )
    if not MANIFEST_PATH.is_file():
        raise CollaborativeArtifactValidationError(
            "ALS model manifest is missing. Retrain with python train_collaborative_model.py."
        )

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise CollaborativeArtifactValidationError("Unsupported ALS artifact schema.")
        if manifest.get("artifact_sha256") != _sha256(MODEL_PATH):
            raise CollaborativeArtifactValidationError("ALS artifact integrity check failed.")

        # Only load locally generated, trusted artifacts. Pickle is not safe for untrusted files.
        with MODEL_PATH.open("rb") as model_file:
            artifacts = pickle.load(model_file)
        _validate_artifacts(artifacts, manifest)
    except CollaborativeArtifactValidationError:
        raise
    except Exception as exc:
        raise CollaborativeArtifactValidationError(
            f"Could not load ALS model artifacts: {exc}"
        ) from exc

    _artifacts = artifacts
    return _artifacts


def invalidate_model_cache():
    """Clear cached factors after a model retrain or artifact replacement."""
    global _artifacts
    _artifacts = None


def recommendation_scores_for_user(user_id: int, top_k: int = 100):
    """Return ranked (TMDB ID, ALS score) pairs, excluding watched items."""
    if not has_model() or top_k <= 0:
        return []

    artifacts = _load_artifacts()
    user_to_idx = artifacts["user_to_idx"]
    if user_id not in user_to_idx:
        return []

    user_idx = user_to_idx[user_id]
    factors = artifacts["item_factors"] @ artifacts["user_factors"][user_idx]
    already_watched = set(artifacts["interaction_matrix"][user_idx].indices)
    ranked = np.argsort(factors)[::-1]
    results = []

    for item_idx in ranked:
        item_idx = int(item_idx)
        if item_idx in already_watched:
            continue
        tmdb_id = artifacts["idx_to_item"].get(item_idx)
        score = float(factors[item_idx])
        if tmdb_id is None or not np.isfinite(score):
            continue
        results.append((int(tmdb_id), score))
        if len(results) >= top_k:
            break
    return results


def recommend_for_user(user_id: int, top_k: int = 10):
    """Return Movie ORM objects in ALS ranking order (legacy API contract)."""
    ranked = recommendation_scores_for_user(user_id, top_k=top_k)
    if not ranked:
        return None if not has_model() else []

    tmdb_ids = [tmdb_id for tmdb_id, _ in ranked]
    db = SessionLocal()
    try:
        movies = db.query(Movie).filter(Movie.tmdb_id.in_(tmdb_ids)).all()
        by_tmdb_id = {movie.tmdb_id: movie for movie in movies}
        return [by_tmdb_id[mid] for mid in tmdb_ids if mid in by_tmdb_id]
    finally:
        db.close()
