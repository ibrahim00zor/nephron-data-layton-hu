"""segment_profile.py — Single segment, single solute profile."""
import streamlit as st

import style
from ui_kit import (
    q, DB, make_chart, figure, neph_for, nephron_phrase, selection, solute_word,
    options, NEPHRON_TYPES, SCENARIO_LABEL, SERIES_WORD, valid_data, segment_broken,
)
from education import segment_info, cite_short
from interpretation import interpret

segs, solutes = options()
chosen = selection(solute=solutes, segment=segs, nephron=NEPHRON_TYPES)
scenario, solute, segment, nephron_req = (chosen[name] for name in ("scenario", "solute", "segment", "nephron"))
nephron = neph_for(segment, nephron_req)
name = solute_word(solute)

st.markdown("## Segment Profile")
st.caption("One solute along one segment, in the lumen and, if you wish, in the interstitium beside it. "
           "Under the chart, the change is split into what is mass and what is water.")
show_bath = st.checkbox("Show the interstitium beside the tubular fluid", value=True)

if nephron != nephron_req:
    st.info(f"The {segment} belongs to the collecting duct, which all nephrons share: there is one of it, "
            f"whatever nephron is selected.")

comps = ["Lumen", "Bath"] if show_bath else ["Lumen"]
df = q(
    f"""SELECT position, value, compartment FROM {DB}
        WHERE condition=? AND variable='con' AND solute=? AND segment=? AND nephron=?
              AND compartment IN ({','.join(['?']*len(comps))})
        ORDER BY position""",
    [scenario, solute, segment, nephron, *comps],
)

seg_broken = segment_broken(scenario, segment)
dropped = 0
if seg_broken:
    df = df.iloc[0:0]          # hide the whole segment (leave no truncated curve)
else:
    df, dropped = valid_data(df, "con")

if df.empty:
    if seg_broken:
        st.warning(f"`{segment}` **failed to converge** numerically in this scenario — data hidden. "
                   f"(Collecting-duct solver error; pick a clean scenario for this segment. "
                   f"Details: Data Integrity page.)")
    else:
        st.warning(f"No data: the {segment} does not exist in {nephron_phrase(nephron)} "
                   f"(the thin limbs, LDL and LAL, exist only in juxtamedullary nephrons).")
else:
    if dropped:
        st.warning(f"{dropped} invalid point(s) (convergence error) hidden; "
                   f"the data shown below is reliable.")
    lumen = df[df.compartment == "Lumen"]
    if not lumen.empty:
        g, c = lumen["value"].iloc[0], lumen["value"].iloc[-1]
        m1, m2, m3 = st.columns(3)
        m1.metric(f"{name} inlet", f"{g:.2f} mM")
        m2.metric(f"{name} outlet", f"{c:.2f} mM", f"{(c-g)/g*100:+.1f} %" if g else None)
        low, high = lumen["value"].min(), lumen["value"].max()
        m3.metric("Range along the segment", f"{low:.2f} – {high:.2f}")

    drawn = df.assign(series=df["compartment"].map(SERIES_WORD).fillna(df["compartment"]))
    fig = make_chart(drawn, "position", "value", "series",
                     f"{segment} — {name}",
                     "Intra-segment position (0 = inlet, 1 = outlet)",
                     f"{name} (mM)", color_label="Compartment",
                     category_orders={"series": [SERIES_WORD["Lumen"], SERIES_WORD["Bath"]]})
    where = "the tubular fluid and the interstitium beside it" if df["compartment"].nunique() > 1 \
        else "the tubular fluid"
    figure(fig, caption=f"{name} along the {segment} of {nephron_phrase(nephron)}, in {where}; "
                        f"{SCENARIO_LABEL.get(scenario, scenario)}")

    # Automatic physiological interpretation
    if len(lumen) >= 2:
        vol_df = q(
            f"""SELECT position, value FROM {DB}
                WHERE condition=? AND variable='water_volume' AND segment=? AND nephron=?
                      AND compartment='Lumen' ORDER BY position""",
            [scenario, segment, nephron],
        )
        if len(vol_df) >= 2:
            note = interpret(
                con_in=float(lumen["value"].iloc[0]),
                con_out=float(lumen["value"].iloc[-1]),
                vol_in=float(vol_df["value"].iloc[0]),
                vol_out=float(vol_df["value"].iloc[-1]),
                solute=solute,
            )
            style.note(note, label="Reading of this profile, mass against volume")

    # Educational content expander
    with st.expander(f"About {segment} — info and citation"):
        seg = segment_info(segment)
        if seg:
            st.markdown(f"#### {seg.get('full_name', segment)}")
            summary = seg.get("summary", "").strip()
            if summary:
                st.markdown(summary)
            else:
                style.pending("The summary of this segment is not written yet.")
            if seg.get("note"):
                st.info(f"Note: {seg['note']}")
            a, b = st.columns(2)
            with a:
                st.markdown("**Apical (lumen)**")
                for t in seg.get("apical", []) or ["—"]:
                    st.markdown(f"- {t}")
            with b:
                st.markdown("**Basolateral (blood)**")
                for t in seg.get("basolateral", []) or ["—"]:
                    st.markdown(f"- {t}")
            page = seg.get("source_page") or "?"
            st.caption(f"Source: {cite_short(seg.get('source_key','turkmen2024'), page)}")

    with st.expander("Download CSV and summary table"):
        summary_tbl = drawn.groupby("series")["value"].agg(["min", "max", "mean"]).round(3)
        style.table(summary_tbl.rename_axis("compartment"), index=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                           file_name=f"{scenario}_{segment}_{solute}_{nephron}.csv",
                           mime="text/csv")
