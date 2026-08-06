from __future__ import annotations

from app.ui_localization import (
    FAULT_KEYS,
    FAULT_LABELS,
    FIELD_KEYS,
    FIELD_LABELS,
    STATE_KEYS,
    STATE_LABELS,
    TRANSLATIONS,
    localized_fault_label,
    localized_state_label,
    preserve_technical_keys,
)


def test_translations_exist_for_both_languages() -> None:
    assert set(TRANSLATIONS) == {"pt-BR", "en"}
    assert set(TRANSLATIONS["pt-BR"]) == set(TRANSLATIONS["en"])


def test_all_known_labels_are_translated() -> None:
    for language in ("pt-BR", "en"):
        assert not set(FIELD_KEYS) - set(FIELD_LABELS[language])
        assert not set(FAULT_KEYS) - set(FAULT_LABELS[language])
        assert not set(STATE_KEYS) - set(STATE_LABELS[language])


def test_internal_field_names_are_preserved() -> None:
    original = {"x_rms_velocity_mm_s": 1.0, "temperature_c": 20.0}
    edited = {"x_rms_velocity_mm_s": 2.0, "temperature_c": 21.0, "localized_label": "ignore"}
    result = preserve_technical_keys(original, edited)
    assert result == {"x_rms_velocity_mm_s": 2.0, "temperature_c": 21.0}
    assert set(result) == set(original)


def test_known_fault_and_state_translations() -> None:
    assert localized_fault_label("misalignment", "pt-BR") == "Desalinhamento"
    assert localized_fault_label("bearing", "en") == "Bearing"
    assert localized_state_label("motor_off", "pt-BR") == "Motor desligado"
    assert localized_state_label("operating", "en") == "Operating"


def test_languages_do_not_share_visible_values_for_core_terms() -> None:
    core_keys = {"title", "overview", "new_analysis", "predicted_fault", "similar_events"}
    for key in core_keys:
        assert TRANSLATIONS["pt-BR"][key] != TRANSLATIONS["en"][key]
