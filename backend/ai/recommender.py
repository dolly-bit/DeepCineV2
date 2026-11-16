import hashlib
import json
from pathlib import Path

import numpy as np

from app.database.connection import SessionLocal
from app.models.movie import Movie
from app.models.watch_history import WatchHistory

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_NAME = "all-MiniLM-L6-v2"
MANIFEST_NAME = "movie_artifact_manifest.json"
ARTIFACT_NAMES = (
    "movie_embeddings.npy",
    "movie_ids.npy",
    "movie_index.faiss",
)
_model = None
_index = None
_movie_ids = None


class ArtifactValidationError(RuntimeError):
    """Raised when content recommendation artifacts are missing or invalid."""


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _get_index_and_ids():
    """Load only a complete, self-consistent artifact generation."""
    global _index, _movie_ids
    if _index is not None and _movie_ids is not None:
        return _index, _movie_ids

    import faiss

    manifest_path = BASE_DIR / MANIFEST_NAME
    artifact_paths = {name: BASE_DIR / name for name in ARTIFACT_NAMES}
    missing = [
        str(path.name)
        for path in [manifest_path, *artifact_paths.values()]
        if not path.is_file()
    ]
    if missing:
        raise ArtifactValidationError(
            "Content recommendation artifacts are incomplete; missing: "
            + ", ".join(missing)
            + ". Rebuild them with python generate_embeddings.py."
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != 1:
            raise ArtifactValidationError("Unsupported content artifact schema.")
        if manifest.get("embedding_model") != MODEL_NAME:
            raise ArtifactValidationError(
                "Content artifacts were built with a different embedding model."
            )

        expected_hashes = manifest.get("artifacts", {})
        for name, path in artifact_paths.items():
            expected = expected_hashes.get(name)
            if not isinstance(expected, str) or _sha256(path) != expected:
                raise ArtifactValidationError(
                    f"Content artifact integrity check failed for {name}."
                )

        movie_ids = np.load(
            str(artifact_paths["movie_ids.npy"]), allow_pickle=False
        )
        if movie_ids.ndim != 1 or not np.issubdtype(movie_ids.dtype, np.integer):
            raise ArtifactValidationError(
                "Movie ID artifact must be a one-dimensional integer array."
            )
        if len(movie_ids) == 0 or np.any(movie_ids <= 0):
            raise ArtifactValidationError(
                "Movie ID artifact is empty or contains invalid IDs."
            )
        if len(np.unique(movie_ids)) != len(movie_ids):
            raise ArtifactValidationError(
                "Movie ID artifact contains duplicate IDs."
            )

        expected_count = manifest.get("movie_count")
        expected_dimension = manifest.get("embedding_dimension")
        if not isinstance(expected_count, int) or expected_count != len(movie_ids):
            raise ArtifactValidationError(
                "Manifest movie count does not match the movie ID mapping."
            )
        if not isinstance(expected_dimension, int) or expected_dimension <= 0:
            raise ArtifactValidationError(
                "Manifest embedding dimension must be a positive integer."
            )

        embeddings = np.load(
            str(artifact_paths["movie_embeddings.npy"]),
            mmap_mode="r",
            allow_pickle=False,
        )
        if (
            embeddings.ndim != 2
            or embeddings.dtype != np.float32
            or embeddings.shape != (expected_count, expected_dimension)
        ):
            raise ArtifactValidationError(
                "Embedding matrix shape or dtype does not match the manifest."
            )

        index = faiss.read_index(str(artifact_paths["movie_index.faiss"]))
        if index.ntotal != len(movie_ids):
            raise ArtifactValidationError(
                "FAISS vector count does not match the movie ID mapping."
            )
        if not isinstance(expected_dimension, int) or index.d != expected_dimension:
            raise ArtifactValidationError(
                "FAISS dimension does not match the artifact manifest."
            )
        if not getattr(index, "is_trained", True):
            raise ArtifactValidationError("FAISS index is not trained.")

    except ArtifactValidationError:
        raise
    except Exception as exc:
        raise ArtifactValidationError(
            f"Could not load content recommendation artifacts: {exc}"
        ) from exc

    # Assign globals only after every integrity and compatibility check passes.
    _index = index
    _movie_ids = movie_ids.astype(np.int64, copy=False)
    return _index, _movie_ids


def invalidate_index_cache():
    global _index, _movie_ids
    _index = None
    _movie_ids = None


def _movie_text(movie):
    return (
        f"Title: {movie.title}\n"
        f"Overview: {movie.overview or ''}\n"
        f"Language: {movie.original_language or ''}"
    )


def recommend_movies(movie_name: str, top_k: int = 10):
    """Existing title-to-title content recommendation contract."""
    if top_k <= 0:
        return []
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(
            Movie.title.ilike(f"%{movie_name}%")
        ).first()
        if not movie:
            return []

        model = get_model()
        index, movie_ids = _get_index_and_ids()
        embedding = model.encode([_movie_text(movie)]).astype("float32")
        _, indices = index.search(embedding, top_k + 1)
        results = []

        for idx in indices[0]:
            if idx < 0 or idx >= len(movie_ids):
                continue
            movie_id = int(movie_ids[idx])
            if movie_id == movie.id:
                continue
            candidate = db.query(Movie).filter(Movie.id == movie_id).first()
            if candidate:
                results.append({
                    "id": candidate.id,
                    "title": candidate.title,
                    "poster_url": (
                        f"https://image.tmdb.org/t/p/w500{candidate.poster_path}"
                        if candidate.poster_path else None
                    ),
                    "overview": candidate.overview,
                    "rating": candidate.vote_average,
                    "release_date": candidate.release_date,
                })
        return results[:top_k]
    finally:
        db.close()


def recommend_for_user_content(user_id: int, db, top_k: int = 100):
    """Return TMDB IDs ranked by semantic proximity to a user's watch history."""
    if top_k <= 0:
        return []

    watched_ids = {
        row[0] for row in db.query(WatchHistory.tmdb_id)
        .filter(WatchHistory.user_id == user_id).distinct().all()
    }
    if not watched_ids:
        return []

    watched = db.query(Movie).filter(Movie.tmdb_id.in_(watched_ids)).all()
    if not watched:
        return []

    # No artifacts yet means content retrieval is unavailable. If any part of
    # the set exists, validate the whole generation instead of using a partial set.
    artifact_files = [BASE_DIR / name for name in (*ARTIFACT_NAMES, MANIFEST_NAME)]
    if not any(path.exists() for path in artifact_files):
        return []

    model = get_model()
    index, indexed_ids = _get_index_and_ids()
    if index.ntotal == 0:
        return []

    vectors = model.encode(
        [_movie_text(movie) for movie in watched]
    ).astype("float32")
    distances, positions = index.search(
        vectors, min(index.ntotal, max(top_k * 3, 50))
    )
    watched_db_ids = {movie.id for movie in watched}
    best_distance = {}

    for distance_row, position_row in zip(distances, positions):
        for distance, position in zip(distance_row, position_row):
            if position < 0 or position >= len(indexed_ids):
                continue
            db_id = int(indexed_ids[position])
            if db_id in watched_db_ids:
                continue
            distance = float(distance)
            if db_id not in best_distance or distance < best_distance[db_id]:
                best_distance[db_id] = distance

    ranked_db_ids = sorted(best_distance, key=best_distance.get)[:top_k]
    rows = db.query(Movie.id, Movie.tmdb_id).filter(
        Movie.id.in_(ranked_db_ids)
    ).all()
    tmdb_by_db_id = {db_id: tmdb_id for db_id, tmdb_id in rows}
    return [tmdb_by_db_id[mid] for mid in ranked_db_ids if mid in tmdb_by_db_id]
