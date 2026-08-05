from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SENSOR_FIELDS = (
    "z_rms_velocity_in_s",
    "z_rms_velocity_mm_s",
    "temperature_f",
    "temperature_c",
    "x_rms_velocity_in_s",
    "x_rms_velocity_mm_s",
    "z_peak_acceleration_g",
    "x_peak_acceleration_g",
    "z_peak_vel_comp_freq_hz",
    "x_peak_vel_comp_freq_hz",
    "z_rms_acceleration_g",
    "x_rms_acceleration_g",
    "z_kurtosis",
    "x_kurtosis",
    "z_crest_factor",
    "x_crest_factor",
    "z_peak_velocity_in_s",
    "z_peak_velocity_mm_s",
    "x_peak_velocity_in_s",
    "x_peak_velocity_mm_s",
    "z_high_freq_rms_accel_g",
    "x_high_freq_rms_accel_g",
    "rpm",
)

NONNEGATIVE_SENSOR_FIELDS = tuple(
    name for name in SENSOR_FIELDS if name not in {"temperature_f", "temperature_c"}
)

ProviderName = Literal["auto", "gemini", "ollama", "extractive"]
RecommendationStatus = Literal[
    "supported",
    "unsupported_documentation",
    "low_confidence",
    "normal_operation",
    "llm_unavailable",
]


class SensorEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | str | None = None
    created_at: datetime | None = None
    z_rms_velocity_in_s: float
    z_rms_velocity_mm_s: float
    temperature_f: float
    temperature_c: float
    x_rms_velocity_in_s: float
    x_rms_velocity_mm_s: float
    z_peak_acceleration_g: float
    x_peak_acceleration_g: float
    z_peak_vel_comp_freq_hz: float
    x_peak_vel_comp_freq_hz: float
    z_rms_acceleration_g: float
    x_rms_acceleration_g: float
    z_kurtosis: float
    x_kurtosis: float
    z_crest_factor: float
    x_crest_factor: float
    z_peak_velocity_in_s: float
    z_peak_velocity_mm_s: float
    x_peak_velocity_in_s: float
    x_peak_velocity_mm_s: float
    z_high_freq_rms_accel_g: float
    x_high_freq_rms_accel_g: float
    rpm: float = Field(ge=0, le=100_000)

    @model_validator(mode="after")
    def numeric_values_must_be_finite(self) -> SensorEvent:
        for name in SENSOR_FIELDS:
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} deve ser finito")
        for name in NONNEGATIVE_SENSOR_FIELDS:
            if float(getattr(self, name)) < 0:
                raise ValueError(f"{name} não pode ser negativo")

        expected_fahrenheit = self.temperature_c * 9 / 5 + 32
        if not math.isclose(self.temperature_f, expected_fahrenheit, abs_tol=0.2):
            raise ValueError("temperature_f e temperature_c são inconsistentes")
        for imperial_name, metric_name in (
            ("z_rms_velocity_in_s", "z_rms_velocity_mm_s"),
            ("x_rms_velocity_in_s", "x_rms_velocity_mm_s"),
            ("z_peak_velocity_in_s", "z_peak_velocity_mm_s"),
            ("x_peak_velocity_in_s", "x_peak_velocity_mm_s"),
        ):
            imperial = float(getattr(self, imperial_name))
            metric = float(getattr(self, metric_name))
            if not math.isclose(metric, imperial * 25.4, rel_tol=0.015, abs_tol=0.03):
                raise ValueError(f"{imperial_name} e {metric_name} são inconsistentes")
        return self

    def sensor_dict(self) -> dict[str, float]:
        return {name: float(getattr(self, name)) for name in SENSOR_FIELDS}


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: SensorEvent
    question: str = Field(
        default="Quais verificacoes e acoes corretivas devo executar?", max_length=500
    )
    provider: ProviderName = "auto"
    top_k: int = Field(default=3, ge=1, le=5)


class Citation(BaseModel):
    citation_id: str
    document: str
    page: int
    section: str
    excerpt: str
    score: float = 0.0


class SimilarCase(BaseModel):
    source_id: str
    fault_family: str
    distance: float
    rpm: float
    created_at: datetime | None = None


class SimilaritySummary(BaseModel):
    reference_count: int
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    events_per_day: float = 0.0
    condition_counts: dict[str, int] = Field(default_factory=dict)
    daily_counts: dict[str, int] = Field(default_factory=dict)
    rpm_counts: dict[str, int] = Field(default_factory=dict)


class RecommendationContent(BaseModel):
    summary: str
    actions: list[str]
    safety_checks: list[str]
    human_validation_required: bool = True
    citation_ids: list[str]


class RecommendationResponse(BaseModel):
    request_id: str
    status: RecommendationStatus
    operating_state: str
    predicted_fault: str
    confidence: float
    novelty_score: float
    occurrence_count: int
    similar_cases: list[SimilarCase]
    similarity_summary: SimilaritySummary
    documentation_available: bool
    citations: list[Citation]
    recommendation: RecommendationContent | None
    provider: str
    model_version: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)
