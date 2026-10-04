"""anatomy.py — Interactive anatomy (D3.js).
Anatomic nephron diagram: osmolality-gradient background, dynamic thickness by flow,
and a concentration heatmap. The segment in the shared selection is highlighted."""
import os
import json
import streamlit as st

import nav
from ui_kit import q, DB, options, NEPHRONS, segment_broken, PROJ, CD_SEGMENTS

active_scenario = nav.get("scenario")

st.markdown("## Interactive Anatomy (BETA)")
st.caption(
    "D3.js-based anatomic nephron drawing. "
    "Segment color shows the selected solute's concentration (switchable to solute **load / flux** "
    "with the button on top), segment thickness shows tubular water flow (volume), "
    "and the background gradient reflects the prescribed interstitial osmolality. "
    "The flow animation conveys water flow via particle speed; click a segment to pin its profile to the chart."
)

# --- Top selectors (bound to the shared selection) ---
c1, c2, c3, c4 = st.columns(4)
segs, sol = options()
solute = nav.select(c1, "Solute", sol, "solute", fallback="Na")
compartment = nav.select(c2, "Compartment", ["Lumen", "Cell", "Bath"], "compartment", fallback="Lumen")
nephron_req = nav.select(c3, "Nephron type (CD segments are 'merged')", NEPHRONS, "nephron", fallback="sup")
focus = nav.select(c4, "Highlighted segment", segs, "segment", fallback="PT",
                   help="The segment in your selection. It is highlighted on the diagram and is the "
                        "one the other pages open with.")

st.markdown("---")

# ============================================================
# 1) Concentration data (for segment colors)
# ============================================================
cd_segs = CD_SEGMENTS
segments_data = {}

all_segs_raw = q(
    f"""SELECT DISTINCT segment FROM {DB}
        WHERE condition = ? AND variable='con' AND solute=?
        AND compartment=?""",
    [active_scenario, solute, compartment]
)

for segment in all_segs_raw['segment'].tolist():
    target_nephron = "merged" if segment in cd_segs else nephron_req
    df_seg = q(
        f"""SELECT position, value FROM {DB}
            WHERE condition=? AND variable='con' AND solute=? AND compartment=?
            AND segment=? AND nephron=? ORDER BY position""",
        [active_scenario, solute, compartment, segment, target_nephron]
    )
    if df_seg.empty or segment_broken(active_scenario, segment):
        continue
    if df_seg['value'].isna().any():
        continue
    segments_data[segment] = {
        "entry": float(df_seg['value'].iloc[0]),
        "exit": float(df_seg['value'].iloc[-1]),
        "mean": float(df_seg['value'].mean()),
        "profile": list(zip(
            df_seg['position'].round(4).tolist(),
            df_seg['value'].round(4).tolist()
        )),
    }

if not segments_data:
    st.warning("No valid data for the selected filters.")
    st.stop()

# Global min/max for color scale
all_vals = [v for s in segments_data.values() for v in (s["entry"], s["exit"])]
con_min = min(all_vals)
con_max = max(all_vals)

# ============================================================
# 2) Water-volume (flow) data (for segment thickness)
# ============================================================
flow_data = {}
for segment in segments_data.keys():
    target_nephron = "merged" if segment in cd_segs else nephron_req
    df_flow = q(
        f"""SELECT position, value FROM {DB}
            WHERE condition=? AND variable='water_volume' AND compartment='Lumen'
            AND segment=? AND nephron=? ORDER BY position""",
        [active_scenario, segment, target_nephron]
    )
    if not df_flow.empty and df_flow['value'].notna().all():
        flow_data[segment] = {
            "entry": float(df_flow['value'].iloc[0]),
            "exit": float(df_flow['value'].iloc[-1]),
            "mean": float(df_flow['value'].mean()),
        }

# Global flow min/max for thickness scale
all_flows = [v for s in flow_data.values() for v in (s["entry"], s["exit"])]
flow_min = min(all_flows) if all_flows else 0
flow_max = max(all_flows) if all_flows else 100

