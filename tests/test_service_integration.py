from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from fiesc_pm.config import get_settings
from fiesc_pm.schemas import RecommendationRequest, SensorEvent
from fiesc_pm.service import RecommendationService


@pytest.fixture(scope="module")
def service(tmp_path_factory: pytest.TempPathFactory) -> RecommendationService:
    database_path = Path(tmp_path_factory.mktemp("audit")) / "test.sqlite3"
    return RecommendationService(replace(get_settings(), database_path=database_path))


@pytest.fixture(scope="module")
def demos() -> dict[str, dict[str, object]]:
    path = get_settings().repo_root / "data" / "demo" / "demo_events.json"
    return {item["name"]: item for item in json.loads(path.read_text(encoding="utf-8"))}


def analyze(
    service: RecommendationService,
    demos: dict[str, dict[str, object]],
    name: str,
):
    event = SensorEvent.model_validate(demos[name]["event"])
    return service.analyze(RecommendationRequest(event=event, provider="extractive", top_k=3))


def test_supported_family_has_validated_citations(service, demos) -> None:
    response = analyze(service, demos, "falha_documentada_rolamento")
    assert response.status == "supported"
    assert response.predicted_fault == "bearing"
    assert response.provider == "extractive"
    assert response.recommendation is not None
    assert response.citations
    assert response.similarity_summary.reference_count > 0
    assert response.similarity_summary.daily_counts
    assert all(case.source_id.startswith("ref-") for case in response.similar_cases)
    assert set(response.recommendation.citation_ids) <= {
        citation.citation_id for citation in response.citations
    }


@pytest.mark.parametrize(
    "name, fault",
    [
        ("sem_documento_rotor_excentrico", "eccentric_rotor"),
        ("sem_documento_perda_de_fase", "phase_loss"),
    ],
)
def test_unsupported_family_stops_before_provider(service, demos, name, fault) -> None:
    response = analyze(service, demos, name)
    assert response.status == "unsupported_documentation"
    assert response.predicted_fault == fault
    assert response.provider == "none"
    assert response.recommendation is None
    assert response.citations == []


def test_low_confidence_stops_before_provider(service, demos) -> None:
    response = analyze(service, demos, "baixa_confianca")
    assert response.status == "low_confidence"
    assert response.confidence < service.bundle.confidence_threshold
    assert response.provider == "none"
    assert response.recommendation is None
    assert response.citations == []


def test_normal_operation_stops_before_provider(service, demos) -> None:
    response = analyze(service, demos, "operacao_normal")
    assert response.status == "normal_operation"
    assert response.predicted_fault == "normal"
    assert response.provider == "none"
    assert response.recommendation is None


def test_motor_off_uses_rule_without_fabricated_confidence(service, demos) -> None:
    payload = dict(demos["operacao_normal"]["event"])
    payload["rpm"] = 0.0
    response = service.analyze(
        RecommendationRequest(event=SensorEvent.model_validate(payload), provider="extractive")
    )
    assert response.status == "normal_operation"
    assert response.operating_state == "motor_off"
    assert response.confidence == 0.0
    assert response.similar_cases == []
