from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .schemas import RecommendationResponse


class AuditStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    request_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    predicted_fault TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    novelty_score REAL NOT NULL,
                    provider TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    citations_json TEXT NOT NULL,
                    latency_ms REAL NOT NULL
                )
                """
            )

    def record(self, response: RecommendationResponse) -> None:
        citations = [citation.citation_id for citation in response.citations]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO analyses (
                    request_id, created_at, status, predicted_fault, confidence,
                    novelty_score, provider, model_version, citations_json, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response.request_id,
                    datetime.now(UTC).isoformat(),
                    response.status,
                    response.predicted_fault,
                    response.confidence,
                    response.novelty_score,
                    response.provider,
                    response.model_version,
                    json.dumps(citations),
                    response.latency_ms,
                ),
            )
            connection.execute(
                """
                DELETE FROM analyses
                WHERE request_id NOT IN (
                    SELECT request_id FROM analyses ORDER BY created_at DESC LIMIT 1000
                )
                """
            )
