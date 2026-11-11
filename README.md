# flow_state

Compressible flow state calculations for Python.

[![Test](https://github.com/hypersonic-aero/flow-state/actions/workflows/test.yml/badge.svg)](https://github.com/hypersonic-aero/flow-state/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/hypersonic-aero/flow-state/branch/main/graph/badge.svg)](https://codecov.io/gh/hypersonic-aero/flow-state)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18926470.svg)](https://doi.org/10.5281/zenodo.18926470)
[![PyPI](https://img.shields.io/pypi/v/flowstate)](https://pypi.org/project/flowstate/)
[![Docs](https://img.shields.io/badge/docs-zensical-blue)](https://hypersonic-aero.github.io/flow-state/)
[![Webapp](https://img.shields.io/badge/webapp-streamlit-red)](https://flow-state-calculator.streamlit.app/)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.11-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Install

```bash
pip install flowstate
```

## Quick Start

**API:**

```python
from flow_state import solve

# From Mach and altitude
state = solve(mach=2.0, altitude=10000)

# From Mach and stagnation conditions (wind tunnel)
state = solve(mach=6, pres_stag=(140, "psi"), temp_stag=420)

# From Mach and target unit Reynolds number
state = solve(mach=5.3, re1=12.8e6)

print(state)  # Full summary
print(state.pres, state.temp, state.re1)
```

**CLI:**

```bash
flow-state init    # Create a config template
flow-state solve   # Solve from flow_config.toml
flow-state recover base_flow.hdf5  # Recover flow_conditions.json from HDF5 metadata
```

- API Usage: https://hypersonic-aero.github.io/flow-state/user_guide/api_usage/
- CLI Usage: https://hypersonic-aero.github.io/flow-state/user_guide/cli_usage/

## Documentation

Full documentation: https://hypersonic-aero.github.io/flow-state

## Citation

If you use `flow_state` in your research, please cite it:

```bibtex
@software{flow_state,
  author = {Hader, Christoph},
  title = {flow\_state: Compressible Flow State Calculations},
  url = {https://github.com/hypersonic-aero/flow-state},
  year = {2026}
}
```

## Code Style

This project follows established Python community conventions so that
contributors can focus on the physics rather than inventing formatting rules.

| Convention | What it covers | Reference |
|---|---|---|
| [PEP 8](https://peps.python.org/pep-0008/) | Code formatting, naming, whitespace | Python standard style guide |
| [PEP 257](https://peps.python.org/pep-0257/) | Docstring structure (triple-quoted, imperative mood) | Python standard docstring conventions |
| [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) | Docstring sections (`Args`, `Returns`, `Raises`) | Google Python style guide |
| [Ruff](https://docs.astral.sh/ruff/) | Automated linting and formatting | Enforces PEP 8 compliance automatically |
| [typing / TYPE_CHECKING](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING) | Type hints for IDE support and static analysis | Python standard library |

## Releasing

This project uses [Semantic Versioning](https://semver.org/) (`vMAJOR.MINOR.PATCH`):

- **MAJOR** (`v1.0.0`, `v2.0.0`): Breaking API changes
- **MINOR** (`v0.3.0`, `v0.4.0`): New features, backward-compatible
- **PATCH** (`v0.3.1`, `v0.3.2`): Bug fixes, minor corrections

To publish a new version to [PyPI](https://pypi.org/project/flowstate/):

1. Regenerate the API architecture diagram:
   ```bash
   pydeps src/flow_state --noshow --max-bacon=4 --cluster -o docs/assets/architecture.svg
   ```
2. Commit and push to `main`
3. Tag and push:
   ```bash
   git tag -a vMAJOR.MINOR.PATCH -m "Release vMAJOR.MINOR.PATCH"
   git push origin vMAJOR.MINOR.PATCH
   ```

The GitHub Actions workflow will automatically build and publish to PyPI via Trusted Publishing.

## License

GNU General Public License v3.0 or later. See [LICENSE](LICENSE) for the
complete license terms.
