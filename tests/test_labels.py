from fiesc_pm.labels import canonicalize_fault, operating_state


def test_representative_label_mapping() -> None:
    cases = {
        "rolamento_inner_2": "bearing",
        "new_desalinhado_4": "misalignment",
        "desbanlanceado_carga_3_2": "imbalance",
        "correia_2": "belt",
        "polia": "pulley",
        "cockecocked_adxl_0": "cocked_rotor",
        "eccentric_adxl_0": "eccentric_rotor",
        "ventoinha_3": "fan",
        "new_falta_fase_2": "phase_loss",
        "normla_carga_3_3": "normal",
        "mortor_desligado_novo": "normal",
    }
    assert {key: canonicalize_fault(key) for key in cases} == cases


def test_operating_state() -> None:
    assert operating_state("motor_desligado", 0) == "motor_off"
    assert operating_state("acelerando", 500) == "acceleration"
    assert operating_state("rolamento_inner", 1000) == "operating"
