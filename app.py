import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from physics.mos_capacitor import MOSCapacitor
from physics.parameters import MOSParameters


st.set_page_config(
    page_title="MOS Capacitor Simulator",
    page_icon="⚡",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def engineering_capacitance(value_f: float) -> str:
    """Format capacitance using an appropriate engineering prefix."""
    if value_f >= 1e-9:
        return f"{value_f * 1e9:.4f} nF"
    if value_f >= 1e-12:
        return f"{value_f * 1e12:.4f} pF"
    if value_f >= 1e-15:
        return f"{value_f * 1e15:.4f} fF"
    return f"{value_f:.4e} F"


def engineering_length(value_m: float) -> str:
    """Format length using an appropriate engineering prefix."""
    if value_m >= 1e-3:
        return f"{value_m * 1e3:.4f} mm"
    if value_m >= 1e-6:
        return f"{value_m * 1e6:.4f} µm"
    if value_m >= 1e-9:
        return f"{value_m * 1e9:.4f} nm"
    return f"{value_m:.4e} m"


def create_parameters(
    na_cm3: float,
    tox_nm: float,
    area_um2: float,
    temperature_k: float,
    phi_ms_v: float,
    q_ox_c_m2: float,
) -> MOSParameters:
    """Create validated SI-based MOS parameters."""
    return MOSParameters.from_gui_units(
        NA_cm3=na_cm3,
        tox_nm=tox_nm,
        area_um2=area_um2,
        temperature_K=temperature_k,
        phi_ms_V=phi_ms_v,
        q_ox_C_m2=q_ox_c_m2,
    )


# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------

st.title("MOS Capacitor C–V Simulator")

st.caption(
    "Ideal p-type silicon MOS capacitor — analytical and numerical "
    "surface-potential models"
)

# ---------------------------------------------------------------------------
# Sidebar — Device parameters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Device Parameters")

    na_cm3 = st.number_input(
        "Substrate doping Nₐ (cm⁻³)",
        min_value=1e10,
        max_value=1e20,
        value=1e16,
        format="%.3e",
    )

    tox_nm = st.number_input(
        "Oxide thickness tₒₓ (nm)",
        min_value=0.1,
        max_value=1000.0,
        value=10.0,
        step=0.5,
    )

    area_um2 = st.number_input(
        "Gate area A (µm²)",
        min_value=0.01,
        max_value=1e12,
        value=100.0,
        step=10.0,
    )

    temperature_k = st.number_input(
        "Temperature T (K)",
        min_value=1.0,
        max_value=1000.0,
        value=300.0,
        step=1.0,
    )

    phi_ms_v = st.number_input(
        "Metal-semiconductor work-function difference ΦMS (V)",
        value=0.0,
        step=0.01,
    )

    q_ox_c_m2 = st.number_input(
        "Oxide charge Qox (C/m²)",
        value=0.0,
        step=1e-6,
        format="%.3e",
    )

    st.divider()

    st.header("Simulation")

    frequency_mode = st.radio(
        "Frequency mode",
        options=[
            "High Frequency",
            "Low Frequency / Quasi-static",
        ],
    )

    voltage_min = st.number_input(
        "Voltage minimum (V)",
        value=-5.0,
        step=0.5,
    )

    voltage_max = st.number_input(
        "Voltage maximum (V)",
        value=5.0,
        step=0.5,
    )

    voltage_step = st.number_input(
        "Voltage step (V)",
        min_value=0.0001,
        value=0.01,
        step=0.01,
        format="%.4f",
    )

    st.divider()

    simulate = st.button(
        "Simulate / Update",
        type="primary",
        use_container_width=True,
    )

    reset = st.button(
        "Reset to Defaults",
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

if reset:
    st.rerun()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

if voltage_max <= voltage_min:
    st.error("Voltage maximum must be greater than voltage minimum.")
    st.stop()

if voltage_step <= 0:
    st.error("Voltage step must be greater than zero.")
    st.stop()


# ---------------------------------------------------------------------------
# Physics model
# ---------------------------------------------------------------------------

try:
    parameters = create_parameters(
        na_cm3=na_cm3,
        tox_nm=tox_nm,
        area_um2=area_um2,
        temperature_k=temperature_k,
        phi_ms_v=phi_ms_v,
        q_ox_c_m2=q_ox_c_m2,
    )

    mos = MOSCapacitor(parameters)

except ValueError as exc:
    st.error(f"Invalid device parameters: {exc}")
    st.stop()

except Exception as exc:
    st.error(f"Unable to initialize MOS model: {exc}")
    st.stop()


# ---------------------------------------------------------------------------
# Calculated results
# ---------------------------------------------------------------------------

st.header("Calculated Device Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Oxide capacitance",
        engineering_capacitance(mos.Cox),
    )

    st.metric(
        "Oxide capacitance / area",
        f"{mos.Cox_per_area:.4e} F/m²",
    )

    st.metric(
        "Fermi potential",
        f"{mos.phi_F:.5f} V",
    )

with col2:
    st.metric(
        "Flat-band voltage",
        f"{mos.V_FB:.5f} V",
    )

    st.metric(
        "Threshold voltage",
        f"{mos.V_T:.5f} V",
    )

    st.metric(
        "Maximum depletion width",
        engineering_length(mos.Wd_max),
    )

with col3:
    st.metric(
        "Minimum capacitance",
        engineering_capacitance(mos.Cmin),
    )

    st.metric(
        "Intrinsic carrier concentration",
        f"{mos.ni:.4e} m⁻³",
    )

    st.metric(
        "2ΦF",
        f"{2.0 * mos.phi_F:.5f} V",
    )


# ---------------------------------------------------------------------------
# Generate C-V data
# ---------------------------------------------------------------------------

high_frequency = frequency_mode == "High Frequency"

try:
    voltage_points = mos.generate_level1_cv(
        voltage_min=voltage_min,
        voltage_max=voltage_max,
        voltage_step=voltage_step,
    )

    numerical_rows = []

    for point in voltage_points:
        psi_s = mos.numerical_surface_potential(point.voltage)

        capacitance = mos.numerical_capacitance(
            point.voltage,
            high_frequency=high_frequency,
        )

        if psi_s < 0.0:
            region = "Accumulation"
        elif psi_s < 2.0 * mos.phi_F:
            region = "Depletion"
        else:
            region = "Inversion"

        numerical_rows.append(
            {
                "Voltage": point.voltage,
                "Capacitance": capacitance,
                "Region": region,
                "Surface Potential": psi_s,
            }
        )

    cv_data = pd.DataFrame(numerical_rows)

except Exception as exc:
    st.error(f"Numerical C–V calculation failed: {exc}")
    st.stop()


# ---------------------------------------------------------------------------
# C-V plot
# ---------------------------------------------------------------------------

st.header("C–V Characteristic")

fig, ax = plt.subplots(figsize=(11, 5))

ax.plot(
    cv_data["Voltage"],
    cv_data["Capacitance"] * 1e12,
    linewidth=2,
    label=frequency_mode,
)

ax.axvline(
    mos.V_FB,
    linestyle="--",
    linewidth=1,
    label=f"VFB = {mos.V_FB:.3f} V",
)

ax.axvline(
    mos.V_T,
    linestyle="--",
    linewidth=1,
    label=f"VT = {mos.V_T:.3f} V",
)

ax.set_xlabel("Gate Voltage, V_G (V)")
ax.set_ylabel("Capacitance (pF)")
ax.set_title("MOS Capacitor C–V Characteristic")
ax.grid(True, alpha=0.25)
ax.legend()

st.pyplot(fig, use_container_width=True)

plt.close(fig)


# ---------------------------------------------------------------------------
# Applied voltage analysis
# ---------------------------------------------------------------------------

st.header("Applied Voltage Analysis")

applied_voltage = st.number_input(
    "Applied gate voltage V_G (V)",
    min_value=float(voltage_min),
    max_value=float(voltage_max),
    value=float(min(max(1.5, voltage_min), voltage_max)),
    step=float(voltage_step),
)

try:
    psi_s = mos.numerical_surface_potential(applied_voltage)

    if psi_s < 0.0:
        region = "Accumulation"
        depletion_width = 0.0
        c_dep = None
    elif psi_s < 2.0 * mos.phi_F:
        region = "Depletion"
        depletion_width = mos.depletion_width(psi_s)
        c_dep = mos.depletion_capacitance(psi_s)
    else:
        region = "Inversion"
        depletion_width = mos.Wd_max
        c_dep = mos.Cdep_min

    total_capacitance = mos.numerical_capacitance(
        applied_voltage,
        high_frequency=high_frequency,
    )

except Exception as exc:
    st.error(f"Unable to analyze applied voltage: {exc}")
    st.stop()

result_col1, result_col2, result_col3 = st.columns(3)

with result_col1:
    st.metric(
        "Operating region",
        region,
    )

    st.metric(
        "Surface potential",
        f"{psi_s:.6f} V",
    )

with result_col2:
    st.metric(
        "Depletion width",
        engineering_length(depletion_width),
    )

    if c_dep is None:
        st.metric(
            "Depletion capacitance",
            "Not applicable",
        )
    else:
        st.metric(
            "Depletion capacitance",
            engineering_capacitance(c_dep),
        )

with result_col3:
    st.metric(
        "Oxide capacitance",
        engineering_capacitance(mos.Cox),
    )

    st.metric(
        "Total MOS capacitance",
        engineering_capacitance(total_capacitance),
    )


# ---------------------------------------------------------------------------
# Model information
# ---------------------------------------------------------------------------

with st.expander("Model assumptions"):
    st.markdown(
        """
        **Device**
        - p-type silicon substrate
        - Uniform substrate doping
        - One-dimensional MOS structure
        - SiO₂ gate dielectric
        - Ideal planar capacitor

        **Initial non-ideal effects**
        - Interface traps are not included
        - Series resistance is not included
        - Oxide charge is configurable
        - Boltzmann statistics are used

        **Frequency modes**
        - High Frequency: minority-carrier response is frozen in strong inversion
        - Low Frequency / Quasi-static: equilibrium semiconductor charge response
          is used through inversion

        **Internal units**
        - All physics calculations use SI units.
        """
    )