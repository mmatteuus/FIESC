from __future__ import annotations

from streamlit.testing.v1 import AppTest

from fiesc_pm.config import get_settings


def test_dashboard_loads_without_exception() -> None:
    path = get_settings().repo_root / "app" / "streamlit_app.py"
    app = AppTest.from_file(str(path), default_timeout=20).run()
    assert not app.exception
    assert len(app.tabs) == 7  # cinco áreas principais + formulário/JSON na entrada
    assert app.title[0].value == "Manutenção prescritiva"
    assert app.sidebar.button[0].label == "Analisar cenário"
