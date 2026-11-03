"""Shared callbacks for the flow-state command-line interface."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import logging

import typer

from flow_state import __version__

# --------------------------------------------------
# module constants
# --------------------------------------------------

# loggers that --verbose switches to debug: this tool and the uahypersonics
# packages it calls
DEBUG_LOGGERS = ("flow_state",)


# --------------------------------------------------
# verbose callback
# --------------------------------------------------
def verbose_callback(value: bool) -> None:
    """Configure console logging; --verbose adds debug output from our own packages.

    Third-party libraries stay at the default level, so --verbose shows our
    debug messages without theirs.
    """

    # default console logging for every logger
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    # debug output from this tool and the uahypersonics packages it calls
    if value:
        for logger_name in DEBUG_LOGGERS:
            logging.getLogger(logger_name).setLevel(logging.DEBUG)


# --------------------------------------------------
# version callback
# --------------------------------------------------
def version_callback(value: bool) -> None:
    """Print the installed package version and exit."""

    # print the version and stop before any command runs
    if value:
        typer.echo(f"flow-state version {__version__}")
        raise typer.Exit()
