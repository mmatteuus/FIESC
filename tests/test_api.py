from __future__ import annotations

import json
from dataclasses import replace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import fiesc_pm.api as api_module
from fiesc_pm.api import app, require_api_key
from fiesc_pm.config import get_settings
from fiesc_pm.service import RecommendationService


def test_health_and_model_info_endpoints() -> None:
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    model_info = client.get("/model-info")
    assert model_info.status_code == 200
    assert model_info.json()["version"].endswith("-v2")


def test_invalid_post_returns_422() -> None:
    response = TestClient(app).post("/v1/recommendations", json={})
    assert response.status_code == 422


def test_valid_post_uses_isolated_audit_database(monkeypatch, tmp_path) -> None:
    settings = replace(get_settings(), database_path=tmp_path / "api.sqlite3")
    service = RecommendationService(settings)
    monkeypatch.setattr(api_module, "get_service", lambda: service)
    demos = json.loads((settings.repo_root / "data/demo/demo_events.json").read_text("utf-8"))
    payload = {"event": demos[0]["event"], "provider": "extractive"}

    response = TestClient(app).post("/v1/recommendations", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "supported"
    assert response.json()["similarity_summary"]["reference_count"] > 0


def test_api_key_is_required_when_configured(monkeypatch) -> None:
    settings = replace(get_settings(), api_key="local-test-key")
    monkeypatch.setattr(api_module, "get_settings", lambda: settings)
    with pytest.raises(HTTPException) as error:
        require_api_key(None)
    assert error.value.status_code == 401
