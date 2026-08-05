from __future__ import annotations

import json

from fiesc_pm.config import get_settings
from fiesc_pm.ingestion import audit_dataset, load_dataset, prepare_training_data
from fiesc_pm.modeling import save_model_bundle, train_models


def main() -> None:
    settings = get_settings()
    csv_path = settings.source_dir / "banner.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Base nao encontrada: {csv_path}")

    frame = load_dataset(csv_path)
    audit = audit_dataset(frame, csv_path)
    features, labels, groups, deduplicated = prepare_training_data(frame)
    counts = frame["canonical_fault"].value_counts().to_dict()
    bundle, metrics = train_models(
        features,
        labels,
        groups,
        deduplicated,
        full_occurrence_counts=counts,
    )
    save_model_bundle(
        bundle,
        metrics,
        settings.model_path,
        settings.metadata_path,
        settings.metrics_path,
        audit,
    )

    print(json.dumps({"audit": audit, "metrics": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
