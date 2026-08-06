from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from app.ui_localization import (
    DEFAULT_LANGUAGE,
    FAULT_KEYS,
    FAULT_LABELS,
    FIELD_GROUPS,
    FIELD_KEYS,
    FIELD_LABELS,
    LANGUAGE_OPTIONS,
    MODE_KEYS,
    PROVIDER_KEYS,
    SCENARIO_KEYS,
    STATE_KEYS,
    STATE_LABELS,
    STATUS_KEYS,
    TRANSLATIONS,
    Language,
    build_event_payload,
    localized_date_format,
    localized_datetime_format,
    localized_fault_label,
    localized_field_label,
    localized_integer_format,
    localized_provider_label,
    localized_scenario_label,
    localized_state_label,
    localized_warning,
    preserve_technical_keys,
    recommended_question,
    translate,
)
from fiesc_pm.schemas import SENSOR_FIELDS, SensorEvent

LANGUAGES: tuple[Language, ...] = ("pt-BR", "en")


def _translations() -> tuple[dict[str, str], dict[str, str]]:
    return TRANSLATIONS["pt-BR"], TRANSLATIONS["en"]


def test_available_languages_and_default() -> None:
    assert set(TRANSLATIONS) == {"pt-BR", "en"}
    assert set(LANGUAGE_OPTIONS) == {"Português (Brasil)", "English"}
    assert DEFAULT_LANGUAGE == "pt-BR"


def test_same_translation_key_coverage_in_both_languages() -> None:
    portuguese, english = _translations()
    assert set(portuguese) == set(english)


def test_no_empty_or_blank_translation_values() -> None:
    for language in LANGUAGES:
        for key, value in TRANSLATIONS[language].items():
            assert value.strip(), (language, key)


def test_all_faults_translated_with_natural_names() -> None:
    for language in LANGUAGES:
        labels = FAULT_LABELS[language]
        assert set(FAULT_KEYS) == set(labels)
        for key, value in labels.items():
            assert value.strip() and value != key
    assert localized_fault_label("misalignment", "pt-BR") == "Desalinhamento"
    assert localized_fault_label("bearing", "pt-BR") == "Rolamento"
    assert localized_fault_label("eccentric_rotor", "en") == "Eccentric rotor"
    assert localized_fault_label("phase_loss", "en") == "Phase loss"


def test_all_states_translated() -> None:
    for language in LANGUAGES:
        labels = STATE_LABELS[language]
        assert set(STATE_KEYS) == set(labels)
        assert all(value.strip() for value in labels.values())
    assert localized_state_label("motor_off", "pt-BR") == "Motor desligado"
    assert localized_state_label("acceleration", "en") == "Acceleration"


def test_all_statuses_translated() -> None:
    for language in LANGUAGES:
        for key in STATUS_KEYS:
            assert TRANSLATIONS[language][key].strip()


def test_all_modes_and_providers_translated() -> None:
    for language in LANGUAGES:
        for mode in MODE_KEYS:
            assert TRANSLATIONS[language][f"mode_{mode}"].strip()
        for _provider, key in PROVIDER_KEYS.items():
            assert TRANSLATIONS[language][key].strip()
    assert localized_provider_label("gemini", "pt-BR") == "Gemini"
    assert localized_provider_label("extractive", "en") == "Document synthesis"
    assert localized_provider_label("unknown", "pt-BR") == "Não consultado"


def test_all_scenarios_translated() -> None:
    for language in LANGUAGES:
        for key in SCENARIO_KEYS.values():
            assert TRANSLATIONS[language][key].strip()
    assert localized_scenario_label("operacao_normal", "pt-BR") == "Operação normal"
    assert localized_scenario_label("sem_documento_rotor_excentrico", "pt-BR") == "Rotor excêntrico — sem documento"
    assert localized_scenario_label("sem_documento_rotor_excentrico", "en") == "Eccentric rotor — no documentation"
    assert localized_scenario_label("sem_documento_perda_de_fase", "pt-BR") == "Perda de fase — sem documento"
    assert localized_scenario_label("sem_documento_perda_de_fase", "en") == "Phase loss — no documentation"


def test_all_sensor_fields_translated() -> None:
    assert set(FIELD_KEYS) == {"id", "created_at"} | set(SENSOR_FIELDS)
    for language in LANGUAGES:
        labels = FIELD_LABELS[language]
        assert not set(FIELD_KEYS) - set(labels)
        for key, value in labels.items():
            assert value.strip() and value != key


