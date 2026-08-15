"""Physical constants and documented silicon material parameters."""

# Fundamental physical constants
Q = 1.602176634e-19              # Elementary charge, C
K_B = 1.380649e-23               # Boltzmann constant, J/K
EPSILON_0 = 8.8541878128e-12     # Vacuum permittivity, F/m

# Useful derived constant
K_B_EV = K_B / Q                 # Boltzmann constant, eV/K

# Relative permittivities
EPSILON_SI_R = 11.7
EPSILON_OX_R = 3.9

# Absolute permittivities
EPSILON_SI = EPSILON_SI_R * EPSILON_0
EPSILON_OX = EPSILON_OX_R * EPSILON_0

# Unit conversions
CM3_TO_M3 = 1.0e6
NM_TO_M = 1.0e-9
UM2_TO_M2 = 1.0e-12

# ---------------------------------------------------------------------------
# Silicon material parameters
#
# Source specified by the implementation plan:
# S. M. Sze and Kwok K. Ng, Physics of Semiconductor Devices, 3rd ed.
# ---------------------------------------------------------------------------

SILICON_EG0_EV = 1.170
SILICON_VARSHNI_ALPHA_EV_PER_K = 4.73e-4
SILICON_VARSHNI_BETA_K = 636.0

SILICON_NC_300_CM3 = 2.8e19
SILICON_NV_300_CM3 = 1.04e19

# Convert documented cm^-3 values to mandatory internal SI units.
SILICON_NC_300_M3 = SILICON_NC_300_CM3 * CM3_TO_M3
SILICON_NV_300_M3 = SILICON_NV_300_CM3 * CM3_TO_M3


def silicon_bandgap(T_K: float) -> float:
    """Return silicon bandgap in eV using the Varshni relation."""
    if T_K <= 0.0:
        raise ValueError("Temperature must be greater than 0 K.")

    return (
        SILICON_EG0_EV
        - (
            SILICON_VARSHNI_ALPHA_EV_PER_K
            * T_K**2
            / (T_K + SILICON_VARSHNI_BETA_K)
        )
    )


def silicon_effective_density_of_states(
    T_K: float,
) -> tuple[float, float]:
    """Return (Nc, Nv) in m^-3 at temperature T."""
    if T_K <= 0.0:
        raise ValueError("Temperature must be greater than 0 K.")

    temperature_factor = (T_K / 300.0) ** 1.5

    nc = SILICON_NC_300_M3 * temperature_factor
    nv = SILICON_NV_300_M3 * temperature_factor

    return nc, nv


def silicon_intrinsic_carrier_concentration(T_K: float) -> float:
    """Return silicon intrinsic carrier concentration in m^-3."""
    if T_K <= 0.0:
        raise ValueError("Temperature must be greater than 0 K.")

    import math
    
    nc, nv = silicon_effective_density_of_states(T_K)
    eg_ev = silicon_bandgap(T_K)

    return math.sqrt(nc * nv) * math.exp(
        -eg_ev / (2.0 * K_B_EV * T_K)
    )