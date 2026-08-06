from __future__ import annotations

from streamlit.testing.v1 import AppTest

from fiesc_pm.config import get_settings


def _dashboard() -> AppTest:
    path = get_settings().repo_root / "app" / "streamlit_app.py"
    return AppTest.from_file(str(path), default_timeout=60)


def test_dashboard_loads_without_exception() -> None:
    app = _dashboard().run()
    assert not app.exception
    assert len(app.tabs) == 7  # cinco áreas principais + formulário/JSON na entrada
    assert app.title[0].value == "Manutenção prescritiva"
    assert app.sidebar.button[0].label == "Analisar cenário"


def test_language_selector_label_is_interface_language() -> None:
    app = _dashboard().run()
    assert app.sidebar.selectbox[0].label == "Idioma da interface"
    assert app.sidebar.selectbox[0].options == ["Português (Brasil)", "English"]


def test_language_switch_clears_previous_response() -> None:
    app = _dashboard().run()
    assert "response" not in app.session_state
    app.sidebar.button[0].click()
    app.run()
    assert "response" in app.session_state
    assert app.success
    app.sidebar.selectbox[0].select("English")
    app.run()
    assert "response" not in app.session_state
    assert not app.success


def test_questions_are_independent_per_language() -> None:
    app = _dashboard().run()
    portuguese_question = "Verificar folga do rolamento?"
    app.sidebar.text_input[0].set_value(portuguese_question)
    app.run()
    assert app.sidebar.text_input[0].value == portuguese_question
    app.sidebar.selectbox[0].select("English")
    app.run()
    english_default = app.sidebar.text_input[0].value
    assert english_default != portuguese_question
    assert "Which checks and corrective actions" in english_default
    english_question = "Verifying bearing clearance?"
    app.sidebar.text_input[0].set_value(english_question)
    app.run()
    assert app.sidebar.text_input[0].value == english_question
    app.sidebar.selectbox[0].select("Português (Brasil)")
    app.run()
    assert app.sidebar.text_input[0].value != english_question
