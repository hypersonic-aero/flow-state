"""Command-line interface for flow-state."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from flow_state.cli.app import app

# --------------------------------------------------
# cli public api
# --------------------------------------------------

# Preserve the existing ``flow_state.cli:cli`` console entry point.
cli = app

__all__ = ["app", "cli"]
