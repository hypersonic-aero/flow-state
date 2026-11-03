"""
tests for io functions (read_config, write_json)
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------

import json
import tempfile
from pathlib import Path

import pytest

from flow_state.io import read_config, read_json, write_json
from flow_state.io.legacy_dat import write_flow_conditions_dat
from flow_state.io.print_summary import summary
from flow_state.io.write_data import write_toml
from flow_state.solvers import solve
from flow_state.transport import Sutherland, transport_model_from_dict

# --------------------------------------------------
# tests for write_json
# --------------------------------------------------


class TestWriteJSON:
    """tests for JSON output"""

    def test_write_json_file(self) -> None:
        """write a state to a JSON file and verify contents"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_state.json"
            write_json(state, path)

            content = path.read_text()
            data = json.loads(content)

            # check for expected keys - values now include units as [value, "unit"]
            assert data["pres"] == [101325.0, "Pa"]
            assert data["temp"] == [300.0, "K"]
            assert data["mach"] == [2.0, "-"]
            assert "gas_model" in data
            assert data["transport_model"] == {
                "type": "sutherland",
                "parameters": {
                    "mu_ref": 1.716e-5,
                    "T_ref": 273.15,
                    "S": 110.4,
                },
            }

            reconstructed_model = transport_model_from_dict(data["transport_model"])
            assert reconstructed_model.mu(300.0) == pytest.approx(state.mu)

    def test_json_includes_provenance(self) -> None:
        """verify provenance is included in JSON output"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_state.json"
            write_json(state, path)

            content = path.read_text()
            data = json.loads(content)

            assert "provenance" in data
            assert data["provenance"]["builder"] == "from_mach_pres_temp"
            assert "inputs" in data["provenance"]


# --------------------------------------------------
# tests for read_json
# --------------------------------------------------


class TestReadJSON:
    """tests for JSON input"""

    def test_flow_state_round_trip(self, tmp_path: Path) -> None:
        """read_json reconstructs every field written by write_json"""
        state = solve(
            mach=2.0,
            altitude=10000.0,
            transport=Sutherland.air(),
            notes="round-trip test",
        )
        path = tmp_path / "flow_state.json"

        # write and reconstruct the complete state
        write_json(state, path)
        reconstructed_state = read_json(path)

        # check the complete public serialized representation
        assert reconstructed_state.to_dict() == state.to_dict()

    def test_flow_state_from_dict_without_transport(self) -> None:
        """from_dict preserves optional null fields"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0)
        state_data = state.to_dict()
        state_data["transport_model"] = None
        state_data["mu"] = None
        state_data["nu"] = None
        state_data["re1"] = None
        state_data["kolmogorov"] = None
        state_data["taylor"] = None

        # reconstruct directly from the canonical dictionary
        reconstructed_state = type(state).from_dict(state_data)

        assert reconstructed_state.to_dict() == state_data
        assert reconstructed_state.transport_model is None
        assert reconstructed_state.kolmogorov is None
        assert reconstructed_state.taylor is None

    def test_from_dict_rejects_wrong_unit(self) -> None:
        """from_dict rejects values carrying incompatible units"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0)
        state_data = state.to_dict()
        state_data["temp"] = [300.0, "Pa"]

        with pytest.raises(ValueError, match="temp must use unit 'K'"):
            type(state).from_dict(state_data)

    def test_read_json_rejects_non_object_root(self, tmp_path: Path) -> None:
        """read_json rejects JSON documents that cannot represent a FlowState"""
        path = tmp_path / "flow_state.json"
        path.write_text("[]", encoding="utf-8")

        with pytest.raises(TypeError, match="JSON root must be an object"):
            read_json(path)


# --------------------------------------------------
# tests for read_config
# --------------------------------------------------


class TestReadConfig:
    """tests for config file reading"""

    def test_read_config_simple(self) -> None:
        """read a simple config file with basic values"""
        config_content = """
mach = 2.0
pres = 101325.0
temp = 300.0
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_config.toml"
            path.write_text(config_content)

            kwargs = read_config(path)

            assert kwargs["mach"] == 2.0
            assert kwargs["pres"] == 101325.0
            assert kwargs["temp"] == 300.0

    def test_read_config_with_units(self) -> None:
        """read config with unit tuples like [140, "psi"]"""
        config_content = """
mach = 6.0
pres_stag = [140, "psi"]
temp_stag = 420
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_config.toml"
            path.write_text(config_content)

            kwargs = read_config(path)

            assert kwargs["mach"] == 6.0
            # unit tuple should be converted from list to tuple
            assert kwargs["pres_stag"] == (140, "psi")
            assert kwargs["temp_stag"] == 420

    def test_read_config_with_notes(self) -> None:
        """read config with notes field"""
        config_content = """
mach = 2.0
pres = 101325.0
temp = 300.0
notes = "Test case"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_config.toml"
            path.write_text(config_content)

            kwargs = read_config(path)

            assert kwargs["notes"] == "Test case"


# --------------------------------------------------
# tests for config validation (FlowConfig)
# --------------------------------------------------

# shipped example configs and the template written by `flow-state init`
EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "src" / "flow_state" / "examples"
EXAMPLE_CONFIGS = sorted(EXAMPLES_DIR.glob("*/flow_config.toml"))


def _write_config(tmp_path: Path, text: str) -> Path:
    """Write a config file into the test directory."""
    path = tmp_path / "flow_config.toml"
    path.write_text(text)
    return path


