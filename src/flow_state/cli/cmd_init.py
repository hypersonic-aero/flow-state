"""Generate a starter flow-state configuration."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_state.cli.constants import DEFAULT_CONFIG
from flow_state.cli.templates import CONFIG_TEMPLATE


# --------------------------------------------------
# subcommand: init
# --------------------------------------------------
def cmd_init(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output config file path"),
    ] = Path(DEFAULT_CONFIG),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing file"),
    ] = False,
) -> None:
    """Generate a documented template configuration file."""

    # check: don't overwrite an existing configuration unless asked to
    if output.exists() and not force:
        typer.echo(f"Error: {output} already exists. Use --force to overwrite", err=True)
        raise typer.Exit(1)

    # write the template and tell the user the next step
    output.write_text(CONFIG_TEMPLATE)
    typer.echo(f"Created {output}")
    typer.echo("Edit the file, then run: flow-state run")
