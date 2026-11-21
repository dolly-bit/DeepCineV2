import hashlib
import json
from pathlib import Path

import faiss
import numpy as np
import pytest
from google.cloud import storage

from ai import artifact_storage as artifacts
from ai.artifact_storage import (
    ARTIFACT_NAMES,
    MANIFEST_NAME,
    POINTER_NAME,
    ArtifactStorageError,
    _validate_staged_generation,
)


def _write_generation(directory):
    directory.mkdir(parents=True, exist_ok=True)
    embeddings = np.asarray(
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype=np.float32
    )
    ids = np.asarray([11, 12], dtype=np.int64)
    np.save(directory / "movie_embeddings.npy", embeddings, allow_pickle=False)
    np.save(directory / "movie_ids.npy", ids, allow_pickle=False)

    index = faiss.IndexFlatL2(3)
    index.add(embeddings)
    faiss.write_index(index, str(directory / "movie_index.faiss"))

    hashes = {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
        for name in ARTIFACT_NAMES
    }
    manifest = {
        "schema_version": 1,
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_dimension": 3,
        "movie_count": 2,
        "artifacts": hashes,
    }
    (directory / MANIFEST_NAME).write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )


class FakeBlob:
    def __init__(self, bucket, name):
        self.bucket = bucket
        self.name = name

    def download_as_bytes(self, **kwargs):
        return self.bucket.objects[self.name]

    def download_to_filename(self, filename, **kwargs):
        Path(filename).write_bytes(self.bucket.objects[self.name])

    def upload_from_filename(self, filename, **kwargs):
        self.bucket.objects[self.name] = Path(filename).read_bytes()
        self.bucket.events.append(self.name)

    def upload_from_string(self, data, **kwargs):
        # The active pointer must be the final write in a publication.
        assert len(self.bucket.events) == 4
        self.bucket.objects[self.name] = data.encode() if isinstance(data, str) else data
        self.bucket.events.append(self.name)


class FakeBucket:
    def __init__(self):
        self.objects = {}
        self.events = []

    def blob(self, name):
        return FakeBlob(self, name)


class FakeClient:
    bucket_instance = FakeBucket()

    def __init__(self):
        pass

    def bucket(self, name):
        assert name == "deepcine-test"
        return self.bucket_instance


def _configure_gcs(monkeypatch, directory):
    monkeypatch.setattr(artifacts, "BASE_DIR", directory)
    monkeypatch.setattr(artifacts.settings, "GCS_BUCKET", "deepcine-test")
    monkeypatch.setattr(artifacts.settings, "GCS_PREFIX", "recommender")
    FakeClient.bucket_instance = FakeBucket()
    monkeypatch.setattr(storage, "Client", FakeClient)
    return FakeClient.bucket_instance


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


def test_publish_uploads_immutable_generation_then_activates_pointer(
    tmp_path, monkeypatch
):
    _write_generation(tmp_path)
    bucket = _configure_gcs(monkeypatch, tmp_path)

    generation = artifacts.publish_artifacts_to_gcs()

    assert len(generation) == 64
    prefix = f"recommender/generations/{generation}"
    assert all(f"{prefix}/{name}" in bucket.objects for name in (*ARTIFACT_NAMES, MANIFEST_NAME))
    pointer_name = "recommender/" + POINTER_NAME
    assert json.loads(bucket.objects[pointer_name]) == {
        "schema_version": 1,
        "generation": generation,
    }
    assert bucket.events[-1] == pointer_name


def test_download_resolves_pointer_and_validates_generation(tmp_path, monkeypatch):
    source = tmp_path / "source"
    _write_generation(source)
    bucket = _configure_gcs(monkeypatch, tmp_path / "runtime")
    monkeypatch.setattr(artifacts, "BASE_DIR", tmp_path / "runtime")

    generation = hashlib.sha256((source / MANIFEST_NAME).read_bytes()).hexdigest()
    prefix = f"recommender/generations/{generation}"
    for filename in (*ARTIFACT_NAMES, MANIFEST_NAME):
        bucket.objects[f"{prefix}/{filename}"] = (source / filename).read_bytes()
    bucket.objects["recommender/" + POINTER_NAME] = json.dumps(
        {"schema_version": 1, "generation": generation}
    ).encode()

    assert artifacts.download_artifacts_from_gcs() is True
    _validate_staged_generation(tmp_path / "runtime")


def test_download_rejects_invalid_active_generation_pointer(tmp_path, monkeypatch):
    bucket = _configure_gcs(monkeypatch, tmp_path / "runtime")
    bucket.objects["recommender/" + POINTER_NAME] = b'{"generation":"../../other"}'

    with pytest.raises(ArtifactStorageError, match="active GCS artifact pointer"):
        artifacts.download_artifacts_from_gcs()
