from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

BASE_FEATURES = (
    "rpm",
    "temperature_c",
    "z_rms_velocity_mm_s",
    "x_rms_velocity_mm_s",
    "z_peak_acceleration_g",
    "x_peak_acceleration_g",
    "z_peak_vel_comp_freq_hz",
    "x_peak_vel_comp_freq_hz",
    "z_rms_acceleration_g",
    "x_rms_acceleration_g",
    "z_kurtosis",
    "x_kurtosis",
    "z_crest_factor",
    "x_crest_factor",
    "z_peak_velocity_mm_s",
    "x_peak_velocity_mm_s",
    "z_high_freq_rms_accel_g",
    "x_high_freq_rms_accel_g",
)

DERIVED_FEATURES = (
    "order_z",
    "order_x",
    "rms_velocity_ratio_zx",
    "peak_velocity_ratio_zx",
    "rms_acceleration_ratio_zx",
    "high_freq_ratio_zx",
    "rms_velocity_delta_zx",
    "peak_frequency_delta_zx",
    "crest_factor_delta_zx",
    "kurtosis_delta_zx",
    "velocity_peak_to_rms_z",
    "velocity_peak_to_rms_x",
)

MODEL_FEATURES = BASE_FEATURES + DERIVED_FEATURES


def _safe_ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    output = np.zeros_like(numerator, dtype=np.float64)
    np.divide(numerator, denominator, out=output, where=np.abs(denominator) > 1e-9)
    return output


def build_features(data: pd.DataFrame | Mapping[str, float]) -> pd.DataFrame:
    frame = pd.DataFrame([data]) if isinstance(data, Mapping) else data.copy()
    missing = sorted(set(BASE_FEATURES) - set(frame.columns))
    if missing:
        raise ValueError(f"Campos necessarios ausentes: {missing}")

    result = frame.loc[:, BASE_FEATURES].astype("float64")
    rpm_hz = result["rpm"].to_numpy() / 60.0
    z_freq = result["z_peak_vel_comp_freq_hz"].to_numpy()
    x_freq = result["x_peak_vel_comp_freq_hz"].to_numpy()
    result["order_z"] = _safe_ratio(z_freq, rpm_hz)
    result["order_x"] = _safe_ratio(x_freq, rpm_hz)
    result["rms_velocity_ratio_zx"] = _safe_ratio(
        result["z_rms_velocity_mm_s"].to_numpy(), result["x_rms_velocity_mm_s"].to_numpy()
    )
    result["peak_velocity_ratio_zx"] = _safe_ratio(
        result["z_peak_velocity_mm_s"].to_numpy(), result["x_peak_velocity_mm_s"].to_numpy()
    )
    result["rms_acceleration_ratio_zx"] = _safe_ratio(
        result["z_rms_acceleration_g"].to_numpy(), result["x_rms_acceleration_g"].to_numpy()
    )
    result["high_freq_ratio_zx"] = _safe_ratio(
        result["z_high_freq_rms_accel_g"].to_numpy(),
        result["x_high_freq_rms_accel_g"].to_numpy(),
    )
    result["rms_velocity_delta_zx"] = result["z_rms_velocity_mm_s"] - result["x_rms_velocity_mm_s"]
    result["peak_frequency_delta_zx"] = (
        result["z_peak_vel_comp_freq_hz"] - result["x_peak_vel_comp_freq_hz"]
    )
    result["crest_factor_delta_zx"] = result["z_crest_factor"] - result["x_crest_factor"]
    result["kurtosis_delta_zx"] = result["z_kurtosis"] - result["x_kurtosis"]
    result["velocity_peak_to_rms_z"] = _safe_ratio(
        result["z_peak_velocity_mm_s"].to_numpy(), result["z_rms_velocity_mm_s"].to_numpy()
    )
    result["velocity_peak_to_rms_x"] = _safe_ratio(
        result["x_peak_velocity_mm_s"].to_numpy(), result["x_rms_velocity_mm_s"].to_numpy()
    )
    values = np.nan_to_num(
        result.loc[:, MODEL_FEATURES].to_numpy(), nan=0.0, posinf=0.0, neginf=0.0
    )
    return pd.DataFrame(values.astype("float32"), columns=MODEL_FEATURES, index=frame.index)
