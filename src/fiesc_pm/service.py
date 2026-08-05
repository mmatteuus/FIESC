from __future__ import annotations

import time
import uuid
from collections import Counter
from datetime import datetime
from typing import cast

import numpy as np

from .config import Settings, get_settings
from .features import build_features
from .labels import operating_state
from .llm import ProviderRouter
from .modeling import ModelBundle, load_model_bundle
from .persistence import AuditStore
from .retrieval import KnowledgeBase
from .schemas import (
    RecommendationContent,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationStatus,
    SimilarCase,
    SimilaritySummary,
)


def _similarity_summary(metadata: list[dict[str, object]]) -> SimilaritySummary:
    if not metadata:
        return SimilaritySummary(reference_count=0)

    dates = [datetime.fromisoformat(str(row["created_at"])) for row in metadata]
    rpms = [float(cast(float | int | str, row["rpm"])) for row in metadata]
    first_seen, last_seen = min(dates), max(dates)
    span_days = max((last_seen - first_seen).total_seconds() / 86_400, 1.0)
    return SimilaritySummary(
        reference_count=len(metadata),
        first_seen=first_seen,
        last_seen=last_seen,
        events_per_day=round(len(metadata) / span_days, 2),
        condition_counts=dict(Counter(str(row["fault_family"]) for row in metadata)),
        daily_counts=dict(Counter(value.date().isoformat() for value in dates)),
        rpm_counts=dict(Counter(f"{value:g}" for value in rpms)),
    )


class RecommendationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.bundle: ModelBundle = load_model_bundle(self.settings.model_path)
        self.knowledge = KnowledgeBase(self.settings.knowledge_path)
        self.providers = ProviderRouter(self.settings)
        self.audit = AuditStore(self.settings.database_path)

    def analyze(self, request: RecommendationRequest) -> RecommendationResponse:
        started = time.perf_counter()
        request_id = str(uuid.uuid4())
        event_data = request.event.sensor_dict()
        feature_frame = build_features(event_data).loc[:, self.bundle.feature_names]
        probabilities = self.bundle.estimator.predict_proba(feature_frame)[0]
        classes = [str(value) for value in self.bundle.estimator.classes_]
        predicted_index = int(np.argmax(probabilities))
        predicted_fault = classes[predicted_index]
        confidence = float(probabilities[predicted_index])
        state = operating_state(None, request.event.rpm)

        scaled = self.bundle.neighbor_scaler.transform(feature_frame)
        neighbor_count = min(request.top_k, len(self.bundle.neighbor_metadata))
        distances, indexes = self.bundle.neighbor_index.kneighbors(
            scaled, n_neighbors=neighbor_count
        )
        nearest_distance = float(distances[0, 0])
        novelty_score = nearest_distance / self.bundle.novelty_distance_threshold
        similar_cases = [
            SimilarCase(
                source_id=self.bundle.neighbor_metadata[int(index)]["source_id"],
                fault_family=self.bundle.neighbor_metadata[int(index)]["fault_family"],
                distance=float(distance),
                rpm=float(self.bundle.neighbor_metadata[int(index)]["rpm"]),
                created_at=self.bundle.neighbor_metadata[int(index)]["created_at"],
            )
            for distance, index in zip(distances[0], indexes[0], strict=True)
        ]
        _, radius_indexes = self.bundle.neighbor_index.radius_neighbors(
            scaled,
            radius=self.bundle.novelty_distance_threshold,
            sort_results=True,
        )
        reference_metadata = [
            self.bundle.neighbor_metadata[int(index)] for index in radius_indexes[0]
        ]
        similarity_summary = _similarity_summary(reference_metadata)

        warnings: list[str] = []
        citations = []
        recommendation: RecommendationContent | None = None
        provider = "none"
        documentation_available = self.knowledge.has_document(predicted_fault)

        status: RecommendationStatus
        if state == "motor_off":
            predicted_fault = "normal"
            confidence = 0.0
            novelty_score = 0.0
            similar_cases = []
            similarity_summary = SimilaritySummary(reference_count=0)
            status = "normal_operation"
            documentation_available = False
            warnings.append(
                "Motor parado: estado definido por regra operacional; o score do modelo não se aplica."
            )
        elif predicted_fault == "normal":
            status = "normal_operation"
        elif confidence < self.bundle.confidence_threshold or novelty_score > 1.0:
            status = "low_confidence"
            warnings.append("Inspecao humana necessaria antes de classificar a falha.")
        elif not documentation_available:
            status = "unsupported_documentation"
            warnings.append(
                "Nao existe documento cadastrado para esta familia; registrar nova documentacao."
            )
        else:
            citations = self.knowledge.retrieve(
                predicted_fault,
                f"{predicted_fault}. {request.question}",
                top_k=request.top_k,
            )
            if not citations:
                status = "llm_unavailable"
                warnings.append("Documento registrado, mas nenhuma evidencia foi recuperada.")
            else:
                recommendation, provider, provider_warnings = self.providers.generate(
                    request.provider,
                    predicted_fault,
                    request.question,
                    citations,
                )
                warnings.extend(provider_warnings)
                status = "supported"

        response = RecommendationResponse(
            request_id=request_id,
            status=status,
            operating_state=state,
            predicted_fault=predicted_fault,
            confidence=round(confidence, 6),
            novelty_score=round(float(novelty_score), 6),
            occurrence_count=int(self.bundle.occurrence_counts.get(predicted_fault, 0)),
            similar_cases=similar_cases,
            similarity_summary=similarity_summary,
            documentation_available=documentation_available,
            citations=citations,
            recommendation=recommendation,
            provider=provider,
            model_version=self.bundle.version,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            warnings=warnings,
        )
        self.audit.record(response)
        return response
