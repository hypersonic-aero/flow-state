"""Compute and write a flow state from CLI or TOML inputs."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from flow_state.cli.constants import DEFAULT_CONFIG, DEFAULT_OUTPUT
from flow_state.io import read_config, write_flow_conditions_dat, write_json
from flow_state.solvers import solve

# --------------------------------------------------
# set up logger
# --------------------------------------------------
logger = logging.getLogger(__name__)


# --------------------------------------------------
# subcommand: run
# --------------------------------------------------
def cmd_run(
    mach: Annotated[float | None, typer.Option("--mach", "-m", help="Mach number")] = None,
    pres_stag: Annotated[
        float | None,
        typer.Option("--pres-stag", help="Stagnation pressure (default: Pa)"),
    ] = None,
    pres_stag_unit: Annotated[
        str | None,
        typer.Option("--pres-stag-unit", help="Stagnation pressure unit (Pa, psi, atm, bar)"),
    ] = None,
    temp_stag: Annotated[
        float | None,
        typer.Option("--temp-stag", help="Stagnation temperature (K)"),
    ] = None,
    altitude: Annotated[
        float | None,
        typer.Option("--altitude", "-a", help="Altitude (default: m)"),
    ] = None,
    altitude_unit: Annotated[
        str | None,
        typer.Option("--altitude-unit", help="Altitude unit (m, ft, km)"),
    ] = None,
    pres: Annotated[
        float | None,
        typer.Option("--pres", help="Static pressure (default: Pa)"),
    ] = None,
    pres_unit: Annotated[
        str | None,
        typer.Option("--pres-unit", help="Static pressure unit (Pa, psi, atm, bar)"),
    ] = None,
    temp: Annotated[
        float | None,
        typer.Option("--temp", help="Static temperature (default: K)"),
    ] = None,
    temp_unit: Annotated[
        str | None,
        typer.Option("--temp-unit", help="Static temperature unit (K, C, F, R)"),
    ] = None,
    re1: Annotated[
        float | None,
        typer.Option("--re1", help="Unit Reynolds number [1/m]"),
    ] = None,
    gas: Annotated[str | None, typer.Option("--gas", help="Gas type (air, n2)")] = None,
    atm: Annotated[
        str | None,
        typer.Option("--atm", help="Atmosphere model (ussa76, cira86)"),
    ] = None,
    lref: Annotated[
        float | None,
        typer.Option("--lref", help="Reference length (m)"),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Input config file (TOML). Ignored if direct options provided.",
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output file (JSON). Defaults to flow_conditions.json in the current directory.",
        ),
    ] = Path(DEFAULT_OUTPUT),
    dat: Annotated[
        bool,
        typer.Option("--dat", help="Write legacy .dat file (flow_conditions.dat)."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress summary output."),
    ] = False,
) -> None:
    """Compute a flow state from direct options or a configuration file."""

    # check: direct options on the command line take precedence over a config file
    has_direct_options = any([mach, pres_stag, temp_stag, altitude, pres, temp, re1])

    # build the solver inputs from the direct options given (units as (value, unit) tuples)
    if has_direct_options:
        solve_kwargs: dict[str, object] = {}
        if mach is not None:
            solve_kwargs["mach"] = mach
        if pres_stag is not None:
            solve_kwargs["pres_stag"] = (pres_stag, pres_stag_unit) if pres_stag_unit else pres_stag
        if temp_stag is not None:
            solve_kwargs["temp_stag"] = temp_stag
        if altitude is not None:
            solve_kwargs["altitude"] = (altitude, altitude_unit) if altitude_unit else altitude
        if pres is not None:
            solve_kwargs["pres"] = (pres, pres_unit) if pres_unit else pres
        if temp is not None:
            solve_kwargs["temp"] = (temp, temp_unit) if temp_unit else temp
        if re1 is not None:
            solve_kwargs["re1"] = re1
        if gas is not None:
            solve_kwargs["gas"] = gas
        if atm is not None:
            solve_kwargs["atm"] = atm
        if lref is not None:
            solve_kwargs["lref"] = lref
    else:
        # read the solver inputs from the config file (default: flow_config.toml)
        config_path = config if config else Path(DEFAULT_CONFIG)

        # check: the config exists, otherwise point to `flow-state init`
        if not config_path.exists():
            typer.echo(f"Error: {config_path} not found.", err=True)
            typer.echo(
                "Provide direct options (--mach, etc.) or run 'flow-state init' to create a config.",
                err=True,
            )
            raise typer.Exit(1)

        # read and parse the config
        try:
            solve_kwargs = read_config(config_path)
        except (OSError, ValueError) as error:
            typer.echo(f"Error parsing {config_path}: {error}", err=True)
            raise typer.Exit(1) from error

    # compute the flow state
    try:
        state = solve(**solve_kwargs)
    except (ValueError, TypeError) as error:
        typer.echo(f"Error computing flow state: {error}", err=True)
        raise typer.Exit(1) from error

    # debug output for devs
    if state.provenance:
        for key, value in state.provenance.items():
            logger.debug("%s: %s", key, value)
    logger.debug("gas_model:       %s", state.gas_model)
    logger.debug("transport_model: %s", state.transport_model)

    # write the flow-state JSON
    write_json(state, output)
    typer.echo(f"Wrote {output}")

    # write the legacy flow_conditions.dat when asked for
    if dat:
        dat_path = Path("flow_conditions.dat")
        write_flow_conditions_dat(state, dat_path)
        typer.echo(f"Wrote {dat_path}")

    # print the summary unless --quiet
    if not quiet:
        typer.echo("")
        typer.echo(str(state))
