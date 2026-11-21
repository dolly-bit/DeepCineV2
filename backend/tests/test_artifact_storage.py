import hashlib
import json

import faiss
import numpy as np
import pytest

from ai.artifact_storage import (
    ARTIFACT_NAMES,
    MANIFEST_NAME,
    ArtifactStorageError,
    _validate_staged_generation,
)


def _write_generation(directory):
    embeddings = np.asarray(
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=np.float32
    )
    ids = np.asarray([11, 12], dtype=np.int64)
    np.save(directory / "movie_embeddings.npy", embeddings, allow_pickle=False)
    np.save(directory / "movie_ids.npy", ids, allow_pickle=False)

    index = faiss.IndexFlatL2(3)
    index.add(embeddings)
    faiss.write_index(index, str(directory / "movie_index.faiss"))

    hashes = {}
    for name in ARTIFACT_NAMES:
        hashes[name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()

    manifest = {
        "schema_version": 1,
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_dimension": 3,
        "movie_count": 2,
        "artifacts": hashes,
    }
    (directory / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def test_validate_staged_generation_accepts_complete_generation(tmp_path):
    _write_generation(tmp_path)

    _validate_staged_generation(tmp_path)


def test_validate_staged_generation_rejects_corrupt_artifact(tmp_path):
    _write_generation(tmp_path)
    with (tmp_path / "movie_ids.npy").open("ab") as artifact:
        artifact.write(b"corruption")

    with pytest.raises(ArtifactStorageError, match="SHA-256"):
        _validate_staged_generation(tmp_path)


def test_validate_staged_generation_rejects_missing_manifest(tmp_path):
    _write_generation(tmp_path)
    (tmp_path / MANIFEST_NAME).unlink()

    with pytest.raises(ArtifactStorageError, match="manifest"):
        _validate_staged_generation(tmp_path)
