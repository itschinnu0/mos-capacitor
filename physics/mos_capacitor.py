"""Analytical MOS capacitor electrostatic calculations."""

import math

from .constants import (
    EPSILON_OX,
    EPSILON_SI,
    Q,
    K_B,
    silicon_intrinsic_carrier_concentration,
)
from .parameters import MOSParameters


class MOSCapacitor:
    """Ideal p-type silicon MOS capacitor analytical model."""

    def __init__(self, parameters: MOSParameters) -> None:
        self.parameters = parameters

        self.ni = silicon_intrinsic_carrier_concentration(parameters.temperature)

    @property
    def Cox_per_area(self) -> float:
        """Oxide capacitance per unit area, F/m^2."""
        return EPSILON_OX / self.parameters.tox

    @property
    def Cox(self) -> float:
        """Total oxide capacitance, F."""
        return self.Cox_per_area * self.parameters.area

    @property
    def phi_F(self) -> float:
        """Positive Fermi potential magnitude for p-type silicon, V."""
        return (
            K_B
            * self.parameters.temperature
            / Q
            * math.log(self.parameters.NA / self.ni)
        )

    @property
    def V_FB(self) -> float:
        """Flat-band voltage, V."""
        return self.parameters.phi_ms - self.parameters.q_ox / self.Cox_per_area

    @property
    def V_T(self) -> float:
        """Threshold voltage for the locked p-type convention, V."""
        return (
            self.V_FB
            + 2.0 * self.phi_F
            + math.sqrt(4.0 * Q * EPSILON_SI * self.parameters.NA * self.phi_F)
            / self.Cox_per_area
        )

    @property
    def Wd_max(self) -> float:
        """Maximum depletion width at strong inversion, m."""
        return math.sqrt(4.0 * EPSILON_SI * self.phi_F / (Q * self.parameters.NA))

    @property
    def Cdep_min(self) -> float:
        """Minimum depletion capacitance, F."""
        return EPSILON_SI * self.parameters.area / self.Wd_max

    @property
    def Cmin(self) -> float:
        """Minimum high-frequency MOS capacitance, F."""
        return self.Cox * self.Cdep_min / (self.Cox + self.Cdep_min)

    def depletion_width(self, psi_s: float) -> float:
        """Return depletion width for psi_s >= 0 under Level 1 approximation."""
        if psi_s < 0.0:
            raise ValueError(
                "The depletion-width equation is not valid in accumulation."
            )

        return math.sqrt(2.0 * EPSILON_SI * psi_s / (Q * self.parameters.NA))

    def depletion_capacitance(self, psi_s: float) -> float:
        """Return depletion capacitance for psi_s > 0, in F."""
        width = self.depletion_width(psi_s)

        if width == 0.0:
            return math.inf

        return EPSILON_SI * self.parameters.area / width
