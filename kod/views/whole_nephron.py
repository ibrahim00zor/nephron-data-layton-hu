"""whole_nephron.py — Chained whole-nephron chart from PT -> IMCD."""
import pandas as pd
import streamlit as st

import style
from ui_kit import (
    q, DB, make_chart, figure, neph_for, selection, solute_word, compartment_word, NEPHRON_TYPES,
    options, SEG_ORDER_SUP, SEG_ORDER_JUX, valid_data, segment_broken, nephron_phrase,
)

segs, solutes = options()
chosen = selection(solute=solutes, nephron=NEPHRON_TYPES, compartment=["Lumen", "Cell", "Bath"])
scenario, solute, nephron, compartment = (chosen[name] for name in ("scenario", "solute", "nephron", "compartment"))
name = solute_word(solute)

st.markdown("## Whole Nephron")
st.caption("One solute followed from the proximal tubule to the papilla, the segments set end to end in "
           "the order the fluid meets them. Dotted lines are segment boundaries; the collecting duct "
           "(CCD, OMCD, IMCD) is shared by all nephrons and is drawn from the merged nephron.")

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
                   f"(the collecting duct did not converge in this scenario; see the note under the selection).")
    full = pd.concat(parts, ignore_index=True)
    fig = make_chart(full, "x", "value", "segment",
                     f"{name} ({compartment_word(compartment)})",
                     "Segment order (flow direction)",
                     f"{name} (mM)", color_label="Segment",
                     category_orders={"segment": order}, height=520)
    for i in range(1, len(order)):
        fig.add_vline(x=i, line_dash="dot", opacity=0.2)
    fig.update_xaxes(tickmode="array",
                     tickvals=[i + 0.5 for i in range(len(order))],
                     ticktext=order)
    figure(fig, caption=f"{name} in the {compartment_word(compartment)} from the proximal tubule to the papilla "
                        f"({nephron_phrase(nephron)}, then the collecting duct), the segments set end to end",
           note="Dotted lines are segment boundaries.")

    with st.expander("Per-segment summary (inlet → outlet)"):
        summary = (full.sort_values(["segment", "x"])
                       .groupby("segment").agg(inlet=("value", "first"),
                                               outlet=("value", "last")).round(2)
                       .reindex(order).dropna())
        summary["ratio"] = (summary["outlet"] / summary["inlet"]).round(2)
        style.table(summary, index=True)
