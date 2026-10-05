"""2_Whole_Nephron.py — Chained whole-nephron chart from PT->IMCD."""
import pandas as pd
import streamlit as st
from ui_kit import (
    setup_page, render_sidebar, q, DB, make_chart, cite_footer, neph_for,
    options, SEG_ORDER_SUP, SEG_ORDER_JUX, valid_data, segment_broken,
)

setup_page("Whole Nephron")
scenario = render_sidebar()

st.markdown("## Along the Whole Nephron")
st.caption("Segments are drawn side by side in physiological order. Vertical dotted lines are segment "
           "boundaries. The collecting duct (CCD/OMCD/IMCD) is under the automatic 'merged' nephron.")

segs, solutes = options()

c1, c2, c3 = st.columns(3)
solute = c1.selectbox("Solute", solutes, index=solutes.index("Na"))
compartment = c2.selectbox("Compartment", ["Lumen", "Cell", "Bath"])
nephron = c3.selectbox("Nephron type", ["sup", "jux1", "jux2", "jux3", "jux4", "jux5"])

order = SEG_ORDER_JUX if nephron.startswith("jux") else SEG_ORDER_SUP
parts = []
skipped = []
for i, seg in enumerate(order):
    if segment_broken(scenario, seg):
        skipped.append(seg)      # not converged -> whole segment removed from the chain
        continue
    eff = neph_for(seg, nephron)
    d = q(
        f"""SELECT position, value FROM {DB}
            WHERE condition=? AND variable='con' AND solute=? AND segment=? AND compartment=? AND nephron=?
            ORDER BY position""",
        [scenario, solute, seg, compartment, eff],
    )
    d, _ = valid_data(d, "con")
    if d.empty:
        continue
    parts.append(d.assign(x=i + d["position"], segment=seg))

if not parts:
    st.warning("No data.")
else:
    if skipped:
        st.warning(f"Non-converged segment(s) removed from the chain: **{', '.join(skipped)}** "
                   f"(the collecting duct is invalid in this scenario; see the side panel).")
    full = pd.concat(parts, ignore_index=True)
    fig = make_chart(full, "x", "value", "segment",
                     f"{nephron} nephron — {solute} ({compartment})",
                     "Segment order (flow direction)",
                     f"{solute} (mM)", color_label="Segment",
                     category_orders={"segment": order}, height=520)
    for i in range(1, len(order)):
        fig.add_vline(x=i, line_dash="dot", opacity=0.2)
    fig.update_xaxes(tickmode="array",
                     tickvals=[i + 0.5 for i in range(len(order))],
                     ticktext=order)
    st.plotly_chart(fig, width='stretch')
    cite_footer()

    with st.expander("Per-segment summary (inlet → outlet)"):
        summary = (full.sort_values(["segment", "x"])
                       .groupby("segment").agg(inlet=("value", "first"),
                                               outlet=("value", "last")).round(2)
                       .reindex(order).dropna())
        summary["ratio"] = (summary["outlet"] / summary["inlet"]).round(2)
        st.dataframe(summary, width='stretch')
