import math
import pandas as pd
import streamlit as st

# -----------------------------
# Constants & option lists
# -----------------------------
SOUND_SPEED = 1500.0          # m/s (typical seawater)
KNOT_TO_MS = 0.514444         # 1 knot in m/s

hit_count_options = list(range(1, 11))     # 1..10
beam_options = [512, 1024]                 # typical values
speed_knots_options = [2, 3, 4, 5, 6, 7, 8]

# -----------------------------
# Inputs
# -----------------------------
depth = st.number_input(
    "🌊 Depth (m)",
    min_value=0.0, step=0.1, value=20.0,
    help="Water depth in meters used for swath and ping rate calculations."
)

cell_size = st.number_input(
    "🧱 Grid cell size (m)",
    min_value=0.01, step=0.01, value=1.0,
    help="Side length of the target grid cell in meters."
)

overlap = st.slider(
    "🔁 Swath overlap (%)",
    min_value=0, max_value=80, step=1, value=20,
    help="Percentage of swath overlap between adjacent lines. If not specified, use: 20%."
)

hit_count_min = st.select_slider(
    "🎯 Minimum hit count per cell",
    options=hit_count_options,
    value=3,
    help="Minimum number of soundings per grid cell. If not specified, use: 3"
)

n_beams = st.select_slider(
    "🔢 Number of beams",
    options=beam_options,
    value=1024,
    help="Total number of beams emitted per ping (typically 512 or 1024)"
)

speed_knots = st.select_slider(
    "🚤 Acquisition speed (knots)",
    options=speed_knots_options,
    value=4,
    help="Vessel speed during MBES acquisition. If not specified, use: 4 knots"
)

speed = speed_knots * KNOT_TO_MS

# -----------------------------
# Core functions
# -----------------------------
# Ping rate estimation
def calculate_ping_rate(depth_m):
    return 1 / (2 * depth_m / SOUND_SPEED) if depth_m > 0 else 1

# Apply correction factor to approximate field conditions
def calculate_hits_per_cell(swath_m, ping_rate_hz, n_beams_int, speed_ms, cell_size_m):
    density_across = n_beams_int / swath_m if swath_m > 0 else 0
    density_along = ping_rate_hz / speed_ms if speed_ms > 0 else 0
    return 0.325 * density_across * cell_size_m * density_along * cell_size_m

# -----------------------------
# Angle range selection
# -----------------------------
results = []
if depth < 7:
    angle_range = range(140, 4, -5)
elif depth > 40 and cell_size <= 0.25:
    angle_range = range(100, 4, -5)
else:
    angle_range = range(120, 4, -5)

# -----------------------------
# Main loop
# -----------------------------
for angle in angle_range:
    theta_rad = math.radians(angle)
    swath = 2 * depth * math.tan(theta_rad / 2)  # total coverage for a single pass

    ping_rate = calculate_ping_rate(depth)
    hits = calculate_hits_per_cell(swath, ping_rate, n_beams, speed, cell_size)
    valid = hits >= hit_count_min

    line_spacing = swath * (1 - overlap / 100)

    results.append({
        "Opening angle (°)": angle,
        "Line spacing (m)": round(line_spacing, 2),
        "Total coverage (m)": round(swath, 2),      # ← NEW COLUMN
        "Hit count per cell": round(hits, 1),
        "Meets requirement": "✅" if valid else "❌"
    })

# -----------------------------
# Build DataFrame & outputs
# -----------------------------
df = pd.DataFrame(results)

valid_angles = df[df["Meets requirement"] == "✅"]
if not valid_angles.empty:
    optimal_angle = valid_angles.iloc[0]["Opening angle (°)"]
    optimal_spacing = valid_angles.iloc[0]["Line spacing (m)"]
    st.info(f"**✔️ Maximum valid opening angle:** `{optimal_angle}°`")
    st.success(f"**📏 Maximum line spacing (with {overlap}% overlap):** `{optimal_spacing:.2f} m`")
else:
    st.error("❌ No swath angle meets the minimum hit count requirement.")

st.subheader("📊 Results per swath angle")
st.dataframe(df, use_container_width=True, hide_index=True)



