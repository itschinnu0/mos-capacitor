import math

import pytest

from physics.mos_capacitor import MOSCapacitor
from physics.parameters import MOSParameters


@pytest.fixture
def reference_mos() -> MOSCapacitor:
    parameters = MOSParameters.from_gui_units(
        NA_cm3=1e16,
        tox_nm=10.0,
        area_um2=100.0,
        temperature_K=300.0,
        phi_ms_V=0.0,
        q_ox_C_m2=0.0,
    )

    return MOSCapacitor(parameters)


def test_oxide_capacitance(reference_mos: MOSCapacitor) -> None:
    assert reference_mos.Cox == pytest.approx(
        3.4531332469920006e-13,
        rel=1e-10,
    )


def test_oxide_capacitance_per_area(
    reference_mos: MOSCapacitor,
) -> None:
    assert reference_mos.Cox_per_area == pytest.approx(
        3.4531332469920004e-3,
        rel=1e-10,
    )


def test_fermi_potential(reference_mos: MOSCapacitor) -> None:
    assert reference_mos.phi_F == pytest.approx(
        0.3698644999770504,
        rel=1e-10,
    )


def test_flat_band_voltage(reference_mos: MOSCapacitor) -> None:
    assert reference_mos.V_FB == pytest.approx(0.0)


def test_threshold_voltage(reference_mos: MOSCapacitor) -> None:
    assert reference_mos.V_T == pytest.approx(
        0.8832318333350341,
        rel=1e-10,
    )


def test_maximum_depletion_width(
    reference_mos: MOSCapacitor,
) -> None:
    assert reference_mos.Wd_max == pytest.approx(
        3.0928824854229785e-7,
        rel=1e-10,
    )


def test_minimum_capacitance(
    reference_mos: MOSCapacitor,
) -> None:
    assert reference_mos.Cmin == pytest.approx(
        3.0532739596740063e-14,
        rel=1e-10,
    )


def test_accumulation(reference_mos: MOSCapacitor) -> None:
    point = reference_mos.level1_point(-1.0)

    assert point.region == "accumulation"
    assert point.capacitance == pytest.approx(
        reference_mos.Cox,
        rel=1e-12,
    )
    assert point.surface_potential < 0.0


def test_depletion(reference_mos: MOSCapacitor) -> None:
    point = reference_mos.level1_point(0.5)

    assert point.region == "depletion"
    assert 0.0 < point.surface_potential
    assert point.surface_potential < 2.0 * reference_mos.phi_F
    assert point.depletion_width > 0.0
    assert point.depletion_capacitance > 0.0
    assert point.capacitance < reference_mos.Cox


def test_inversion(reference_mos: MOSCapacitor) -> None:
    point = reference_mos.level1_point(2.0)

    assert point.region == "inversion"
    assert point.surface_potential >= 2.0 * reference_mos.phi_F
    assert point.depletion_width == pytest.approx(
        reference_mos.Wd_max,
        rel=1e-12,
    )
    assert point.capacitance == pytest.approx(
        reference_mos.Cmin,
        rel=1e-12,
    )


def test_flatband_boundary(reference_mos: MOSCapacitor) -> None:
    point = reference_mos.level1_point(reference_mos.V_FB)

    assert point.surface_potential == pytest.approx(0.0)
    assert point.capacitance == pytest.approx(
        reference_mos.Cox,
        rel=1e-12,
    )


def test_surface_potential_increases_with_gate_voltage(
    reference_mos: MOSCapacitor,
) -> None:
    psi_1 = reference_mos.level1_surface_potential(0.2)
    psi_2 = reference_mos.level1_surface_potential(0.5)
    psi_3 = reference_mos.level1_surface_potential(1.0)

    assert psi_1 < psi_2 < psi_3


def test_level1_cv_generation(
    reference_mos: MOSCapacitor,
) -> None:
    data = reference_mos.generate_level1_cv(
        voltage_min=-5.0,
        voltage_max=5.0,
        voltage_step=0.01,
    )

    assert len(data) > 0
    assert data[0].voltage == pytest.approx(-5.0)
    assert data[-1].voltage <= 5.0

    regions = {point.region for point in data}

    assert "accumulation" in regions
    assert "depletion" in regions
    assert "inversion" in regions


def test_level1_capacitance_bounds(
    reference_mos: MOSCapacitor,
) -> None:
    data = reference_mos.generate_level1_cv(
        voltage_min=-5.0,
        voltage_max=5.0,
        voltage_step=0.01,
    )

    for point in data:
        assert math.isfinite(point.capacitance)
        assert 0.0 < point.capacitance <= reference_mos.Cox
