import streamlit as st
import numpy as np
import pandas as pd
import math

# Constants
SOUND_SPEED = 1500  # m/s
KNOT_TO_MS = 0.514444

st.set_page_config(page_title="Line Spacing Calculator MBES", layout="centered")
st.title("📡 Line Spacing Calculator MBES")

# Discrete options
cell_options = [0.1, 0.2, 0.25, 0.5, 1, 2, 3, 4, 5]
overlap_options = [10, 20, 30]
hit_count_options = [1, 2, 3, 4, 5]
beam_options = [512, 1024]
speed_knots_options = [2, 3, 4, 5, 6]

# User inputs with proper tooltips (help)
depth = st.slider(
    "🌊 Depth (m)",
    min_value=0.0,
    max_value=400.0,
    value=20.0,
    step=1.0,
    help="Depth of the seafloor below the MBES transducer (in meters)"
)

cell_size = st.select_slider(
    "📐 Cell size (m)",
    options=cell_options,
    value=0.5,
    help="Size of each cell in the grid where hit count is evaluated. If not specified, use: 0.5 m"
)

overlap = st.select_slider(
    "🔁 Line overlap (%)",
    options=overlap_options,
    value=20,
    help="Percentage of swath overlap between adjacent lines. If not specified, use: 20%"
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

# Ping rate estimation
def calculate_ping_rate(depth):
    return 1 / (2 * depth / SOUND_SPEED) if depth > 0 else 1

# Apply correction factor to approximate field conditions
def calculate_hits_per_cell(swath, ping_rate, n_beams, speed, cell_size):
    density_across = n_beams / swath
    density_along = ping_rate / speed
    return 0.325 * density_across * cell_size * density_along * cell_size

# Define valid angle range based on depth and cell size
results = []
if depth < 7:
    angle_range = range(140, 4, -5)
elif depth > 40 and cell_size <= 0.25:
    angle_range = range(100, 4, -5)
else:
    angle_range = range(120, 4, -5)

# Loop through angles and compute results
for angle in angle_range:
    theta_rad = math.radians(angle)
    swath = 2 * depth * math.tan(theta_rad / 2)
    ping_rate = calculate_ping_rate(depth)
    hits = calculate_hits_per_cell(swath, ping_rate, n_beams, speed, cell_size)
    valid = hits >= hit_count_min
    line_spacing = swath * (1 - overlap / 100)
    results.append({
        "Opening angle (°)": angle,
        "Line spacing (m)": round(line_spacing, 2),
        "Hit count per cell": round(hits, 1),
        "Meets requirement": "✅" if valid else "❌"
    })

# Build DataFrame
df = pd.DataFrame(results)

# Show results
valid_angles = df[df["Meets requirement"] == "✅"]
if not valid_angles.empty:
    optimal_angle = valid_angles.iloc[0]["Opening angle (°)"]
    optimal_spacing = valid_angles.iloc[0]["Line spacing (m)"]
    st.info(f"**✔️ Maximum valid opening angle:** `{optimal_angle}°`")
    st.success(f"**📏 Maximum line spacing (with {overlap}% overlap):** `{optimal_spacing:.2f} m`")
else:
    st.error("❌ No swath angle meets the minimum hit count requirement.")

# Show table
st.subheader("📊 Results per swath angle")
st.dataframe(df, use_container_width=True, hide_index=True)

