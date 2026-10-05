"""3_Nephron_Types.py — sup vs jux1-5 comparison."""
import streamlit as st
import plotly.express as px
from ui_kit import (
    setup_page, render_sidebar, q, DB, cite_footer, options, CD_SEGMENTS, valid_data,
)
from education import segment_info, cite_short

setup_page("Nephron Types")
scenario = render_sidebar()

st.markdown("## Compare Nephron Types")
st.caption("For the same segment + solute + compartment, sup and jux1–5 are overlaid. "
           "Deep nephrons (jux5) descend furthest into the medulla — the gradient arises from them.")

segs, solutes = options()
compare_segs = [s for s in segs if s not in CD_SEGMENTS]

c1, c2, c3 = st.columns(3)
solute = c1.selectbox("Solute", solutes, index=solutes.index("Na"))
segment = c2.selectbox("Segment", compare_segs)
compartment = c3.selectbox("Compartment", ["Lumen", "Cell", "Bath"])

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
    color_map = {"sup": "#dc2626", "jux1": "#93c5fd", "jux2": "#60a5fa",
                 "jux3": "#3b82f6", "jux4": "#2563eb", "jux5": "#1e3a8a"}
    fig = px.line(df, x="position", y="value", color="nephron",
                  title=f"{segment} — {solute} ({compartment}) — by nephron type",
                  labels={"position": "Position (0–1)", "value": f"{solute} (mM)",
                          "nephron": "Nephron"},
                  color_discrete_map=color_map,
                  category_orders={"nephron": ["sup","jux1","jux2","jux3","jux4","jux5"]})
    fig.update_layout(hovermode="x unified", height=480)
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(fig, width='stretch')
    cite_footer()

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
