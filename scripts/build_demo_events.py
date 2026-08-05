from __future__ import annotations

import json

import numpy as np

from fiesc_pm.config import get_settings
from fiesc_pm.features import build_features
from fiesc_pm.ingestion import load_dataset
from fiesc_pm.modeling import load_model_bundle
from fiesc_pm.schemas import SENSOR_FIELDS


def main() -> None:
    settings = get_settings()
    frame = load_dataset(settings.source_dir / "banner.csv")
    bundle = load_model_bundle(settings.model_path)
    features = build_features(frame).loc[:, bundle.feature_names]
    probabilities = bundle.estimator.predict_proba(features)
    class_names = np.asarray(bundle.estimator.classes_, dtype=str)
    predicted_indexes = np.argmax(probabilities, axis=1)
    predicted = class_names[predicted_indexes]
    confidence = probabilities[np.arange(len(frame)), predicted_indexes]

    scenarios = [
        ("falha_documentada_rolamento", "bearing", "supported"),
        ("falha_documentada_desalinhamento", "misalignment", "supported"),
        ("sem_documento_rotor_excentrico", "eccentric_rotor", "unsupported_documentation"),
        ("sem_documento_perda_de_fase", "phase_loss", "unsupported_documentation"),
        ("operacao_normal", "normal", "normal_operation"),
    ]
    demos: list[dict[str, object]] = []
    canonical = frame["canonical_fault"].to_numpy(dtype=str)
    rpm = frame["rpm"].to_numpy(dtype=float)

    for name, family, expected_status in scenarios:
        mask = (
            (canonical == family)
            & (predicted == family)
            & (confidence >= bundle.confidence_threshold)
            & (rpm > 1)
        )
        candidates = np.flatnonzero(mask)
        if not len(candidates):
            raise RuntimeError(f"Nenhum demo confiavel para {family}")
        candidates = candidates[np.argsort(confidence[candidates])[::-1][:500]]
        candidate_scaled = bundle.neighbor_scaler.transform(features.iloc[candidates])
        distances, _ = bundle.neighbor_index.kneighbors(candidate_scaled, n_neighbors=1)
        candidate_novelty = distances[:, 0] / bundle.novelty_distance_threshold
        accepted = np.flatnonzero(candidate_novelty <= 1.0)
        if not len(accepted):
            raise RuntimeError(f"Nenhum demo dentro da distribuicao para {family}")
        score = confidence[candidates[accepted]] - candidate_novelty[accepted] * 0.05
        selected_position = int(accepted[int(np.argmax(score))])
        row_index = int(candidates[selected_position])
        selected_novelty = float(candidate_novelty[selected_position])
        row = frame.iloc[row_index]
        event: dict[str, object] = {field: float(row[field]) for field in SENSOR_FIELDS}
        demos.append(
            {
                "name": name,
                "expected_fault": family,
                "expected_status": expected_status,
                "confidence": float(confidence[row_index]),
                "novelty_score": selected_novelty,
                "event": event,
            }
        )

    low_mask = (predicted != "normal") & (rpm > 1) & (confidence < bundle.confidence_threshold)
    low_candidates = np.flatnonzero(low_mask)
    if not len(low_candidates):
        raise RuntimeError("Nenhum evento de baixa confianca encontrado")
    low_score = np.abs(confidence[low_candidates] - bundle.confidence_threshold)
    low_index = int(low_candidates[int(np.argmin(low_score))])
    low_scaled = bundle.neighbor_scaler.transform(features.iloc[[low_index]])
    low_distances, _ = bundle.neighbor_index.kneighbors(low_scaled, n_neighbors=1)
    low_novelty = float(low_distances[0, 0] / bundle.novelty_distance_threshold)
    low_row = frame.iloc[low_index]
    low_event: dict[str, object] = {field: float(low_row[field]) for field in SENSOR_FIELDS}
    demos.append(
        {
            "name": "baixa_confianca",
            "expected_fault": str(predicted[low_index]),
            "expected_status": "low_confidence",
            "confidence": float(confidence[low_index]),
            "novelty_score": low_novelty,
            "event": low_event,
        }
    )

    output = settings.repo_root / "data" / "demo" / "demo_events.json"
    output.write_text(json.dumps(demos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(demos, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
