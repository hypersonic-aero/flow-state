"""
Validated model of the flow-state TOML configuration.

The model checks the config at the input boundary: unknown keys (typos such
as ``lrefs``), wrong types, unknown units, unknown gas or atmosphere names and
out-of-range values fail with a message that names the key. Which inputs may
be combined (e.g. mach + pres_stag + temp_stag) is left to ``solve()``, which
picks the solver from them.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from flow_state.atmosphere.registry import MODELS as ATMOSPHERE_MODELS
from flow_state.gas.registry import get_gas
from flow_state.units import (
    convert_length,
    convert_pressure,
    convert_temperature,
    convert_velocity,
)

# --------------------------------------------------
# value types
# --------------------------------------------------

# a dimensional value: a number in SI units, or [value, "unit"] in the TOML
ValueWithUnit = float | tuple[float, str]


# --------------------------------------------------
# helper: split a dimensional value
# --------------------------------------------------
def _split_value(value: ValueWithUnit) -> tuple[float, str | None]:
    """Split a dimensional value into its number and unit (None for SI)."""

    # [value, "unit"] pairs arrive as tuples, plain numbers are SI
    if isinstance(value, tuple):
        number, unit = value
        return number, unit

    return value, None


# --------------------------------------------------
# [atmosphere] table
# --------------------------------------------------
class AtmosphereConfig(BaseModel):
    """The [atmosphere] table: an atmosphere model and its options.

    Attributes:
        model: Atmosphere model name.
        latitude: Latitude [deg] (CIRA-86 only).
        month: Month of the year, 1-12 (CIRA-86 only).
    """

    model_config = ConfigDict(extra="forbid")

    model: Literal["ussa76", "cira86"] = "ussa76"
    latitude: float = Field(default=45.0, ge=-90.0, le=90.0)
    month: int = Field(default=1, ge=1, le=12)


# --------------------------------------------------
# flow-state configuration
# --------------------------------------------------
class FlowConfig(BaseModel):
    """The flow-state configuration file (flow_config.toml).

    Dimensional values are a number in SI units or a ``[value, "unit"]`` pair.

    Attributes:
        mach: Mach number.
        pres: Static pressure.
        temp: Static temperature.
        uvel: Velocity.
        pres_stag: Stagnation pressure.
        temp_stag: Stagnation temperature.
        altitude: Geometric altitude.
        re1: Unit Reynolds number [1/m].
        lref: Reference length for the turbulence scales.
        pr: Prandtl number.
        gas: Gas name (air, nitrogen / n2).
        notes: Free-text notes stored with the flow state.
        atm: Atmosphere model name (short form of the [atmosphere] table).
        atmosphere: Atmosphere model with options.
    """

    model_config = ConfigDict(extra="forbid")

    # flow inputs (which combination is valid is decided by solve())
    mach: float | None = Field(default=None, gt=0.0)
    pres: ValueWithUnit | None = None
    temp: ValueWithUnit | None = None
    uvel: ValueWithUnit | None = None
    pres_stag: ValueWithUnit | None = None
    temp_stag: ValueWithUnit | None = None
    altitude: ValueWithUnit | None = None
    re1: float | None = Field(default=None, gt=0.0)

    # options
    lref: ValueWithUnit | None = None
    pr: float | None = Field(default=None, gt=0.0)
    gas: str | None = None
    notes: str | None = None

    # atmosphere: a model name, or a table with options
    atm: str | None = None
    atmosphere: AtmosphereConfig | None = None

    # --------------------------------------------------
    # field checks
    # --------------------------------------------------
    @field_validator("pres", "pres_stag")
    @classmethod
    def _check_pressure(cls, value: ValueWithUnit | None) -> ValueWithUnit | None:
        """Pressures: a known unit and a positive value."""

        # nothing to check for an absent value
        if value is None:
            return value

        # convert to Pa (raises for an unknown unit), then check the sign
        number, unit = _split_value(value)
        pres_pa = convert_pressure(number, unit) if unit else number
        if pres_pa <= 0.0:
            raise ValueError(f"must be positive, got {value}")

        return value

    @field_validator("temp", "temp_stag")
    @classmethod
    def _check_temperature(cls, value: ValueWithUnit | None) -> ValueWithUnit | None:
        """Temperatures: a known unit and above absolute zero."""

        # nothing to check for an absent value
        if value is None:
            return value

        # convert to K (raises for an unknown unit), then check absolute zero
        number, unit = _split_value(value)
        temp_k = convert_temperature(number, unit) if unit else number
        if temp_k <= 0.0:
            raise ValueError(f"must be above absolute zero, got {value}")

        return value

    @field_validator("altitude", "lref")
    @classmethod
    def _check_length(cls, value: ValueWithUnit | None) -> ValueWithUnit | None:
        """Lengths: a known unit."""

        # convert to m, which raises for an unknown unit
        if value is not None:
            number, unit = _split_value(value)
            if unit:
                convert_length(number, unit)

        return value

    @field_validator("uvel")
    @classmethod
    def _check_velocity(cls, value: ValueWithUnit | None) -> ValueWithUnit | None:
        """Velocities: a known unit."""

        # convert to m/s, which raises for an unknown unit
        if value is not None:
            number, unit = _split_value(value)
            if unit:
                convert_velocity(number, unit)

        return value

    @field_validator("gas")
    @classmethod
    def _check_gas(cls, value: str | None) -> str | None:
        """Gas: a name the gas registry knows."""

        # look the name up (raises ValueError listing the known gases)
        if value is not None:
            get_gas(value)

        return value

    @field_validator("atm")
    @classmethod
    def _check_atmosphere_name(cls, value: str | None) -> str | None:
        """atm: a name the atmosphere registry knows."""

        # check against the registered models
        if value is not None and value.lower() not in ATMOSPHERE_MODELS:
            known = ", ".join(sorted(ATMOSPHERE_MODELS))
            raise ValueError(f"unknown atmosphere model {value!r}; known: {known}")

        return value

    # --------------------------------------------------
    # cross-field checks
    # --------------------------------------------------
    @model_validator(mode="after")
    def _check_one_atmosphere(self) -> FlowConfig:
        """The atmosphere is given once: as atm or as an [atmosphere] table."""

        # check: not both forms at once
        if self.atm is not None and self.atmosphere is not None:
            raise ValueError("give the atmosphere as atm or as an [atmosphere] table, not both")

        return self

    # --------------------------------------------------
    # conversion for solve()
    # --------------------------------------------------
    def solve_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for ``solve()``, with only the keys that were given.

        Returns:
            Dict of solve() inputs; [atmosphere] tables become a model name or
            a configured CIRA86 instance.
        """

        # keys that pass straight through to solve()
        kwargs = self.model_dump(exclude_none=True, exclude={"atm", "atmosphere"})

        # atmosphere: a plain name, or a configured model from the table
        if self.atm is not None:
            kwargs["atm"] = self.atm
        elif self.atmosphere is not None:
            if self.atmosphere.model == "cira86":
                from flow_state.atmosphere import CIRA86

                kwargs["atm"] = CIRA86(
                    latitude=self.atmosphere.latitude,
                    month=self.atmosphere.month,
                )
            else:
                kwargs["atm"] = self.atmosphere.model

        return kwargs
