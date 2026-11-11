# BSD-3-Clause License - see LICENSE file
"""
Streamlit webapp for flow_state.

This app provides a web interface for computing compressible flow states
using the same builders as the CLI. No physics logic is duplicated here;
all calculations are delegated to the flow_state library.

Run with:
    streamlit run app.py
"""

import json
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

import streamlit as st

from flow_state import (
    from_mach_altitude_atmosphere,
    from_mach_pres_stag_temp_stag,
    from_mach_pres_temp,
    from_mach_re1_atmosphere,
    from_re1_pres_mach,
    from_re1_pres_stag_temp_stag,
    from_re1_temp_mach,
)
from flow_state.atmosphere import CIRA86, USSA76
from flow_state.gas import PerfectGas
from flow_state.transport import Sutherland

try:
    __version__ = _pkg_version("flowstate")
except PackageNotFoundError:
    __version__ = "0+unknown"

# Solver options with user-friendly names
SOLVERS = {
    "Mach, Pressure, Temperature": "mach_pres_temp",
    "Mach, Stagnation Pressure, Stagnation Temperature": "mach_pres_stag_temp_stag",
    "Mach, Altitude": "mach_altitude",
    "Unit Reynolds, Temperature, Mach": "re1_temp_mach",
    "Unit Reynolds, Pressure, Mach": "re1_pres_mach",
    "Unit Reynolds, Stagnation Pressure, Stagnation Temperature": "re1_pres_stag_temp_stag",
    "Mach, Unit Reynolds, Altitude": "mach_re1_altitude",
}


