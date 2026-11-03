"""Bundled example cases for the flow-state CLI.

Each example is a folder under ``flow_state/examples/`` holding the files of
one case (here a ``flow_config.toml``). The folder name is the example's name
and the first text line of its config is the description, so the folders are
the registry: adding an example means adding a folder.

Adding a new example
--------------------
1. Add ``src/flow_state/examples/<name>/flow_config.toml``.
2. Start the file with a comment that names the case (shown in the listing).
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

# --------------------------------------------------
# module constants
# --------------------------------------------------

# config file every example holds (run's default config name)
EXAMPLE_CONFIG = "flow_config.toml"


# --------------------------------------------------
# helpers
# --------------------------------------------------
def _examples_root() -> Traversable:
    """Folder of the bundled examples inside the installed package."""
    return files("flow_state") / "examples"


def _description(config_text: str) -> str:
    """First text line of a config's header comment (dividers skipped)."""

    # walk the leading comment block
    for line in config_text.splitlines():
        stripped = line.strip()

        # the header ends at the first line that isn't a comment
        if stripped and not stripped.startswith("#"):
            break

        # skip blank comment lines and dividers like "# -----"
        text = stripped.lstrip("#").strip()
        if text and set(text) - set("-=#"):
            return text

    return ""


# --------------------------------------------------
# public API
# --------------------------------------------------
def list_examples() -> dict[str, str]:
    """Return a name -> description mapping of the bundled examples.

    Returns:
        Dict of {name: description}, sorted by name.
    """

    # every folder with a config is an example
    examples: dict[str, str] = {}
    for folder in sorted(_examples_root().iterdir(), key=lambda item: item.name):
        config = folder / EXAMPLE_CONFIG
        if folder.is_dir() and config.is_file():
            examples[folder.name] = _description(config.read_text(encoding="utf-8"))

    return examples


def copy_example(name: str, destination: str | Path, force: bool = False) -> list[Path]:
    """Copy a bundled example's files into a folder.

    Args:
        name: Example name (see list_examples).
        destination: Folder to create and copy the files into.
        force: Overwrite files that already exist in the folder.

    Returns:
        The paths of the written files.

    Raises:
        KeyError: If there is no example of that name.
        FileExistsError: If the folder exists and force is False.
    """

    # check: a known example
    if name not in list_examples():
        raise KeyError(name)

    # check: don't overwrite an earlier copy unless asked to
    destination = Path(destination)
    if destination.exists() and not force:
        raise FileExistsError(f"{destination} already exists (use --force to overwrite)")

    # copy every file of the example folder
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    source = _examples_root() / name
    for item in sorted(source.iterdir(), key=lambda entry: entry.name):
        if item.is_file():
            target = destination / item.name
            target.write_bytes(item.read_bytes())
            written.append(target)

    return written
