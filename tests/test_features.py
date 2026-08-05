import numpy as np

from fiesc_pm.features import MODEL_FEATURES, build_features


def test_feature_engineering_handles_zero_rpm(sample_event_dict: dict[str, float]) -> None:
    features = build_features(sample_event_dict)
    assert list(features.columns) == list(MODEL_FEATURES)
    assert np.isfinite(features.to_numpy()).all()
    assert features.iloc[0]["order_z"] == 0
    assert features.iloc[0]["order_x"] == 0
