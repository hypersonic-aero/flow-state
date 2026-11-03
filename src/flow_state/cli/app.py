"""Typer application for the flow-state command-line interface."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from typing import Annotated

import typer

from flow_state.cli.callbacks import verbose_callback, version_callback
from flow_state.cli.cmd_examples import cmd_examples
from flow_state.cli.cmd_init import cmd_init
from flow_state.cli.cmd_recover import cmd_recover
from flow_state.cli.cmd_run import cmd_run

# --------------------------------------------------
# app
# --------------------------------------------------
app = typer.Typer(
    name="flow-state",
    help="Compute flow states.",
    add_completion=False,
    no_args_is_help=True,
)


# --------------------------------------------------
# callback for --version and --verbose options
# version_callback and verbose_callback are defined in callbacks.py
# --------------------------------------------------
@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose (debug) output.",
            callback=verbose_callback,
        ),
    ] = False,
) -> None:
    """Compute flow states from freestream, stagnation, or atmospheric inputs."""

    # both options act through their callbacks; nothing left to do here
    del version, verbose


# --------------------------------------------------
# register subcommands
# notes:
# - the order at which they are registered is the order in which they display
# --------------------------------------------------
app.command(name="init")(cmd_init)
app.command(name="run")(cmd_run)
app.command(name="recover")(cmd_recover)
app.command(name="examples")(cmd_examples)

# --------------------------------------------------
# main entry point
# --------------------------------------------------
if __name__ == "__main__":
    app()
