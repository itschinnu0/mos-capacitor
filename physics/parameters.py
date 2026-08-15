"""Validated MOS capacitor device/model parameters."""

from dataclasses import dataclass

from .constants import CM3_TO_M3, NM_TO_M, UM2_TO_M2


@dataclass(frozen=True)
class MOSParameters:
    """MOS capacitor parameters stored internally in SI units."""

    # Substrate acceptor concentration, m^-3
    NA: float

    # Oxide thickness, m
    tox: float

    # Gate area, m^2
    area: float

    # Temperature, K
    temperature: float

    # Metal-semiconductor work-function difference, V
    phi_ms: float

    # Fixed oxide charge density, C/m^2
    q_ox: float = 0.0

    def __post_init__(self) -> None:
        if self.NA <= 0.0:
            raise ValueError("N_A must be greater than 0.")

        if self.tox <= 0.0:
            raise ValueError("Oxide thickness must be greater than 0.")

        if self.area <= 0.0:
            raise ValueError("Gate area must be greater than 0.")

        if self.temperature <= 0.0:
            raise ValueError("Temperature must be greater than 0 K.")

    @classmethod
    def from_gui_units(
        cls,
        NA_cm3: float,
        tox_nm: float,
        area_um2: float,
        temperature_K: float,
        phi_ms_V: float,
        q_ox_C_m2: float = 0.0,
    ) -> "MOSParameters":
        """Create parameters from the project's GUI units."""
        return cls(
            NA=NA_cm3 * CM3_TO_M3,
            tox=tox_nm * NM_TO_M,
            area=area_um2 * UM2_TO_M2,
            temperature=temperature_K,
            phi_ms=phi_ms_V,
            q_ox=q_ox_C_m2,
        )

    @property
    def NA_cm3(self) -> float:
        """Return substrate doping in cm^-3."""
        return self.NA / CM3_TO_M3

    @property
    def tox_nm(self) -> float:
        """Return oxide thickness in nm."""
        return self.tox / NM_TO_M

    @property
    def area_um2(self) -> float:
        """Return gate area in um^2."""
        return self.area / UM2_TO_M2
