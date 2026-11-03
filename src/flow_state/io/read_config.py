"""
Read TOML configuration file for flow_state CLI.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from flow_state.io.flow_config import FlowConfig

# --------------------------------------------------
# read config file
#
# reads a TOML config file and returns a dict of kwargs for solve()
# TOML arrays [value, "unit"] are converted to tuples (value, "unit")
# --------------------------------------------------


def read_config(path: Path) -> dict[str, Any]:
    """
    Read a TOML config file and return kwargs for solve().

    The file is validated against FlowConfig: unknown keys, wrong types,
    unknown units and out-of-range values raise a ValueError naming the key.

    Args:
        path: path to the TOML config file

    Returns:
        dict of keyword arguments for solve()

    Raises:
        FileNotFoundError: if config file does not exist
        tomllib.TOMLDecodeError: if config file is invalid TOML
        ValueError: if the config doesn't validate
    """
    with open(path, "rb") as f:
        cfg = tomllib.load(f)

    # validate the config (pydantic's ValidationError reworded as one line per key)
    try:
        flow_config = FlowConfig.model_validate(cfg)
    except ValidationError as error:
        raise ValueError(_format_validation_error(error)) from None

    # build kwargs for solve()
    kwargs = flow_config.solve_kwargs()

    return kwargs


# --------------------------------------------------
# helper: readable validation errors
# --------------------------------------------------
def _format_validation_error(error: ValidationError) -> str:
    """One ``key: message`` line per problem, without pydantic's URLs."""

    # collect a line per error, located by its (dotted) key
    lines = ["invalid config:"]
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        message = item["msg"].removeprefix("Value error, ")
        lines.append(f"  {location}: {message}")

    return "\n".join(lines)
