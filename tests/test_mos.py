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


def test_charge_sign_convention(
    reference_mos: MOSCapacitor,
) -> None:
    q_accumulation = reference_mos.solver.semiconductor_charge(-0.1)
    q_depletion = reference_mos.solver.semiconductor_charge(0.1)
    q_inversion = reference_mos.solver.semiconductor_charge(1.0)

    assert q_accumulation > 0.0
    assert q_depletion < 0.0
    assert q_inversion < 0.0


def test_charge_is_zero_at_flatband(
    reference_mos: MOSCapacitor,
) -> None:
    assert reference_mos.solver.semiconductor_charge(0.0) == pytest.approx(
        0.0,
        abs=1e-30,
    )


def test_semiconductor_capacitance_positive(
    reference_mos: MOSCapacitor,
) -> None:
    for psi_s in [
        -1.0,
        -0.5,
        -0.1,
        0.01,
        0.1,
        0.3,
        0.7,
        1.0,
        2.0,
    ]:
        c_s = reference_mos.solver.semiconductor_capacitance_per_area(psi_s)

        assert math.isfinite(c_s)
        assert c_s > 0.0


def test_numerical_solver_flatband(
    reference_mos: MOSCapacitor,
) -> None:
    psi_s = reference_mos.numerical_surface_potential(reference_mos.V_FB)

    assert psi_s == pytest.approx(
        0.0,
        abs=1e-10,
    )


def test_numerical_solver_accumulation(
    reference_mos: MOSCapacitor,
) -> None:
    psi_s = reference_mos.numerical_surface_potential(-1.0)

    assert psi_s < 0.0


def test_numerical_solver_depletion(
    reference_mos: MOSCapacitor,
) -> None:
    psi_s = reference_mos.numerical_surface_potential(0.5)

    assert 0.0 < psi_s < 2.0 * reference_mos.phi_F


def test_numerical_solver_inversion(
    reference_mos: MOSCapacitor,
) -> None:
    psi_s = reference_mos.numerical_surface_potential(2.0)

    assert psi_s > 2.0 * reference_mos.phi_F


def test_numerical_solver_residual(
    reference_mos: MOSCapacitor,
) -> None:
    result = reference_mos.solver.solve(
        voltage=0.5,
        v_fb=reference_mos.V_FB,
        c_ox_per_area=reference_mos.Cox_per_area,
    )

    assert abs(result.residual) < 1e-9


def test_high_frequency_inversion_capacitance(
    reference_mos: MOSCapacitor,
) -> None:
    capacitance = reference_mos.numerical_capacitance(
        voltage=2.0,
        high_frequency=True,
    )

    assert capacitance == pytest.approx(
        reference_mos.Cmin,
        rel=1e-8,
    )


def test_low_frequency_inversion_capacitance(
    reference_mos: MOSCapacitor,
) -> None:
    capacitance = reference_mos.numerical_capacitance(
        voltage=2.0,
        high_frequency=False,
    )

    assert capacitance > reference_mos.Cmin
    assert capacitance <= reference_mos.Cox


def test_numerical_solver_is_consistent_with_level1_regions(
    reference_mos: MOSCapacitor,
) -> None:
    for voltage in [0.1, 0.3, 0.5, 0.7]:
        level1 = reference_mos.level1_point(voltage)
        numerical = reference_mos.numerical_surface_potential(voltage)

        assert level1.region == "depletion"
        assert 0.0 < numerical < 2.0 * reference_mos.phi_F


def test_numerical_solver_large_voltage_range(
    reference_mos: MOSCapacitor,
) -> None:
    for voltage in [-20.0, -10.0, -5.0, 0.0, 5.0, 10.0, 20.0]:
        psi_s = reference_mos.numerical_surface_potential(voltage)

        assert math.isfinite(psi_s)

        capacitance = reference_mos.numerical_capacitance(
            voltage,
            high_frequency=True,
        )

        assert math.isfinite(capacitance)
        assert 0.0 < capacitance <= reference_mos.Cox

def test_thicker_oxide_reduces_oxide_capacitance() -> None:
    thin = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=5.0,
            area_um2=100.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
        )
    )

    thick = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=20.0,
            area_um2=100.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
        )
    )

    assert thick.Cox < thin.Cox


def test_larger_area_increases_oxide_capacitance() -> None:
    small = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=10.0,
            area_um2=50.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
        )
    )

    large = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=10.0,
            area_um2=200.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
        )
    )

    assert large.Cox > small.Cox


def test_higher_doping_reduces_maximum_depletion_width() -> None:
    low_doping = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e15,
            tox_nm=10.0,
            area_um2=100.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
        )
    )

    high_doping = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e17,
            tox_nm=10.0,
            area_um2=100.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
        )
    )

    assert high_doping.Wd_max < low_doping.Wd_max


def test_accumulation_capacitance_approaches_oxide_capacitance(
    reference_mos: MOSCapacitor,
) -> None:
    capacitance = reference_mos.numerical_capacitance(
        -5.0,
        high_frequency=True,
    )

    assert capacitance < reference_mos.Cox
    assert capacitance / reference_mos.Cox > 0.98


def test_high_frequency_inversion_is_frozen(
    reference_mos: MOSCapacitor,
) -> None:
    c1 = reference_mos.numerical_capacitance(
        1.0,
        high_frequency=True,
    )
    c2 = reference_mos.numerical_capacitance(
        5.0,
        high_frequency=True,
    )

    assert c1 == pytest.approx(c2, rel=1e-10)
    assert c1 == pytest.approx(reference_mos.Cmin, rel=1e-10)


def test_quasi_static_inversion_rises_with_voltage(
    reference_mos: MOSCapacitor,
) -> None:
    c1 = reference_mos.numerical_capacitance(
        1.0,
        high_frequency=False,
    )
    c2 = reference_mos.numerical_capacitance(
        2.0,
        high_frequency=False,
    )
    c3 = reference_mos.numerical_capacitance(
        5.0,
        high_frequency=False,
    )

    assert c1 < c2 < c3
    assert c3 <= reference_mos.Cox


def test_high_doping_numerical_solver() -> None:
    mos = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e18,
            tox_nm=10.0,
            area_um2=100.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
        )
    )

    for voltage in [-10.0, -5.0, 0.0, 1.0, 5.0, 10.0]:
        psi_s = mos.numerical_surface_potential(voltage)
        capacitance = mos.numerical_capacitance(
            voltage,
            high_frequency=True,
        )

        assert math.isfinite(psi_s)
        assert math.isfinite(capacitance)
        assert 0.0 < capacitance <= mos.Cox

def test_intrinsic_carrier_concentration_changes_with_temperature() -> None:
    cold = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=10.0,
            area_um2=100.0,
            temperature_K=250.0,
            phi_ms_V=0.0,
        )
    )

    hot = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=10.0,
            area_um2=100.0,
            temperature_K=350.0,
            phi_ms_V=0.0,
        )
    )

    assert hot.ni > cold.ni

def test_oxide_charge_shifts_flatband_voltage() -> None:
    no_charge = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=10.0,
            area_um2=100.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
            q_ox_C_m2=0.0,
        )
    )

    charged = MOSCapacitor(
        MOSParameters.from_gui_units(
            NA_cm3=1e16,
            tox_nm=10.0,
            area_um2=100.0,
            temperature_K=300.0,
            phi_ms_V=0.0,
            q_ox_C_m2=1e-5,
        )
    )

    expected = -1e-5 / charged.Cox_per_area

    assert charged.V_FB == pytest.approx(expected)
    assert charged.V_FB < no_charge.V_FB            