def test_field_labels_include_units() -> None:
    assert localized_field_label("x_rms_velocity_mm_s", "pt-BR") == "Velocidade RMS no eixo X (mm/s)"
    assert localized_field_label("z_rms_velocity_in_s", "pt-BR") == "Velocidade RMS no eixo Z (pol/s)"
    assert localized_field_label("temperature_c", "pt-BR") == "Temperatura (°C)"
    assert localized_field_label("x_rms_velocity_mm_s", "en") == "X-axis RMS velocity (mm/s)"
    assert localized_field_label("temperature_f", "en") == "Temperature (°F)"


def test_field_groups_cover_exactly_all_field_keys() -> None:
    grouped = [field for _, fields in FIELD_GROUPS for field in fields]
    assert set(grouped) == set(FIELD_KEYS)
    assert len(grouped) == len(FIELD_KEYS)
    assert len(set(grouped)) == len(grouped)


def test_internal_field_names_are_preserved() -> None:
    original = {"x_rms_velocity_mm_s": 1.0, "temperature_c": 20.0}
    edited = {"x_rms_velocity_mm_s": 2.0, "temperature_c": 21.0, "localized_label": "ignore"}
    result = preserve_technical_keys(original, edited)
    assert result == {"x_rms_velocity_mm_s": 2.0, "temperature_c": 21.0}
    assert set(result) == set(original)


def test_build_event_payload_preserves_technical_keys_and_values() -> None:
    original = {"rpm": 2000.0, "temperature_c": 20.0}
    edited = {"rpm": 1500.0, "temperature_f": 68.0}
    payload = build_event_payload(original, edited)
    assert payload == {"rpm": 1500.0, "temperature_c": 20.0}
    assert set(payload) == set(original)


def as_dict(value: object) -> dict[str, object]:
    return cast(dict[str, object], value)


def test_payload_from_form_round_trips_through_sensor_event() -> None:
    demos = json.loads(
        (Path(__file__).resolve().parents[1] / "data" / "demo" / "demo_events.json").read_text(encoding="utf-8")
    )
    assert isinstance(demos, list)
    for item in demos:
        assert isinstance(item, dict)
        event = as_dict(item["event"])
        updated = {**event, "rpm": float(cast(float, event["rpm"])) + 1.0, "localized_label": "ignore"}
        payload = build_event_payload(event, updated)
        assert set(payload) == set(event)
        validated = SensorEvent.model_validate(payload)
        assert validated.sensor_dict()["rpm"] == float(cast(float, updated["rpm"]))


def test_unknown_keys_fall_back_gracefully() -> None:
    assert localized_fault_label("falha_desconhecida", "pt-BR") == "falha_desconhecida"
    assert localized_state_label("unknown_state", "en") == "unknown_state"
    assert localized_field_label("campo_inexistente", "pt-BR") == "campo_inexistente"
    assert localized_warning("mensagem inesperada", "en") == "mensagem inesperada"
    assert translate("chave_inexistente", "pt-BR") == "chave_inexistente"
    assert localized_scenario_label("cenario_desconhecido", "en") == "cenario_desconhecido"


def test_recommended_question_follows_language() -> None:
    assert recommended_question("Pergunta em português?", "pt-BR") == "Pergunta em português?"
    assert recommended_question("Pergunta em português?", "en") == "Pergunta em português?\nAnswer in English."
    assert recommended_question("Answer in English, please.", "en") == "Answer in English, please."
    long_question = "x" * 500
    directive = recommended_question(long_question, "en")
    assert len(directive) <= 500
    assert directive.endswith("Answer in English.")


def test_known_warnings_are_localized() -> None:
    source = "Serviço de linguagem indisponível; síntese documental utilizada."
    assert localized_warning(source, "pt-BR") == source
    assert localized_warning(source, "en") == "Language service unavailable; document synthesis used."


def test_core_ui_terms_are_natural_in_portuguese() -> None:
    expected = {
        "title": "Manutenção prescritiva",
        "overview": "Visão geral",
        "new_analysis": "Nova análise",
        "diagnosis_actions": "Diagnóstico e ações",
        "evidence": "Evidências",
        "quality_limits": "Qualidade e limites",
        "predicted_fault": "Falha provável",
        "similar_events": "Eventos semelhantes",
        "documentation_available": "Documento disponível",
        "safety_checks": "Verificações de segurança",
    }
    for key, value in expected.items():
        assert TRANSLATIONS["pt-BR"][key] == value


