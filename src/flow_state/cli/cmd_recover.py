"""Recover and write flow conditions from HDF5 metadata."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_state.cli.constants import DEFAULT_OUTPUT
from flow_state.io import write_json
from flow_state.recover import recover_from_hdf5


# --------------------------------------------------
# subcommand: recover
# --------------------------------------------------
def cmd_recover(
    input_file: Annotated[
        Path,
        typer.Argument(help="HDF5 base-flow file containing flow-condition attributes."),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output JSON file.",
        ),
    ] = Path(DEFAULT_OUTPUT),
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress summary output."),
    ] = False,
) -> None:
    """Recover flow_conditions.json from HDF5 root attributes."""

    # read: rebuild the flow state from the HDF5 root attributes
    try:
        state = recover_from_hdf5(input_file)
    except (FileNotFoundError, OSError, TypeError, ValueError) as error:
        typer.echo(f"Error recovering flow state: {error}", err=True)
        raise typer.Exit(1) from error

    # write the flow-state JSON
    write_json(state, output)
    typer.echo(f"Wrote {output}")

    # print the summary unless --quiet
    if not quiet:
        typer.echo("")
        typer.echo(str(state))
