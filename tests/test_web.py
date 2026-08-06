from pathlib import Path

from fastapi.testclient import TestClient

from fiesc_pm.api import app


def test_web_demo_contains_required_elements() -> None:
    root = Path(__file__).resolve().parents[1]
    html = (root / "public/index.html").read_text(encoding="utf-8")
    assert "Manutenção Prescritiva" in html
    assert "/v1/recommendations" in html
    assert "/demo-events" in html
    assert "scenario" in html
    assert "provider:'auto'" in html
    assert "gemini_configured" in html
    assert 'id="provider"' in html
    assert "aria-live" in html
    assert "mtsferreira.dev" in html
    assert "innerHTML" not in html


def test_web_demo_does_not_expose_full_document_excerpts() -> None:
    root = Path(__file__).resolve().parents[1]
    html = (root / "public/index.html").read_text(encoding="utf-8")
    assert "SNIPPET_LIMIT=220" in html
    assert "textContent=publicSnippet(citation.excerpt)" in html
    assert "excerpt.textContent=citation.excerpt;" not in html


def test_root_redirects_to_web_demo() -> None:
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/index.html"
