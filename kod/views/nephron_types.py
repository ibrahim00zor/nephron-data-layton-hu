"""nephron_types.py — sup vs jux1-5 comparison."""
import streamlit as st
import plotly.express as px

import nav
import style
from ui_kit import (
    q, DB, figure, options, selection, solute_word, compartment_word, CD_SEGMENTS, NEPHRON_TYPES,
    NEPHRON_WORD, SCENARIO_LABEL, valid_data,
)
from education import segment_info, cite_short

segs, solutes = options()
compare_segs = [s for s in segs if s not in CD_SEGMENTS]
chosen = selection(solute=solutes, segment=compare_segs, compartment=["Lumen", "Cell", "Bath"])
scenario, solute, segment, compartment = (chosen[name] for name in ("scenario", "solute", "segment", "compartment"))
name = solute_word(solute)

st.markdown("## Nephron Types")
st.caption("The superficial nephron against the five juxtamedullary ones, for one solute in one segment. "
           "Juxtamedullary 5 descends furthest into the medulla.")

if nav.get("segment") in CD_SEGMENTS:
    st.info(f"The {nav.get('segment')} belongs to the collecting duct, which all nephron types share, "
            f"so there is nothing to compare here: the {segment} is shown instead. "
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
    drawn = df.assign(nephron=df["nephron"].map(NEPHRON_WORD))
    fig = px.line(drawn, x="position", y="value", color="nephron",
                  title=f"{segment} — {name} ({compartment_word(compartment)}) — by nephron type",
                  labels={"position": "Position (0–1)", "value": f"{name} (mM)",
                          "nephron": "Nephron"},
                  color_discrete_map={NEPHRON_WORD[code]: colour for code, colour in style.NEPHRON_COLOR.items()},
                  category_orders={"nephron": [NEPHRON_WORD[code] for code in NEPHRON_TYPES]})
    fig.update_layout(hovermode="x unified", height=480)
    fig.update_traces(line=dict(width=2), hovertemplate="%{y:.4g}")
    figure(fig, caption=f"{name} along the {segment} ({compartment_word(compartment)}), the superficial nephron "
                        f"against the juxtamedullary ones; {SCENARIO_LABEL.get(scenario, scenario)}")

    with st.expander(f"About {segment} — info and citation"):
        seg = segment_info(segment)
        if seg:
            st.markdown(f"#### {seg.get('full_name', segment)}")
            if seg.get("summary"):
                st.markdown(seg["summary"])
            if seg.get("note"):
                st.info(f"Note: {seg['note']}")
            # a source is named for what is written: no summary and no page yet, no source line
            if seg.get("summary", "").strip() and seg.get("source_page"):
                st.caption(f"Source: {cite_short(seg.get('source_key', 'turkmen2024'), seg['source_page'])}")
