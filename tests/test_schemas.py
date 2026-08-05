import math

import pytest
from pydantic import ValidationError

from fiesc_pm.schemas import SensorEvent


def test_sensor_event_accepts_valid_values(sample_event_dict: dict[str, float]) -> None:
    event = SensorEvent.model_validate(sample_event_dict)
    assert len(event.sensor_dict()) == 23


def test_sensor_event_rejects_infinite(sample_event_dict: dict[str, float]) -> None:
    sample_event_dict["x_kurtosis"] = math.inf
    with pytest.raises(ValidationError):
        SensorEvent.model_validate(sample_event_dict)


def test_sensor_event_rejects_unknown_fields(sample_event_dict: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        SensorEvent.model_validate({**sample_event_dict, "hidden_label": "bearing"})


def test_sensor_event_rejects_inconsistent_units(sample_event_dict: dict[str, float]) -> None:
    sample_event_dict["temperature_f"] = 120.0
    with pytest.raises(ValidationError, match="inconsistentes"):
        SensorEvent.model_validate(sample_event_dict)


def test_sensor_event_rejects_negative_vibration(sample_event_dict: dict[str, float]) -> None:
    sample_event_dict["z_rms_acceleration_g"] = -0.1
    with pytest.raises(ValidationError, match="negativo"):
        SensorEvent.model_validate(sample_event_dict)
