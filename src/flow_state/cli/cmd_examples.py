"""List bundled example cases, or copy one into a new folder."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_state.io.examples import copy_example, list_examples


# --------------------------------------------------
# subcommand: examples
# --------------------------------------------------
def cmd_examples(
    name: Annotated[
        str | None,
        typer.Argument(help="Example to copy into ./<name>/. Omit to list the examples."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite an existing ./<name>/ folder."),
    ] = False,
) -> None:
    """List the bundled examples, or copy one into a new folder to run."""

    # list: name and description of every example
    examples = list_examples()
    if name is None:
        width = max(len(example_name) for example_name in [*examples, "<name>"])
        typer.echo("")
        typer.echo(f"  {'<name>':<{width}}  description")
        typer.echo(f"  {'-'*width}  {'-'*11}")
        for example_name, description in examples.items():
            typer.echo(f"  {example_name:<{width}}  {description}")
        typer.echo("")
        typer.echo("command sequence:")
        typer.echo("  - check out the example")
        typer.echo("     flow-state examples <name>")
        typer.echo("  - change into its folder")
        typer.echo("     cd <name>")
        typer.echo("  - run the example")
        typer.echo("     flow-state run")
        typer.echo("")
        return

    # copy the example into ./<name>/
    try:
        written = copy_example(name, Path(name), force=force)
    except KeyError:
        known = ", ".join(examples)
        typer.echo(f"error: unknown example {name!r}; available: {known}", err=True)
        raise typer.Exit(1) from None
    except FileExistsError as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None

    # report the files and the next step
    for path in written:
        typer.echo(f"wrote {path}")
    typer.echo(f"then: cd {name} && flow-state run")
