"""Build versioned, integrity-checked content recommendation artifacts."""

import hashlib
import json
import os
import tempfile
from pathlib import Path

from app.models.movie import Movie
from ai.embeddings import get_movie_embedding

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_NAME = "all-MiniLM-L6-v2"
MANIFEST_NAME = "movie_artifact_manifest.json"
ARTIFACT_NAMES = (
    "movie_embeddings.npy",
    "movie_ids.npy",
    "movie_index.faiss",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _temporary_path(directory: Path, suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        prefix=".deepcine-", suffix=suffix, dir=directory, delete=False
    )
    handle.close()
    return Path(handle.name)


def build_recommendation_index(db, verbose: bool = True):
    """Build artifacts and publish the manifest last.

    The manifest is the commit marker: readers reject a partially replaced
    artifact set because its hashes will not match the previous manifest.
    """
    import faiss
    import numpy as np

    movies = db.query(Movie).order_by(Movie.id.asc()).all()
    if not movies:
        if verbose:
            print(
                "No movies found in the database - nothing to index. "
                "Run `python import_movies.py` first."
            )
        return 0

    if verbose:
        print(
            f"Embedding {len(movies)} movies with {MODEL_NAME} "
            "(the model loads on first use)..."
        )

    vectors = []
    movie_ids = []
    for position, movie in enumerate(movies, start=1):
        vector = np.asarray(get_movie_embedding(movie), dtype=np.float32)
        if vector.ndim != 1 or not np.isfinite(vector).all():
            raise ValueError(
                f"Invalid embedding for movie database ID {movie.id}."
            )
        vectors.append(vector)
        movie_ids.append(movie.id)
        if verbose and (position % 100 == 0 or position == len(movies)):
            print(f"  {position}/{len(movies)}")

    embeddings = np.vstack(vectors).astype(np.float32, copy=False)
    ids = np.asarray(movie_ids, dtype=np.int64)

    if len(set(movie_ids)) != len(movie_ids):
        raise ValueError("Duplicate movie database IDs found; refusing to index.")
    if embeddings.ndim != 2 or embeddings.shape[0] != len(ids):
        raise ValueError("Embedding rows do not match the movie ID mapping.")

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    staged = {}
    try:
        embeddings_path = _temporary_path(BASE_DIR, ".npy")
        ids_path = _temporary_path(BASE_DIR, ".npy")
        index_path = _temporary_path(BASE_DIR, ".faiss")
        manifest_path = _temporary_path(BASE_DIR, ".json")
        staged = {
            "movie_embeddings.npy": embeddings_path,
            "movie_ids.npy": ids_path,
            "movie_index.faiss": index_path,
        }

        # Use file handles so numpy does not append another .npy suffix.
        with embeddings_path.open("wb") as output:
            np.save(output, embeddings, allow_pickle=False)
        with ids_path.open("wb") as output:
            np.save(output, ids, allow_pickle=False)

        index = faiss.IndexFlatL2(int(embeddings.shape[1]))
        index.add(embeddings)
        faiss.write_index(index, str(index_path))

        manifest = {
            "schema_version": 1,
            "embedding_model": MODEL_NAME,
            "embedding_dimension": int(embeddings.shape[1]),
            "movie_count": int(len(ids)),
            "artifacts": {
                name: _sha256(temp_path)
                for name, temp_path in staged.items()
            },
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # Publish data first and the manifest last. A crash mid-publish fails
        # closed because the old manifest hashes will no longer match.
        for name, temp_path in staged.items():
            os.replace(temp_path, BASE_DIR / name)
        os.replace(manifest_path, BASE_DIR / MANIFEST_NAME)

    finally:
        for temp_path in list(staged.values()):
            temp_path.unlink(missing_ok=True)
        if "manifest_path" in locals():
            manifest_path.unlink(missing_ok=True)

    if verbose:
        print(
            f"Published {len(ids)} movies, {embeddings.shape[1]} dimensions, "
            f"manifest: {MANIFEST_NAME}"
        )
    return len(ids)