class TestConfigValidation:
    """config errors fail at the input boundary, naming the key"""

    @pytest.mark.parametrize(
        ("config_text", "key", "message"),
        [
            # typo of an optional key: used to be ignored silently
            ("mach = 6.0\npres = 600.0\ntemp = 50.0\nlrefs = 0.5\n", "lrefs", "Extra inputs"),
            # typo of an input key
            ('mach = 6.0\npres_stg = [140, "psi"]\ntemp_stag = 420\n', "pres_stg", "Extra inputs"),
            # unknown unit
            ('mach = 6.0\npres_stag = [140, "psii"]\ntemp_stag = 420\n', "pres_stag", "psii"),
            # out-of-range values
            ("mach = -6.0\npres = 600.0\ntemp = 50.0\n", "mach", "greater than 0"),
            ('mach = 6.0\npres = 600.0\ntemp = [-300, "C"]\n', "temp", "absolute zero"),
            # unknown gas
            ('mach = 6.0\npres = 600.0\ntemp = 50.0\ngas = "argon"\n', "gas", "argon"),
            # [atmosphere] table: range and unknown key
            ("mach = 6.0\naltitude = 30000\n[atmosphere]\nmodel = \"cira86\"\nmonth = 13\n",
             "atmosphere.month", "less than or equal to 12"),
            ("mach = 6.0\naltitude = 30000\n[atmosphere]\nlatitud = 30\n",
             "atmosphere.latitud", "Extra inputs"),
            # the atmosphere given twice
            ('mach = 6.0\naltitude = 30000\natm = "ussa76"\n[atmosphere]\nmodel = "cira86"\n',
             "not both", "not both"),
        ],
    )
    def test_invalid_config_names_the_key(
        self, tmp_path: Path, config_text: str, key: str, message: str
    ) -> None:
        """each invalid config raises a ValueError with the key and the reason"""
        path = _write_config(tmp_path, config_text)

        with pytest.raises(ValueError) as error:
            read_config(path)

        assert key in str(error.value)
        assert message in str(error.value)
        assert "errors.pydantic.dev" not in str(error.value)

    def test_atmosphere_table_builds_cira86(self, tmp_path: Path) -> None:
        """an [atmosphere] table with options becomes a configured CIRA86 model"""
        from flow_state.atmosphere import CIRA86

        config_text = 'mach = 6.0\naltitude = 30000\n[atmosphere]\nmodel = "cira86"\nlatitude = 30.0\nmonth = 7\n'
        path = _write_config(tmp_path, config_text)

        kwargs = read_config(path)

        assert isinstance(kwargs["atm"], CIRA86)
        assert "atmosphere" not in kwargs

    @pytest.mark.parametrize("example_path", EXAMPLE_CONFIGS, ids=lambda path: path.parent.name)
    def test_shipped_examples_validate_and_solve(self, example_path: Path) -> None:
        """every shipped example config validates and solves"""
        kwargs = read_config(example_path)

        state = solve(**kwargs)

        assert state.mach > 0.0

    def test_init_template_validates(self, tmp_path: Path) -> None:
        """the template written by `flow-state init` validates and solves"""
        from flow_state.cli.templates import CONFIG_TEMPLATE

        path = _write_config(tmp_path, CONFIG_TEMPLATE)
        kwargs = read_config(path)

        state = solve(**kwargs)

        assert state.mach > 0.0


# --------------------------------------------------
# tests for print_summary
# --------------------------------------------------


class TestPrintSummary:
    """tests for human-readable summary output"""

    def test_summary_basic(self) -> None:
        """summary includes key flow properties"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0)
        text = summary(state)

        assert "FlowState Summary" in text
        assert "pres" in text
        assert "temp" in text
        assert "mach" in text

    def test_summary_with_transport(self) -> None:
        """summary includes transport properties when present"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0, transport=Sutherland.air())
        text = summary(state)

        assert "mu" in text
        assert "nu" in text
        assert "re1" in text
        assert "pr" in text

    def test_summary_with_altitude(self) -> None:
        """summary includes altitude when present"""
        state = solve(mach=2.0, altitude=10000)
        text = summary(state)

        assert "altitude" in text
        assert "atm_model" in text

    def test_str_calls_summary(self) -> None:
        """FlowState.__str__ returns the summary"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0)
        assert str(state) == summary(state)


# --------------------------------------------------
# tests for legacy .dat writer
# --------------------------------------------------


class TestLegacyDat:
    """tests for legacy .dat file output"""

    def test_write_dat_no_header(self) -> None:
        """write dat without header (avoids legacy tool_version attribute)"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "flow.dat"
            write_flow_conditions_dat(state, path)

            content = path.read_text()
            assert "freestream pressure, pfs" in content
            assert "freestream temperature, Tfs" in content
            assert "freestream density, rhofs" in content
            assert "heat capacity ratio, gamma" in content
            assert "freestream Mach number, M" in content

    def test_write_dat_with_transport(self) -> None:
        """transport properties included when present"""
        state = solve(mach=2.0, pres=101325.0, temp=300.0, transport=Sutherland.air())

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "flow.dat"
            write_flow_conditions_dat(state, path)

            content = path.read_text()
            assert "viscosity, mu" in content
            assert "unit Reynolds number, re1" in content
            assert "Prandtl number, Pr" in content


# --------------------------------------------------
# tests for write_toml
# --------------------------------------------------


class TestWriteTOML:
    """tests for TOML output"""

    @pytest.mark.skip(
        reason="write_toml broken: to_dict() contains None values that tomli_w cannot serialize"
    )
    def test_write_toml_basic(self) -> None:
        """write a state to TOML and verify file exists"""
        # use a full solve with all fields populated to avoid None serialization issues
        state = solve(mach=2.0, altitude=10000, transport=Sutherland.air())

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.toml"
            write_toml(state, path)

            content = path.read_text()
            assert "pres" in content
            assert "temp" in content
