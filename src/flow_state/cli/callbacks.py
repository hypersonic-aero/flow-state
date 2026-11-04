"""Shared callbacks for the flow-state command-line interface."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import logging

import typer

from flow_state import __version__


# --------------------------------------------------
# verbose callback
# --------------------------------------------------
def verbose_callback(value: bool) -> None:
    """Configure console logging; --verbose adds debug output from this tool.

    Other packages, ours and third-party, stay at the default level, so
    --verbose shows this tool's debug messages only.
    """

    # default console logging for every logger
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    # debug output from this tool only; the packages it calls keep their levels
    if value:
        logging.getLogger("flow_state").setLevel(logging.DEBUG)


# --------------------------------------------------
# version callback
# --------------------------------------------------
def version_callback(value: bool) -> None:
    """Print the installed package version and exit."""

    # print the version and stop before any command runs
    if value:
        typer.echo(f"flow-state version {__version__}")
        raise typer.Exit()
