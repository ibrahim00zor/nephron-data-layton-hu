"""nephron_types.py — sup vs jux1-5 comparison."""
import streamlit as st
import plotly.express as px

import nav
import style
from ui_kit import q, DB, figure, options, CD_SEGMENTS, SCENARIO_LABEL, valid_data
from education import segment_info, cite_short

scenario = nav.get("scenario")

st.markdown("## Nephron Types")
st.caption("The superficial nephron against the five juxtamedullary ones, for one solute in one segment. "
           "jux5 descends furthest into the medulla.")

segs, solutes = options()
compare_segs = [s for s in segs if s not in CD_SEGMENTS]

c1, c2, c3 = st.columns(3)
solute = nav.select(c1, "Solute", solutes, "solute", fallback="Na")
segment = nav.select(c2, "Segment", compare_segs, "segment", fallback="PT")
compartment = nav.select(c3, "Compartment", ["Lumen", "Cell", "Bath"], "compartment", fallback="Lumen")

if nav.get("segment") in CD_SEGMENTS:
    st.info(f"`{nav.get('segment')}` is a collecting-duct segment, shared by all nephron types "
            f"(merged), so there is nothing to compare here — showing `{segment}` instead. "
            f"Your selection is unchanged on the other pages.")

df = q(
    f"""SELECT position, value, nephron FROM {DB}
        WHERE condition=? AND variable='con' AND solute=? AND segment=? AND compartment=?
              AND nephron IN ('sup','jux1','jux2','jux3','jux4','jux5')
        ORDER BY nephron, position""",
    [scenario, solute, segment, compartment],
)

df, _ = valid_data(df, "con")

if df.empty:
    st.warning(f"Segment `{segment}` only exists in a single nephron type.")
else:
    color_map = style.NEPHRON_COLOR
    fig = px.line(df, x="position", y="value", color="nephron",
                  title=f"{segment} — {solute} ({compartment}) — by nephron type",
                  labels={"position": "Position (0–1)", "value": f"{solute} (mM)",
                          "nephron": "Nephron"},
                  color_discrete_map=color_map,
                  category_orders={"nephron": ["sup","jux1","jux2","jux3","jux4","jux5"]})
    fig.update_layout(hovermode="x unified", height=480)
    fig.update_traces(line=dict(width=2), hovertemplate="%{y:.4g}")
    figure(fig, caption=f"{solute} along the {segment} ({compartment.lower()}), the superficial nephron "
                        f"against the juxtamedullary ones; {SCENARIO_LABEL.get(scenario, scenario)}")

    with st.expander(f"About {segment} — info and citation"):
        seg = segment_info(segment)
        if seg:
            st.markdown(f"#### {seg.get('full_name', segment)}")
            if seg.get("summary"):
                st.markdown(seg["summary"])
            if seg.get("note"):
                st.info(f"Note: {seg['note']}")
            page = seg.get("source_page") or "?"
            st.caption(f"Source: {cite_short(seg.get('source_key','turkmen2024'), page)}")
