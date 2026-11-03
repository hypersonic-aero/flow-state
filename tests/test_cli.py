"""Tests for the flow-state command-line interface."""

from __future__ import annotations

import json

import h5py
import pytest
from typer.testing import CliRunner

from flow_state.cli import app, cli
from flow_state.io.examples import list_examples

runner = CliRunner()


def test_cli_alias_preserves_console_entry_point() -> None:
    """The historical ``flow_state.cli:cli`` entry point remains valid."""

    assert cli is app


def test_help_lists_commands() -> None:
    """Top-level help presents the public command surface."""

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Commands" in result.output
    assert "run" in result.output
    assert "init" in result.output
    assert "recover" in result.output


def test_version_exits_successfully() -> None:
    """The eager version option does not require a command."""

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.startswith("flow-state version ")


def test_init_creates_template(tmp_path) -> None:
    """The init command writes a usable starter configuration."""

    output_path = tmp_path / "flow_config.toml"
    result = runner.invoke(app, ["init", "--output", str(output_path)])

    assert result.exit_code == 0
    assert output_path.exists()
    assert "mach = 6.0" in output_path.read_text()


def test_init_refuses_to_overwrite_existing_file(tmp_path) -> None:
    """The init command protects existing configuration files."""

    output_path = tmp_path / "flow_config.toml"
    output_path.write_text("existing")
    result = runner.invoke(app, ["init", "--output", str(output_path)])

    assert result.exit_code == 1
    assert "Use --force to overwrite" in result.output
    assert output_path.read_text() == "existing"


def test_run_reports_missing_config(tmp_path, monkeypatch) -> None:
    """The default workflow explains how to recover from a missing config."""

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run"])

    assert result.exit_code == 1
    assert "flow_config.toml not found" in result.output
    assert "flow-state init" in result.output


def test_run_rejects_a_misspelled_config_key(tmp_path, monkeypatch) -> None:
    """A typo in the config fails and names the key, instead of being ignored."""

    monkeypatch.chdir(tmp_path)
    (tmp_path / "flow_config.toml").write_text(
        'mach = 6.0\npres_stag = [140, "psi"]\ntemp_stag = 420\nlrefs = 0.5\n'
    )
    result = runner.invoke(app, ["run"])

    assert result.exit_code == 1
    assert "lrefs" in result.output
    assert not (tmp_path / "flow_conditions.json").exists()


def test_run_direct_options_writes_json(tmp_path) -> None:
    """Direct inputs run the solver and write structured output."""

    output_path = tmp_path / "flow_state.json"
    result = runner.invoke(
        app,
        [
            "run",
            "--mach",
            "2",
            "--pres",
            "101325",
            "--temp",
            "300",
            "--quiet",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert f"Wrote {output_path}" in result.output
    output_data = json.loads(output_path.read_text())
    assert output_data["mach"][0] == 2.0


def test_recover_writes_flow_conditions_json(tmp_path) -> None:
    """HDF5 root attributes can reconstruct the canonical JSON output."""
    input_path = tmp_path / "base_flow.hdf5"
    output_path = tmp_path / "recovered.json"
    with h5py.File(input_path, "w") as hdf5_file:
        hdf5_file.attrs["mach"] = 6.0
        hdf5_file.attrs["re1"] = 10_000_000.0
        hdf5_file.attrs["temp_inf"] = 45.73170731707317

    result = runner.invoke(
        app,
        ["recover", str(input_path), "--output", str(output_path), "--quiet"],
    )

    assert result.exit_code == 0
    assert f"Wrote {output_path}" in result.output
    output_data = json.loads(output_path.read_text())
    assert output_data["mach"] == [6.0, "-"]
    assert output_data["re1"][0] == pytest.approx(10_000_000.0)


def test_recover_reports_insufficient_metadata(tmp_path) -> None:
    """Recovery explains when recognized attributes cannot define a state."""
    input_path = tmp_path / "base_flow.hdf5"
    with h5py.File(input_path, "w") as hdf5_file:
        hdf5_file.attrs["mach"] = 6.0

    result = runner.invoke(app, ["recover", str(input_path)])

    assert result.exit_code == 1
    assert "does not contain a complete flow-state input combination" in result.output


# --------------------------------------------------
# examples
# --------------------------------------------------
EXAMPLE_NAMES = sorted(list_examples())


def test_examples_lists_every_example_with_a_description() -> None:
    """Without a name, examples lists each example and its description."""

    result = runner.invoke(app, ["examples"])

    assert result.exit_code == 0
    for name, description in list_examples().items():
        assert description
        assert name in result.output
        assert description in result.output


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_every_example_copies_and_runs(tmp_path, monkeypatch, name: str) -> None:
    """Each example lands in ./<name>/ and runs there with the default config name."""

    monkeypatch.chdir(tmp_path)
    copy_result = runner.invoke(app, ["examples", name])
    assert copy_result.exit_code == 0

    monkeypatch.chdir(tmp_path / name)
    run_result = runner.invoke(app, ["run", "--quiet"])

    assert run_result.exit_code == 0
    assert (tmp_path / name / "flow_conditions.json").exists()


def test_examples_refuses_an_existing_folder_unless_forced(tmp_path, monkeypatch) -> None:
    """A second copy fails without --force and overwrites with it."""

    monkeypatch.chdir(tmp_path)
    name = EXAMPLE_NAMES[0]
    runner.invoke(app, ["examples", name])

    refused = runner.invoke(app, ["examples", name])
    forced = runner.invoke(app, ["examples", name, "--force"])

    assert refused.exit_code == 1
    assert "already exists" in refused.output
    assert forced.exit_code == 0


def test_examples_rejects_an_unknown_name(tmp_path, monkeypatch) -> None:
    """An unknown name fails and lists the available examples."""

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["examples", "nope"])

    assert result.exit_code == 1
    assert "unknown example" in result.output
    assert EXAMPLE_NAMES[0] in result.output
    assert not (tmp_path / "nope").exists()
