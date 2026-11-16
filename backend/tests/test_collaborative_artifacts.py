import hashlib
import json
import pickle

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from ai import collaborative


@pytest.fixture
def model_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(collaborative, "MODEL_PATH", tmp_path / "cf_model.pkl")
    monkeypatch.setattr(collaborative, "MANIFEST_PATH", tmp_path / "cf_model_manifest.json")
    collaborative.invalidate_model_cache()
    yield tmp_path
    collaborative.invalidate_model_cache()


def write_artifact(directory, *, invalid_user_shape=False):
    user_factors = np.ones((2, 3), dtype=np.float32)
    if invalid_user_shape:
        user_factors = np.ones((1, 3), dtype=np.float32)
    artifacts = {
        "user_to_idx": {10: 0, 20: 1},
        "item_to_idx": {101: 0, 202: 1},
        "idx_to_item": {0: 101, 1: 202},
        "user_factors": user_factors,
        "item_factors": np.ones((2, 3), dtype=np.float32),
        "interaction_matrix": csr_matrix(
            np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        ),
    }
    model_path = directory / "cf_model.pkl"
    with model_path.open("wb") as model_file:
        pickle.dump(artifacts, model_file)
    manifest = {
        "schema_version": 1,
        "n_users": 2,
        "n_items": 2,
        "n_factors": 3,
        "interaction_count": 2,
        "artifact_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
    }
    (directory / "cf_model_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )


def test_loader_accepts_valid_als_artifact(model_paths):
    write_artifact(model_paths)

    artifacts = collaborative._load_artifacts()

    assert artifacts["user_factors"].shape == (2, 3)
    assert artifacts["item_factors"].shape == (2, 3)
    assert artifacts["interaction_matrix"].shape == (2, 2)


def test_loader_rejects_tampered_als_artifact(model_paths):
    write_artifact(model_paths)
    with (model_paths / "cf_model.pkl").open("ab") as model_file:
        model_file.write(b"tampered")

    with pytest.raises(
        collaborative.CollaborativeArtifactValidationError,
        match="integrity check failed",
    ):
        collaborative._load_artifacts()


def test_loader_rejects_incompatible_factor_shapes(model_paths):
    write_artifact(model_paths, invalid_user_shape=True)

    with pytest.raises(
        collaborative.CollaborativeArtifactValidationError,
        match="user factor matrix",
    ):
        collaborative._load_artifacts()


def test_loader_rejects_missing_manifest(model_paths):
    write_artifact(model_paths)
    (model_paths / "cf_model_manifest.json").unlink()

    with pytest.raises(
        collaborative.CollaborativeArtifactValidationError,
        match="manifest is missing",
    ):
        collaborative._load_artifacts()
