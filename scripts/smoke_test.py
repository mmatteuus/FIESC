from __future__ import annotations

import json

from fiesc_pm.config import get_settings
from fiesc_pm.schemas import RecommendationRequest, SensorEvent
from fiesc_pm.service import RecommendationService


def main() -> None:
    settings = get_settings()
    demos = json.loads(
        (settings.repo_root / "data" / "demo" / "demo_events.json").read_text(encoding="utf-8")
    )
    service = RecommendationService(settings)
    results: list[dict[str, object]] = []
    for demo in demos:
        request = RecommendationRequest(
            event=SensorEvent.model_validate(demo["event"]),
            provider="extractive",
        )
        response = service.analyze(request)
        passed = response.status == demo["expected_status"]
        results.append(
            {
                "name": demo["name"],
                "expected": demo["expected_status"],
                "actual": response.status,
                "fault": response.predicted_fault,
                "provider": response.provider,
                "citations": len(response.citations),
                "latency_ms": response.latency_ms,
                "passed": passed,
            }
        )
        if not passed:
            raise AssertionError(results[-1])
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
