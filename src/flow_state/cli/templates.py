"""Configuration templates emitted by flow-state CLI commands."""

# --------------------------------------------------
# configuration template
# --------------------------------------------------

# starter flow_config.toml written by `flow-state init`
CONFIG_TEMPLATE = """\
# flow_state configuration file
# =============================
# Edit the values below and run: flow-state run

# Supported units:
#   pressure    : Pa, psi, atm, bar, torr
#   temperature : K, C, F, R (Rankine)
#   length      : m, ft, km, mi
#   velocity    : m/s, ft/s, kts, mph, kph

# Use [value, "unit"] tuples for non-SI units, e.g.:
#   pres_stag = [140, "psi"]
#   altitude = [30000, "ft"]

# --------------------------------------------------
# Input mode: Choose ONE of the following sections
# --------------------------------------------------

# Option 1: Mach + stagnation conditions (wind tunnel)
mach = 6.0
pres_stag = [140, "psi"]  # or 965266.0 for Pa
temp_stag = 420           # Kelvin

# Option 2: Altitude + Mach (flight conditions)
# altitude = [30000, "ft"]
# mach = 0.8

# Option 3: Static conditions
# pres = 101325    # Pa
# temp = 300       # K
# mach = 2.0

# --------------------------------------------------
# Reference length scale (for turbulence scales)
# --------------------------------------------------
lref = 1.0  # [m]

# --------------------------------------------------
# Gas model (optional, default: "air")
# --------------------------------------------------
# gas = "air"       # calorically perfect air (gamma=1.4, R=287.05)
# gas = "n2"        # nitrogen (gamma=1.4, R=296.8, Sutherland nitrogen)

# --------------------------------------------------
# Optional notes
# --------------------------------------------------
# notes = "BAM6QT Mach 6 tunnel conditions"
"""
