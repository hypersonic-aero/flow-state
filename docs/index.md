# flow_state

`flow_state` is a lightweight utility to compute thermodynamic and aerodynamic properties for compressible flows.

## Features

- **CLI**: Quick calculations from the terminal
- **API**: Enables scripting and automation
- [**Webapp**](https://flow-state-calculator.streamlit.app/): No installation required

## Quick Start

Install the [PyPI package](https://pypi.org/project/flowstate/) (see [Installation](installation.md) for detailed instructions).
```bash
pip install flowstate
```

Use `flow_state` package (see [User Guide](user-guide/index.md) for detailed examples)
```python
# load package
from flow_state import solve
# solve from known values
state = solve(mach=7.0, pres=1000.0, temp=200.0)
# print results
print(state)
```

## Webapp

Interactive flow calculator online (no installation required).

[Launch Webapp](https://flow-state-calculator.streamlit.app/)

## Why flow_state?

Specify the known quantities (Mach, altitude, Re, etc.), `flow_state` computes the rest.

## License

GNU General Public License v3.0 or later. See
[LICENSE](https://github.com/hypersonic-aero/flow-state/blob/main/LICENSE) for the
complete license terms.