# ============================================================
# 2b) Solute LOAD (load = molar flux, pmol/min) — for the color mode
# ============================================================
# Concentration misleads; for reabsorption/delivery look at MASS (flux). This mode makes
# the "golden rule" from the clinical-page science audit visible on the diagram.
load_data = {}
for segment in segments_data.keys():
    target_nephron = "merged" if segment in cd_segs else nephron_req
    df_load = q(
        f"""SELECT position, value FROM {DB}
            WHERE condition=? AND variable='flow' AND solute=? AND compartment='Lumen'
            AND segment=? AND nephron=? ORDER BY position""",
        [active_scenario, solute, segment, target_nephron]
    )
    if not df_load.empty and df_load['value'].notna().all():
        load_data[segment] = {
            "entry": float(df_load['value'].iloc[0]),
            "exit": float(df_load['value'].iloc[-1]),
            "mean": float(df_load['value'].mean()),
            "profile": list(zip(
                df_load['position'].round(4).tolist(),
                df_load['value'].round(2).tolist()
            )),
        }

all_loads = [v for s in load_data.values() for v in (s["entry"], s["exit"])]
load_min = min(all_loads) if all_loads else 0
load_max = max(all_loads) if all_loads else 100

# ============================================================
# 3) Interstitial (Bath) osmolality gradient (for the background)
# ============================================================
# Cortical segments (sup), medullary segments (sup or merged CD)
# Goal: an osmolality gradient by depth (y-coordinate)
gradient_segments = [
    ("PT",   "sup",    0.0),   # Cortex top
    ("cTAL", "sup",    0.15),  # Cortex bottom
    ("S3",   "sup",    0.28),  # Outer-medulla upper boundary
    ("mTAL", "sup",    0.40),  # Outer medulla middle
    ("SDL",  "sup",    0.55),  # Outer medulla lower
    ("OMCD", "merged", 0.55),  # Outer–inner medulla boundary
    ("IMCD", "merged", 1.0),   # Papilla (deepest)
]

gradient_stops = []
for seg, neph, frac in gradient_segments:
    df_osm = q(
        f"""SELECT AVG(value) as avg_osm FROM {DB}
            WHERE condition=? AND variable='osmolality' AND compartment='Bath'
            AND segment=? AND nephron=?""",
        [active_scenario, seg, neph]
    )
    if not df_osm.empty and df_osm['avg_osm'].notna().iloc[0]:
        gradient_stops.append({
            "frac": frac,
            "osm": round(float(df_osm['avg_osm'].iloc[0]), 1),
        })

# ============================================================
# 4) Build the JSON package
# ============================================================
injected_data = {
    "solute": solute,
    "con_min": round(con_min, 2),
    "con_max": round(con_max, 2),
    "flow_min": round(flow_min, 2),
    "flow_max": round(flow_max, 2),
    "load_min": round(load_min, 2),
    "load_max": round(load_max, 2),
    "segments": segments_data,
    "flow": flow_data,
    "load": load_data,
    "gradient_stops": gradient_stops,
    "nephron_type": nephron_req,
    "focus": focus,
}

# ============================================================
# 5) Read the D3.js HTML template and inject the data
# ============================================================
html_path = os.path.join(PROJ, "kod", "d3_components", "nephron_diagram.html")
try:
    with open(html_path, "r", encoding="utf-8") as f:
        html_template = f.read()
except FileNotFoundError:
    st.error(f"HTML template not found: {html_path}")
    st.stop()

json_str = json.dumps(injected_data, ensure_ascii=False)
html_rendered = html_template.replace("__INJECTED_DATA__", json_str)

if hasattr(st, "iframe"):
    st.iframe(html_rendered, height=870)
else:  # older Streamlit: the component API that st.iframe replaces
    import streamlit.components.v1 as components
    components.html(html_rendered, height=870, scrolling=False)

# Input note (kept short and understated by design; readers who dig will find it)
st.caption(
    "ℹ The background gradient shows the interstitial osmolality the model is **given** as an "
    "input — it is prescribed, not computed (Layton & Layton 2019, Table 2). Its papillary value "
    "is ~734 mOsm in every scenario; ~1200 mOsm is reported for maximal antidiuresis."
)
