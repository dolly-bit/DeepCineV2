"""Publish and download immutable content-recommender generations in GCS.

Each publication writes data under a unique generation prefix. A single small
current.json object is replaced last to activate that generation atomically.
Readers resolve the pointer once and download only objects from that generation.
Authentication uses Application Default Credentials (ADC).
"""
import hashlib
import json
import logging
import os
import re
import tempfile
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("deepcine.artifacts")

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "movie_artifact_manifest.json"
POINTER_NAME = "current.json"
ARTIFACT_NAMES = (
    "movie_embeddings.npy",
    "movie_ids.npy",
    "movie_index.faiss",
)
MODEL_NAME = "all-MiniLM-L6-v2"
_GENERATION_RE = re.compile(r"^[a-f0-9]{64}$")


class ArtifactStorageError(RuntimeError):
    """Raised when a published GCS artifact generation is unavailable or invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prefix(*parts: str) -> str:
    prefix = settings.GCS_PREFIX.strip("/")
    suffix = "/".join(part.strip("/") for part in parts if part)
    return f"{prefix}/{suffix}" if prefix and suffix else prefix or suffix


def _generation_id(manifest_bytes: bytes) -> str:
    return hashlib.sha256(manifest_bytes).hexdigest()


def _validate_staged_generation(staging_dir: Path) -> None:
    manifest_path = staging_dir / MANIFEST_NAME
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ArtifactStorageError(f"Could not read GCS artifact manifest: {exc}") from exc

    if manifest.get("schema_version") != 1:
        raise ArtifactStorageError("Unsupported content artifact schema in GCS.")
    if manifest.get("embedding_model") != MODEL_NAME:
        raise ArtifactStorageError("GCS artifacts use an unexpected embedding model.")

    hashes = manifest.get("artifacts")
    if not isinstance(hashes, dict):
        raise ArtifactStorageError("GCS artifact manifest has no artifact hash mapping.")

    for filename in ARTIFACT_NAMES:
        path = staging_dir / filename
        expected = hashes.get(filename)
        if not path.is_file() or not isinstance(expected, str):
            raise ArtifactStorageError(f"GCS generation is missing {filename}.")
        if _sha256(path) != expected:
            raise ArtifactStorageError(f"SHA-256 validation failed for {filename}.")

    try:
        import numpy as np
        import faiss

        ids = np.load(str(staging_dir / "movie_ids.npy"), allow_pickle=False)
        embeddings = np.load(
            str(staging_dir / "movie_embeddings.npy"),
            mmap_mode="r",
            allow_pickle=False,
        )
        expected_count = manifest.get("movie_count")
        expected_dimension = manifest.get("embedding_dimension")
        if (
            ids.ndim != 1
            or not np.issubdtype(ids.dtype, np.integer)
            or len(ids) == 0
            or np.any(ids <= 0)
            or len(np.unique(ids)) != len(ids)
        ):
            raise ArtifactStorageError("GCS movie ID mapping is invalid.")
        if not isinstance(expected_count, int) or len(ids) != expected_count:
            raise ArtifactStorageError("GCS movie count does not match its manifest.")
        if (
            not isinstance(expected_dimension, int)
            or expected_dimension <= 0
            or embeddings.shape != (expected_count, expected_dimension)
            or embeddings.dtype != np.float32
            or not np.isfinite(embeddings).all()
        ):
            raise ArtifactStorageError("GCS embedding matrix is invalid.")
        index = faiss.read_index(str(staging_dir / "movie_index.faiss"))
        if (
            index.ntotal != expected_count
            or index.d != expected_dimension
            or not getattr(index, "is_trained", True)
        ):
            raise ArtifactStorageError("GCS FAISS index is incompatible with its manifest.")
    except ArtifactStorageError:
        raise
    except Exception as exc:
        raise ArtifactStorageError(f"GCS artifact validation failed: {exc}") from exc


def _read_active_generation(bucket) -> str:
    try:
        pointer_bytes = bucket.blob(_prefix(POINTER_NAME)).download_as_bytes(timeout=30)
        pointer = json.loads(pointer_bytes)
        generation = pointer.get("generation")
        if not isinstance(generation, str) or not _GENERATION_RE.fullmatch(generation):
            raise ValueError("invalid generation identifier")
        return generation
    except Exception as exc:
        raise ArtifactStorageError(f"Could not read active GCS artifact pointer: {exc}") from exc


def download_artifacts_from_gcs() -> bool:
    """Resolve the active generation once, then stage and validate all its files."""
    if not settings.GCS_BUCKET.strip():
        logger.info("GCS_BUCKET is unset; remote recommender artifacts are disabled.")
        return False

    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(settings.GCS_BUCKET)
        generation = _read_active_generation(bucket)
        generation_prefix = _prefix("generations", generation)
        BASE_DIR.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="deepcine-artifacts-") as temp:
            staging_dir = Path(temp)
            filenames = (*ARTIFACT_NAMES, MANIFEST_NAME)
            for filename in filenames:
                object_name = _prefix("generations", generation, filename)
                blob = bucket.blob(object_name)
                try:
                    blob.download_to_filename(str(staging_dir / filename), timeout=120)
                except Exception as exc:
                    raise ArtifactStorageError(
                        f"Could not download gs://{settings.GCS_BUCKET}/{object_name}: {exc}"
                    ) from exc

            _validate_staged_generation(staging_dir)
            manifest_bytes = (staging_dir / MANIFEST_NAME).read_bytes()
            if _generation_id(manifest_bytes) != generation:
                raise ArtifactStorageError("Downloaded manifest does not match active generation.")

            # Cloud Run loads artifacts before serving requests. Manifest last
            # preserves a detectable local generation if replacement is interrupted.
            for filename in ARTIFACT_NAMES:
                os.replace(staging_dir / filename, BASE_DIR / filename)
            os.replace(staging_dir / MANIFEST_NAME, BASE_DIR / MANIFEST_NAME)

        logger.info("Downloaded validated recommender generation %s.", generation)
        return True
    except ArtifactStorageError:
        raise
    except Exception as exc:
        raise ArtifactStorageError(f"Could not initialize recommender artifacts from GCS: {exc}") from exc


def publish_artifacts_to_gcs() -> str:
    """Upload an immutable generation, then atomically activate it via current.json."""
    if not settings.GCS_BUCKET.strip():
        raise ArtifactStorageError("Set GCS_BUCKET before publishing artifacts.")

    from google.cloud import storage

    _validate_staged_generation(BASE_DIR)
    manifest_bytes = (BASE_DIR / MANIFEST_NAME).read_bytes()
    generation = _generation_id(manifest_bytes)
    client = storage.Client()
    bucket = client.bucket(settings.GCS_BUCKET)
    generation_prefix = _prefix("generations", generation)

    for filename in (*ARTIFACT_NAMES, MANIFEST_NAME):
        bucket.blob(f"{generation_prefix}/{filename}").upload_from_filename(
            str(BASE_DIR / filename), timeout=300
        )
        logger.info("Uploaded %s for generation %s.", filename, generation)

    # This single-object write is the publication/activation point. Existing
    # readers keep using their resolved immutable generation.
    pointer = json.dumps(
        {"schema_version": 1, "generation": generation},
        sort_keys=True,
        separators=(",", ":"),
    )
    bucket.blob(_prefix(POINTER_NAME)).upload_from_string(
        pointer, content_type="application/json", timeout=30
    )
    logger.info("Activated recommender generation %s.", generation)
    return generation
