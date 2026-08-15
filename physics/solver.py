"""Numerical surface-potential solver for the MOS capacitor model."""

import math
from dataclasses import dataclass

from scipy.optimize import brentq

from .constants import EPSILON_SI, K_B, Q
from .parameters import MOSParameters


@dataclass(frozen=True)
class SurfacePotentialResult:
    """Result of a numerical surface-potential solution."""

    surface_potential: float
    residual: float
    iterations_bracket: tuple[float, float]


class SurfacePotentialSolver:
    """Solve the Level 2 MOS surface-potential equation."""

    def __init__(self, parameters: MOSParameters, ni: float) -> None:
        self.parameters = parameters
        self.ni = ni

        self._thermal_voltage = K_B * parameters.temperature / Q

        self._charge_prefactor = math.sqrt(
            2.0 * EPSILON_SI * parameters.NA * K_B * parameters.temperature
        )

        self._intrinsic_ratio_squared = (ni / parameters.NA) ** 2

    @property
    def thermal_voltage(self) -> float:
        """Return kT/q in volts."""
        return self._thermal_voltage

    def normalized_surface_potential(
        self,
        psi_s: float,
    ) -> float:
        """Return u_s = q*psi_s/(kT)."""
        return psi_s / self._thermal_voltage

    def _stable_exp(self, value: float) -> float:
        """Evaluate exp(value) without allowing overflow."""
        # Double precision exp overflows at approximately 709.
        if value > 700.0:
            return math.exp(700.0)

        if value < -700.0:
            return 0.0

        return math.exp(value)

    def charge_function(self, psi_s: float) -> float:
        """Return the dimensionless F(u_s) appearing in Q_s."""
        u_s = self.normalized_surface_potential(psi_s)

        exp_negative = self._stable_exp(-u_s)
        exp_positive = self._stable_exp(u_s)

        return (
            exp_negative
            + u_s
            - 1.0
            + self._intrinsic_ratio_squared * (exp_positive - u_s - 1.0)
        )

    def semiconductor_charge(
        self,
        psi_s: float,
    ) -> float:
        """Return signed semiconductor charge density Q_s in C/m^2."""
        if psi_s == 0.0:
            return 0.0

        f_value = self.charge_function(psi_s)

        if f_value < 0.0:
            # Numerical roundoff can produce a tiny negative value
            # extremely close to flatband.
            if f_value > -1.0e-14:
                f_value = 0.0
            else:
                raise ValueError("Non-physical negative charge-function value.")

        return -math.copysign(1.0, psi_s) * self._charge_prefactor * math.sqrt(f_value)

    def charge_function_derivative(
        self,
        psi_s: float,
    ) -> float:
        """Return dF/dpsi_s analytically."""
        u_s = self.normalized_surface_potential(psi_s)

        exp_negative = self._stable_exp(-u_s)
        exp_positive = self._stable_exp(u_s)

        dF_du = (
            -exp_negative + 1.0 + self._intrinsic_ratio_squared * (exp_positive - 1.0)
        )

        return dF_du / self._thermal_voltage

    def d_charge_d_psi(
        self,
        psi_s: float,
    ) -> float:
        """Return analytical dQ_s/dpsi_s."""
        # The closed-form derivative becomes numerically ill-conditioned
        # extremely close to flatband because F(u_s) approaches zero.
        # Use the analytical limiting derivative in that neighborhood.
        if abs(psi_s) <= 1.0e-12:
            ratio = self.ni / self.parameters.NA

            f_second = 1.0 + ratio**2

            return -self._charge_prefactor * math.sqrt(
                f_second / self._thermal_voltage**2
            )

        f_value = self.charge_function(psi_s)

        if f_value <= 0.0:
            raise ValueError("Charge-function derivative undefined for non-positive F.")

        sign = math.copysign(1.0, psi_s)

        return (
            -sign
            * self._charge_prefactor
            * self.charge_function_derivative(psi_s)
            / (2.0 * math.sqrt(f_value))
        )

    def semiconductor_capacitance_per_area(
        self,
        psi_s: float,
    ) -> float:
        """Return positive semiconductor differential capacitance F/m^2."""
        capacitance = -self.d_charge_d_psi(psi_s)

        if not math.isfinite(capacitance) or capacitance <= 0.0:
            raise ValueError(
                "Calculated semiconductor capacitance is not positive " "and finite."
            )

        return capacitance

    def voltage_residual(
        self,
        psi_s: float,
        voltage: float,
        v_fb: float,
        c_ox_per_area: float,
    ) -> float:
        """Return residual of Vg = VFB + psi_s - Qs/Cox'."""
        q_s = self.semiconductor_charge(psi_s)

        return v_fb + psi_s - q_s / c_ox_per_area - voltage

    def solve(
        self,
        voltage: float,
        v_fb: float,
        c_ox_per_area: float,
    ) -> SurfacePotentialResult:
        """Solve for surface potential using a bounded Brent root solver."""

        thermal_voltage = self._thermal_voltage

        # Start with a physically broad interval in normalized
        # surface-potential units.
        lower = -40.0 * thermal_voltage
        upper = 40.0 * thermal_voltage

        def residual(psi_s: float) -> float:
            value = self.voltage_residual(
                psi_s,
                voltage,
                v_fb,
                c_ox_per_area,
            )

            if not math.isfinite(value):
                raise ValueError("Non-finite MOS voltage residual encountered.")

            return value

        f_lower = residual(lower)
        f_upper = residual(upper)

        # Expand the bracket only when necessary.
        expansion_count = 0

        while f_lower * f_upper > 0.0 and expansion_count < 10:
            lower *= 1.5
            upper *= 1.5

            f_lower = residual(lower)
            f_upper = residual(upper)

            expansion_count += 1

        if f_lower * f_upper > 0.0:
            raise RuntimeError("Unable to establish a valid surface-potential bracket.")

        root = brentq(
            residual,
            lower,
            upper,
            xtol=1.0e-12,
            rtol=1.0e-12,
            maxiter=200,
        )

        final_residual = residual(root)

        if abs(final_residual) > 1.0e-9:
            raise RuntimeError(
                "Surface-potential solver converged with an excessive "
                f"residual: {final_residual}"
            )

        return SurfacePotentialResult(
            surface_potential=root,
            residual=final_residual,
            iterations_bracket=(lower, upper),
        )
