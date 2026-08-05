from __future__ import annotations

import re
import unicodedata

CANONICAL_LABELS = (
    "normal",
    "bearing",
    "misalignment",
    "imbalance",
    "belt",
    "pulley",
    "cocked_rotor",
    "eccentric_rotor",
    "fan",
    "phase_loss",
    "unknown",
)


def normalize_label(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def canonicalize_fault(value: object) -> str:
    label = normalize_label(value)
    if "falta_fase" in label or "phase_loss" in label:
        return "phase_loss"
    if "rolamento" in label or "bearing" in label:
        return "bearing"
    if "desalinh" in label or "misalign" in label:
        return "misalignment"
    imbalance_tokens = (
        "balance",
        "balanc",
        "desabanc",
        "desbanlanc",
        "desabance",
        "desbalance",
    )
    if any(token in label for token in imbalance_tokens):
        return "imbalance"
    if "correia" in label or "belt" in label:
        return "belt"
    if "polia" in label or "pulley" in label:
        return "pulley"
    if "cock" in label or "rotor_inclinado" in label:
        return "cocked_rotor"
    if "eccentric" in label or "excentric" in label:
        return "eccentric_rotor"
    if "ventoinha" in label or "ventilador" in label or label.startswith("fan"):
        return "fan"
    normal_tokens = (
        "normal",
        "normla",
        "baseline",
        "teste",
        "new_tes",
        "motor_desligado",
        "mortor_desligado",
        "acelerando",
    )
    if any(token in label for token in normal_tokens):
        return "normal"
    return "unknown"


def operating_state(raw_label: object | None, rpm: float) -> str:
    label = normalize_label(raw_label or "")
    if rpm <= 1 or "desligado" in label:
        return "motor_off"
    if "aceler" in label:
        return "acceleration"
    return "operating"