def test_core_ui_terms_differ_between_languages() -> None:
    core_keys = {"title", "overview", "new_analysis", "predicted_fault", "similar_events"}
    for key in core_keys:
        assert TRANSLATIONS["pt-BR"][key] != TRANSLATIONS["en"][key]


def test_test_sessions_labels_are_explicit() -> None:
    assert TRANSLATIONS["pt-BR"]["test_sessions"] == "Sessões de teste"
    assert TRANSLATIONS["en"]["test_sessions"] == "Test sessions"
    assert TRANSLATIONS["pt-BR"]["independent_sessions"] == "Sessões no teste independente"
    assert TRANSLATIONS["en"]["independent_sessions"] == "Sessions in the independent test set"


def test_language_selector_labels_and_note() -> None:
    assert TRANSLATIONS["pt-BR"]["language"] == "Idioma da interface"
    assert TRANSLATIONS["en"]["language"] == "Interface language"
    assert TRANSLATIONS["en"]["language_note"] == "Technical source excerpts may remain in their original language."
    assert TRANSLATIONS["pt-BR"]["language_note"].strip()


def test_undocumented_scenarios_explicitly_refuse() -> None:
    assert TRANSLATIONS["pt-BR"]["scenario_eccentric"] == "Rotor excêntrico — sem documento"
    assert TRANSLATIONS["pt-BR"]["scenario_phase_loss"] == "Perda de fase — sem documento"
    assert TRANSLATIONS["en"]["scenario_eccentric"] == "Eccentric rotor — no documentation"
    assert TRANSLATIONS["en"]["scenario_phase_loss"] == "Phase loss — no documentation"


def test_localized_integer_format() -> None:
    assert localized_integer_format(166796, "pt-BR") == "166.796"
    assert localized_integer_format(166796, "en") == "166,796"
    assert localized_integer_format(74, "pt-BR") == "74"
    assert localized_integer_format(74, "en") == "74"
    assert localized_integer_format(1000000, "pt-BR") == "1.000.000"
    assert localized_integer_format(1000000, "en") == "1,000,000"


def test_localized_date_formats() -> None:
    assert localized_date_format("pt-BR") == "%d/%m/%Y"
    assert localized_date_format("en") == "%m/%d/%Y"


def test_localized_datetime_formats() -> None:
    assert localized_datetime_format("pt-BR") == "%d/%m/%Y %H:%M"
    assert localized_datetime_format("en") == "%m/%d/%Y %H:%M"


def test_technical_excerpts_are_preserved_in_original_language() -> None:
    root = Path(__file__).resolve().parents[1]
    index = json.loads((root / "artifacts" / "knowledge_index.json").read_text(encoding="utf-8"))
    chunks = cast(list[dict[str, object]], index["chunks"])
    assert chunks, "indice documental sem trechos"
    excerpts = [str(chunk["text"])[:650] for chunk in chunks if not str(chunk["text"]).isspace()]
    assert excerpts, "indice documental sem trechos de texto"
    original_language_text = next(
        text for text in excerpts
        if any(char in text for char in "ãçêõáéíóú")
    )
    pt_values = set(TRANSLATIONS["pt-BR"].values())
    en_values = set(TRANSLATIONS["en"].values())
    assert original_language_text not in pt_values
    assert original_language_text not in en_values
    assert all(text.strip() for text in excerpts[:5])


def test_no_mojibake_in_interface_files() -> None:
    mojibake_sequences = (
        chr(0xC3) + chr(0xA3), chr(0xC3) + chr(0xA7), chr(0xC3) + chr(0xA9),
        chr(0xC3) + chr(0xAA), chr(0xC3) + chr(0xAD), chr(0xC3) + chr(0xB3),
        chr(0xC3) + chr(0xB4), chr(0xC3) + chr(0xBA), chr(0xC3) + chr(0xB1),
        chr(0xC2) + chr(0xB0), chr(0xE2) + chr(0x80) + chr(0x9C),
    )
    root = Path(__file__).resolve().parents[1]
    files = (root / "app" / "streamlit_app.py", root / "app" / "ui_localization.py")
    for path in files:
        text = path.read_text(encoding="utf-8")
        for sequence in mojibake_sequences:
            assert sequence not in text, (path, sequence)
