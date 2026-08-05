from __future__ import annotations

import pytest


@pytest.fixture
def sample_event_dict() -> dict[str, float]:
    return {
        "z_rms_velocity_in_s": 0.0427,
        "z_rms_velocity_mm_s": 1.086,
        "temperature_f": 74.0,
        "temperature_c": 23.33,
        "x_rms_velocity_in_s": 0.0619,
        "x_rms_velocity_mm_s": 1.573,
        "z_peak_acceleration_g": 0.031,
        "x_peak_acceleration_g": 0.033,
        "z_peak_vel_comp_freq_hz": 61.0,
        "x_peak_vel_comp_freq_hz": 61.0,
        "z_rms_acceleration_g": 0.046,
        "x_rms_acceleration_g": 0.066,
        "z_kurtosis": 3.276,
        "x_kurtosis": 3.25,
        "z_crest_factor": 4.435,
        "x_crest_factor": 3.918,
        "z_peak_velocity_in_s": 0.0605,
        "z_peak_velocity_mm_s": 1.536,
        "x_peak_velocity_in_s": 0.0875,
        "x_peak_velocity_mm_s": 2.224,
        "z_high_freq_rms_accel_g": 0.007,
        "x_high_freq_rms_accel_g": 0.008,
        "rpm": 0.0,
    }
