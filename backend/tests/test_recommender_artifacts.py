import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from ai import index_builder, recommender


@pytest.fixture
def artifact_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(index_builder, "BASE_DIR", tmp_path)
    monkeypatch.setattr(recommender, "BASE_DIR", tmp_path)
    recommender.invalidate_index_cache()
    yield tmp_path
    recommender.invalidate_index_cache()


def build_small_index(artifact_dir, monkeypatch):
    movies = [
        SimpleNamespace(id=11, title="Film One", overview="First", original_language="en"),
        SimpleNamespace(id=22, title="Film Two", overview="Second", original_language="fr"),
    ]
    db = MagicMock()
    db.query.return_value.order_by.return_value.all.return_value = movies

    vectors = {
        11: np.array([1.0, 0.0], dtype=np.float32),
        22: np.array([0.0, 1.0], dtype=np.float32),
    }
    monkeypatch.setattr(
        index_builder,
        "get_movie_embedding",
        lambda movie: vectors[movie.id],
    )
    count = index_builder.build_recommendation_index(db, verbose=False)
    return count


def test_builder_publishes_manifest_and_loader_accepts_matching_artifacts(
    artifact_dir, monkeypatch
):
    count = build_small_index(artifact_dir, monkeypatch)

    assert count == 2
    manifest = json.loads(
        (artifact_dir / recommender.MANIFEST_NAME).read_text(encoding="utf-8")
    )
    assert manifest["schema_version"] == 1
    assert manifest["embedding_model"] == recommender.MODEL_NAME
    assert manifest["movie_count"] == 2
    assert manifest["embedding_dimension"] == 2

    index, movie_ids = recommender._get_index_and_ids()
    assert index.ntotal == 2
    assert index.d == 2
    assert movie_ids.tolist() == [11, 22]


def test_loader_rejects_tampered_artifact(artifact_dir, monkeypatch):
    build_small_index(artifact_dir, monkeypatch)

    ids_path = artifact_dir / "movie_ids.npy"
    with ids_path.open("ab") as artifact:
        artifact.write(b"tampered")

    recommender.invalidate_index_cache()
    with pytest.raises(
        recommender.ArtifactValidationError,
        match="integrity check failed",
    ):
        recommender._get_index_and_ids()


def test_loader_rejects_manifest_count_mismatch(artifact_dir, monkeypatch):
    build_small_index(artifact_dir, monkeypatch)

    manifest_path = artifact_dir / recommender.MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["movie_count"] = 99
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    recommender.invalidate_index_cache()
    with pytest.raises(
        recommender.ArtifactValidationError,
        match="movie count",
    ):
        recommender._get_index_and_ids()
