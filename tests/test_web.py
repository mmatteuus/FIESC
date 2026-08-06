from pathlib import Path


def test_web_demo_contains_required_elements() -> None:
    root = Path(__file__).resolve().parents[1]
    html = (root / "public/index.html").read_text(encoding="utf-8")
    assert "Manutenção Prescritiva" in html
    assert "/v1/recommendations" in html
    assert "/demo-events" in html
    assert "scenario" in html
    assert "aria-live" in html
    assert "mtsferreira.dev" in html
