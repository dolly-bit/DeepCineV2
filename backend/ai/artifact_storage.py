"""Download and publish versioned content-recommender artifacts in GCS.

The manifest is uploaded last and acts as the publication marker. Downloads are
staged locally and checksum-validated before replacing the active files.
Authentication uses Application Default Credentials (ADC).
"""
import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("deepcine.artifacts")

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "movie_artifact_manifest.json"
ARTIFACT_NAMES = (
    "movie_embeddings.npy",
    "movie_ids.npy",
    "movie_index.faiss",
)
MODEL_NAME = "all-MiniLM-L6-v2"


class ArtifactStorageError(RuntimeError):
    """Raised when a published GCS artifact generation is unavailable or invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _object_name(filename: str) -> str:
    prefix = settings.GCS_PREFIX.strip("/")
    return f"{prefix}/{filename}" if prefix else filename


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


def download_artifacts_from_gcs() -> bool:
    """Download one complete generation to the API instance's local disk."""
    if not settings.GCS_BUCKET.strip():
        logger.info("GCS_BUCKET is unset; remote recommender artifacts are disabled.")
        return False

    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(settings.GCS_BUCKET)
        BASE_DIR.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="deepcine-artifacts-") as temp:
            staging_dir = Path(temp)
            filenames = (*ARTIFACT_NAMES, MANIFEST_NAME)
            for filename in filenames:
                blob = bucket.blob(_object_name(filename))
                try:
                    blob.download_to_filename(str(staging_dir / filename), timeout=120)
                except Exception as exc:
                    raise ArtifactStorageError(
                        f"Could not download gs://{settings.GCS_BUCKET}/"
                        f"{_object_name(filename)}: {exc}"
                    ) from exc

            _validate_staged_generation(staging_dir)

            # Replace data files first and the manifest last. If the process is
            # interrupted, the old manifest cannot validate a mixed generation.
            for filename in ARTIFACT_NAMES:
                os.replace(staging_dir / filename, BASE_DIR / filename)
            os.replace(staging_dir / MANIFEST_NAME, BASE_DIR / MANIFEST_NAME)

        logger.info(
            "Downloaded and validated %s recommender artifacts from GCS bucket %s.",
            len(filenames),
            settings.GCS_BUCKET,
        )
        return True
    except ArtifactStorageError:
        raise
    except Exception as exc:
        raise ArtifactStorageError(f"Could not initialize recommender artifacts from GCS: {exc}") from exc


def publish_artifacts_to_gcs() -> None:
    """Upload validated local artifacts, publishing the manifest last.

    Run as a one-off operator command after building the index against the
    target database. Never invoke this from an API request.
    """
    if not settings.GCS_BUCKET.strip():
        raise ArtifactStorageError("Set GCS_BUCKET before publishing artifacts.")

    from google.cloud import storage

    _validate_staged_generation(BASE_DIR)
    client = storage.Client()
    bucket = client.bucket(settings.GCS_BUCKET)

    for filename in ARTIFACT_NAMES:
        bucket.blob(_object_name(filename)).upload_from_filename(
            str(BASE_DIR / filename), timeout=300
        )
        logger.info("Uploaded %s to GCS.", filename)

    bucket.blob(_object_name(MANIFEST_NAME)).upload_from_filename(
        str(BASE_DIR / MANIFEST_NAME), timeout=120
    )
    logger.info("Published recommender manifest last to GCS.")
