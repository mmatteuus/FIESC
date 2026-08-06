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
    assert "aria-live" in html
    assert "mtsferreira.dev" in html


def test_root_redirects_to_web_demo() -> None:
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/index.html"
