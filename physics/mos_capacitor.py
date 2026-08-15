"""Analytical MOS capacitor electrostatic calculations."""

import math
import numpy as np
from dataclasses import dataclass

from .constants import (
    EPSILON_OX,
    EPSILON_SI,
    Q,
    K_B,
    silicon_intrinsic_carrier_concentration,
)
from .parameters import MOSParameters
from .solver import SurfacePotentialSolver


@dataclass(frozen=True)
class Level1Point:
    """Single operating point from the Level 1 analytical model."""

    voltage: float
    surface_potential: float
    region: str
    depletion_width: float
    depletion_capacitance: float
    capacitance: float


class MOSCapacitor:
    """Ideal p-type silicon MOS capacitor analytical model."""

    def __init__(self, parameters: MOSParameters) -> None:
        self.parameters = parameters

        self.ni = silicon_intrinsic_carrier_concentration(parameters.temperature)

        self.solver = SurfacePotentialSolver(
            parameters,
            self.ni,
        )

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

    def level1_surface_potential(self, voltage: float) -> float:
        """Solve the Level 1 depletion approximation for surface potential."""
        voltage_bias = voltage - self.V_FB

        if voltage_bias < 0.0:
            return voltage_bias

        k = math.sqrt(2.0 * Q * EPSILON_SI * self.parameters.NA) / self.Cox_per_area

        x = (-k + math.sqrt(k**2 + 4.0 * voltage_bias)) / 2.0

        return x**2

    def level1_point(self, voltage: float) -> Level1Point:
        """Calculate one operating point using the Level 1 model."""
        voltage_bias = voltage - self.V_FB

        # Accumulation
        if voltage_bias < 0.0:
            return Level1Point(
                voltage=voltage,
                surface_potential=voltage_bias,
                region="accumulation",
                depletion_width=0.0,
                depletion_capacitance=math.inf,
                capacitance=self.Cox,
            )

        # Depletion/inversion surface potential
        psi_s = self.level1_surface_potential(voltage)

        # Strong inversion
        if psi_s >= 2.0 * self.phi_F:
            return Level1Point(
                voltage=voltage,
                surface_potential=psi_s,
                region="inversion",
                depletion_width=self.Wd_max,
                depletion_capacitance=self.Cdep_min,
                capacitance=self.Cmin,
            )

        # Depletion
        width = self.depletion_width(psi_s)

        if width == 0.0:
            cdep = math.inf
            capacitance = self.Cox
        else:
            cdep = self.depletion_capacitance(psi_s)
            capacitance = self.Cox * cdep / (self.Cox + cdep)

        return Level1Point(
            voltage=voltage,
            surface_potential=psi_s,
            region="depletion",
            depletion_width=width,
            depletion_capacitance=cdep,
            capacitance=capacitance,
        )

    def generate_level1_cv(
        self,
        voltage_min: float,
        voltage_max: float,
        voltage_step: float,
    ) -> list[Level1Point]:
        """Generate Level 1 C-V data across the requested voltage range."""
        if voltage_max <= voltage_min:
            raise ValueError("Voltage maximum must be greater than voltage minimum.")

        if voltage_step <= 0.0:
            raise ValueError("Voltage step must be greater than 0.")

        voltages = np.arange(
            voltage_min,
            voltage_max + voltage_step,
            voltage_step,
        )

        return [
            self.level1_point(float(voltage))
            for voltage in voltages
            if voltage <= voltage_max
        ]

    def numerical_surface_potential(
        self,
        voltage: float,
    ) -> float:
        """Solve Level 2 surface potential for a gate voltage."""
        result = self.solver.solve(
            voltage=voltage,
            v_fb=self.V_FB,
            c_ox_per_area=self.Cox_per_area,
        )

        return result.surface_potential

    def numerical_semiconductor_capacitance_per_area(
        self,
        psi_s: float,
        high_frequency: bool = True,
    ) -> float:
        """Return Level 2 semiconductor capacitance per unit area."""
        if high_frequency and psi_s >= 2.0 * self.phi_F:
            return EPSILON_SI / self.Wd_max

        return self.solver.semiconductor_capacitance_per_area(psi_s)

    def numerical_capacitance(
        self,
        voltage: float,
        high_frequency: bool = True,
    ) -> float:
        """Return total Level 2 MOS capacitance."""
        psi_s = self.numerical_surface_potential(voltage)

        c_s = self.numerical_semiconductor_capacitance_per_area(
            psi_s,
            high_frequency=high_frequency,
        )

        return self.parameters.area * (
            self.Cox_per_area * c_s / (self.Cox_per_area + c_s)
        )
