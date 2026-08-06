from __future__ import annotations

import json
import secrets
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse

from .config import get_settings
from .schemas import RecommendationRequest, RecommendationResponse
from .service import RecommendationService

app = FastAPI(
    title="FIESC - Manutencao Prescritiva",
    version="1.1.0",
    description="API auditavel com classificacao, recuperacao documental, citacoes e abstencao segura.",
)


@lru_cache(maxsize=1)
def get_service() -> RecommendationService:
    return RecommendationService()


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().api_key
    if expected and (not x_api_key or not secrets.compare_digest(expected, x_api_key)):
        raise HTTPException(status_code=401, detail="API key ausente ou invalida")


@app.get("/", include_in_schema=False)
def web_demo() -> RedirectResponse:
    return RedirectResponse(url="/index.html", status_code=307)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, object]:
    settings = get_settings()
    try:
        service = get_service()
        return {
            "status": "ready",
            "model": service.bundle.version,
            "knowledge_chunks": len(service.knowledge.chunks),
            "gemini_configured": bool(settings.gemini_api_key),
            "ollama_automatic": settings.enable_ollama_fallback,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Servico nao pronto: {type(exc).__name__}"
        ) from exc


@app.get("/demo-events")
def demo_events() -> list[dict[str, object]]:
    settings = get_settings()
    path = settings.repo_root / "data" / "demo" / "demo_events.json"
    if not path.exists():
        raise HTTPException(status_code=503, detail="Cenarios demonstrativos ausentes")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "name": item["name"],
            "expected_fault": item["expected_fault"],
            "expected_status": item["expected_status"],
            "event": item["event"],
        }
        for item in payload
    ]


@app.get("/model-info")
def model_info() -> dict[str, object]:
    settings = get_settings()
    if not settings.metadata_path.exists():
        raise HTTPException(status_code=503, detail="Metadados do modelo ausentes")
    return json.loads(settings.metadata_path.read_text(encoding="utf-8"))


@app.post(
    "/v1/recommendations",
    response_model=RecommendationResponse,
    dependencies=[Depends(require_api_key)],
)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    try:
        return get_service().analyze(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
