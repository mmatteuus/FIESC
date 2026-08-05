from __future__ import annotations

import json
import shutil

import pytest

from fiesc_pm.config import get_settings
from fiesc_pm.modeling import load_model_bundle


def test_model_hash_is_verified_before_deserialization(tmp_path) -> None:
    settings = get_settings()
    model_path = tmp_path / "model_bundle.joblib"
    metadata_path = tmp_path / "model_metadata.json"
    shutil.copy2(settings.model_path, model_path)
    metadata = json.loads(settings.metadata_path.read_text(encoding="utf-8"))
    metadata["model_sha256"] = "0" * 64
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="Hash SHA-256"):
        load_model_bundle(model_path)