def display_results(state) -> None:
    """Display computed flow state results."""
    st.success("Flow state computed successfully!")

    # Build results table
    data = {
        "Property": [],
        "Value": [],
        "Unit": [],
    }

    def add_row(name, value, unit, fmt=".4e"):
        data["Property"].append(name)
        data["Value"].append(f"{value:{fmt}}" if value is not None else "—")
        data["Unit"].append(unit)

    # Static conditions
    add_row("Pressure", state.pres, "Pa")
    add_row("Temperature", state.temp, "K", ".2f")
    add_row("Density", state.dens, "kg/m³")

    # Stagnation conditions
    add_row("Stagnation Pressure", state.pres_stag, "Pa")
    add_row("Stagnation Temperature", state.temp_stag, "K", ".2f")
    add_row("Stagnation Density", state.dens_stag, "kg/m³")

    # Kinematic properties
    add_row("Mach", state.mach, "—", ".4f")
    add_row("Velocity", state.uvel, "m/s", ".2f")
    add_row("Speed of Sound", state.a, "m/s", ".2f")

    # Gas properties
    add_row("gamma", state.gamma, "—", ".4f")
    add_row("R", state.r_gas, "J/(kg K)", ".2f")
    add_row("cp", state.cp, "J/(kg K)", ".2f")

    # Transport properties
    if state.mu is not None:
        add_row("Dynamic Viscosity", state.mu, "Pa s")
        add_row("Kinematic Viscosity", state.nu, "m²/s")
        add_row("Unit Reynolds", state.re1, "1/m")

    # Reference-based
    if state.lref is not None:
        add_row("Reference Length", state.lref, "m", ".4f")
        if state.re1 is not None:
            re = state.re1 * state.lref
            add_row("Reynolds Number", re, "—")

    # Display table
    st.subheader("Results")
    st.dataframe(
        data,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # Use the API's to_dict which includes [value, "unit"] arrays
    state_dict = state.to_dict()
    # Remove None values for cleaner output
    state_dict = {k: v for k, v in state_dict.items() if v is not None}

    json_content = json.dumps(state_dict, indent=2)
    st.download_button(
        label="Download JSON",
        data=json_content,
        file_name="flow_state.json",
        mime="application/json",
        width="stretch",
    )

    # Show raw output in expander
    with st.expander("View JSON"):
        st.code(json_content, language="json")


def get_gas_and_transport():
    """Get gas model and transport model from user selection."""
    st.subheader("Gas Model")
    gas_choice = st.selectbox(
        "Select gas model",
        options=["Air", "Nitrogen", "Custom"],
        index=0,
    )

    if gas_choice == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            gamma = st.number_input(
                "Specific heat ratio (gamma)",
                min_value=1.01,
                max_value=2.0,
                value=1.4,
                step=0.01,
                format="%.4f",
            )
        with col2:
            R = st.number_input(
                "Gas constant R [J/(kg K)]",
                min_value=100.0,
                max_value=1000.0,
                value=287.05,
                step=1.0,
                format="%.2f",
            )
        gas = PerfectGas.custom(gamma=gamma, r_gas=R, name="custom")
        transport = Sutherland.air()
    elif gas_choice == "Nitrogen":
        gas = PerfectGas.nitrogen()
        transport = Sutherland.nitrogen()
    else:
        gas = PerfectGas.air()
        transport = Sutherland.air()

    return gas, transport


def get_atmosphere():
    """Get atmosphere model from user selection."""
    atm_choice = st.selectbox(
        "Atmosphere model",
        options=["USSA76", "CIRA86"],
        index=0,
    )
    return USSA76() if atm_choice == "USSA76" else CIRA86()


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Flow Conditions Calculator",
        layout="centered",
    )

    st.title("Flow Conditions Calculator")
    st.markdown(f"*flow_state* v{__version__}")

    st.divider()

    # Solver selection
    st.subheader("Solver")
    solver_name = st.selectbox(
        "Select solver based on known inputs",
        options=list(SOLVERS.keys()),
        index=0,
    )
    solver = SOLVERS[solver_name]

    st.divider()

    # Determine if we need gas model (not needed for atmosphere-based solvers)
    needs_gas = solver not in ["mach_altitude", "mach_re1_altitude"]

    gas = None
    transport = None
    if needs_gas:
        gas, transport = get_gas_and_transport()
        st.divider()

    # Flow conditions based on solver
    st.subheader("Flow Conditions")

    # Collect inputs based on solver type
    mach = None
    pres = None
    temp = None
    pres_stag = None
    temp_stag = None
    altitude = None
    re1 = None
    atm = None

    if solver == "mach_pres_temp":
        col1, col2, col3 = st.columns(3)
        with col1:
            mach = st.number_input("Mach number", min_value=0.01, max_value=50.0, value=6.0, step=0.1, format="%.4f")
        with col2:
            pres = st.number_input("Static pressure [Pa]", min_value=0.1, max_value=1e8, value=101325.0, step=1000.0, format="%.2f")
        with col3:
            temp = st.number_input("Static temperature [K]", min_value=50.0, max_value=5000.0, value=300.0, step=10.0, format="%.2f")

    elif solver == "mach_pres_stag_temp_stag":
        col1, col2, col3 = st.columns(3)
        with col1:
            mach = st.number_input("Mach number", min_value=0.01, max_value=50.0, value=6.0, step=0.1, format="%.4f")
        with col2:
            pres_stag = st.number_input("Stagnation pressure [Pa]", min_value=1.0, max_value=1e9, value=1e6, step=10000.0, format="%.2f")
        with col3:
            temp_stag = st.number_input("Stagnation temperature [K]", min_value=100.0, max_value=10000.0, value=1000.0, step=50.0, format="%.2f")

    elif solver == "mach_altitude":
        col1, col2 = st.columns(2)
        with col1:
            mach = st.number_input("Mach number", min_value=0.01, max_value=50.0, value=6.0, step=0.1, format="%.4f")
        with col2:
            altitude = st.number_input("Altitude [km]", min_value=0.0, max_value=120.0, value=30.0, step=1.0, format="%.2f")
        atm = get_atmosphere()

    elif solver == "re1_temp_mach":
        col1, col2, col3 = st.columns(3)
        with col1:
            re1 = st.number_input("Unit Reynolds [1/m]", min_value=1e3, max_value=1e9, value=1e6, step=1e5, format="%.4e")
        with col2:
            temp = st.number_input("Static temperature [K]", min_value=50.0, max_value=5000.0, value=300.0, step=10.0, format="%.2f")
        with col3:
            mach = st.number_input("Mach number", min_value=0.01, max_value=50.0, value=6.0, step=0.1, format="%.4f")

    elif solver == "re1_pres_mach":
        col1, col2, col3 = st.columns(3)
        with col1:
            re1 = st.number_input("Unit Reynolds [1/m]", min_value=1e3, max_value=1e9, value=1e6, step=1e5, format="%.4e")
        with col2:
            pres = st.number_input("Static pressure [Pa]", min_value=0.1, max_value=1e8, value=101325.0, step=1000.0, format="%.2f")
        with col3:
            mach = st.number_input("Mach number", min_value=0.01, max_value=50.0, value=6.0, step=0.1, format="%.4f")

    elif solver == "re1_pres_stag_temp_stag":
        col1, col2, col3 = st.columns(3)
        with col1:
            re1 = st.number_input("Unit Reynolds [1/m]", min_value=1e3, max_value=1e9, value=1e6, step=1e5, format="%.4e")
        with col2:
            pres_stag = st.number_input("Stagnation pressure [Pa]", min_value=1.0, max_value=1e9, value=1e6, step=10000.0, format="%.2f")
        with col3:
            temp_stag = st.number_input("Stagnation temperature [K]", min_value=100.0, max_value=10000.0, value=1000.0, step=50.0, format="%.2f")

    elif solver == "mach_re1_altitude":
        col1, col2 = st.columns(2)
        with col1:
            mach = st.number_input("Mach number", min_value=0.01, max_value=50.0, value=6.0, step=0.1, format="%.4f")
        with col2:
            re1 = st.number_input("Unit Reynolds [1/m]", min_value=1e3, max_value=1e9, value=1e6, step=1e5, format="%.4e")
        atm = get_atmosphere()

    # Reference length
    st.divider()
    st.subheader("Reference Length")
    lref = st.number_input(
        "Reference length [m] (set to 0 to skip)",
        min_value=0.0,
        max_value=1000.0,
        value=1.0,
        step=0.1,
        format="%.4f",
    )
    if lref == 0.0:
        lref = None

    st.divider()

    # Compute button
    if st.button("Compute", type="primary", width="stretch"):
        try:
            if solver == "mach_pres_temp":
                state = from_mach_pres_temp(
                    mach=mach, pres=pres, temp=temp,
                    gas=gas, transport=transport, lref=lref,
                )
            elif solver == "mach_pres_stag_temp_stag":
                state = from_mach_pres_stag_temp_stag(
                    mach=mach, pres_stag=pres_stag, temp_stag=temp_stag,
                    gas=gas, transport=transport, lref=lref,
                )
            elif solver == "mach_altitude":
                state = from_mach_altitude_atmosphere(
                    mach=mach, altitude_km=altitude, atmosphere=atm, lref=lref,
                )
            elif solver == "re1_temp_mach":
                state = from_re1_temp_mach(
                    re1=re1, temp=temp, mach=mach,
                    gas=gas, transport=transport, lref=lref,
                )
            elif solver == "re1_pres_mach":
                state = from_re1_pres_mach(
                    re1=re1, pres=pres, mach=mach,
                    gas=gas, transport=transport, lref=lref,
                )
            elif solver == "re1_pres_stag_temp_stag":
                state = from_re1_pres_stag_temp_stag(
                    re1=re1, pres_stag=pres_stag, temp_stag=temp_stag,
                    gas=gas, transport=transport, lref=lref,
                )
            elif solver == "mach_re1_altitude":
                state = from_mach_re1_atmosphere(
                    mach=mach, re1=re1, atmosphere=atm, lref=lref,
                )

            display_results(state)

        except Exception as e:
            st.error(f"Error computing flow state: {e}")

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.8em;'>
        flow_state by UAH Hypersonics<br>
        <a href="https://github.com/hypersonic-aero/flow-state" target="_blank">GitHub</a> |
        <a href="https://hypersonic-aero.github.io/flow-state" target="_blank">Documentation</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
