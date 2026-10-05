"""transporters.py — Membrane transport fluxes, per pathway and per transporter.

Shows model output that is in the dataset but was not exposed before. Nothing is
interpreted here; units, sign and how they were verified are documented in transport.py
and in the expander at the bottom of the page.
"""
import pandas as pd
import streamlit as st

import nav
import style
import transport as T
from ui_kit import (
    figure, make_chart, neph_for, options, scenario_list,
    NEPHRONS, SCENARIO_COLOR, SCENARIO_LABEL, segment_broken, nephron_phrase,
)

scenario = nav.get("scenario")

st.markdown("## Transporters")
st.caption("What crosses the epithelium in each segment, as the model computes it: the totals for "
           "Na⁺ and K⁺ across the apical membrane and through the tight junction, and the flux through "
           "each transporter. This is model output shown as it is; nothing is interpreted.")

# ------------------------------------------------------------
#  Selection (bound to the shared context)
# ------------------------------------------------------------
all_segments, _ = options()
with_flux = set(T.flux_segments())
segments = [s for s in all_segments if s in with_flux]

c1, c2, c3 = st.columns(3)
segment = nav.select(c1, "Segment", segments, "segment", fallback="PT")
solute = nav.select(c2, "Solute", T.flux_solutes(segment), "solute", fallback="Na")
nephron_req = nav.select(c3, "Nephron", NEPHRONS, "nephron", fallback="sup")
nephron = neph_for(segment, nephron_req)

if nav.get("solute") != solute:
    st.info(f"No exported flux moves `{nav.get('solute')}` in `{segment}`, so `{solute}` is shown here. "
            f"Your selection is unchanged on the other pages.")
if nephron != nephron_req:
    st.info(f"`{segment}` is a collecting-duct segment → nephron automatically **merged**.")

integrable = segment in T.INTEGRABLE
y_label = f"{solute} flux ({T.FLUX_UNIT_LABEL})"
x_label = "Intra-segment position (0 = inlet, 1 = outlet)"


def summary_table(df, group):
    """Inlet / outlet / mean flux density per series, plus the whole-segment total if verified."""
    table = (df.sort_values("position").groupby(group, sort=False)["density"]
               .agg(inlet="first", outlet="last", mean="mean").round(1))
    return table


tab_one, tab_many = st.tabs(["In this scenario", "Across scenarios"])

# ============================================================
#  One scenario: every pathway that moves the solute
# ============================================================
with tab_one:
    if segment_broken(scenario, segment):
        st.warning(f"`{segment}` **failed to converge** numerically in this scenario — data hidden. "
                   f"Pick a clean scenario for this segment (details: Data Integrity page).")
    else:
        df = T.profiles(scenario, segment, nephron, solute)
        df = df[df["value"].notna()]
        if df.empty:
            st.warning(f"No flux data for `{solute}` in `{segment}` of nephron `{nephron}` "
                       f"(LDL/LAL only exist in jux nephrons).")
        else:
            fig = make_chart(df, "position", "density", "pathway",
                             f"{segment} — {solute} fluxes ({nephron}) · {SCENARIO_LABEL.get(scenario, scenario)}",
                             x_label, y_label, color_label="Pathway", height=520, legend_below=True)
            fig.add_hline(y=0, line_dash="dot", opacity=0.35)
            figure(fig, caption=f"What carries {solute} across the epithelium of the {segment} "
                                f"({nephron_phrase(nephron)}), along the segment; "
                                f"{SCENARIO_LABEL.get(scenario, scenario)}",
                   note=f"Flux density in {T.FLUX_UNIT_LABEL} of luminal surface.")

            table = summary_table(df, "pathway")
            if integrable:
                totals = T.segment_totals(scenario, segment, nephron, solute).set_index("pathway")["total"]
                table["whole segment (pmol/min)"] = totals.reindex(table.index).round(1)
            style.table(table, index=True)
            st.caption(f"Inlet, outlet and mean are flux densities, in {T.FLUX_UNIT_LABEL} of luminal surface.")
            if not integrable:
                st.caption(f"No whole-segment total for `{segment}`: it is a coalescing tubule and its "
                           f"intercalated-cell pathways are not exported, so only the flux density is shown.")

            balance = T.mass_balance(scenario, segment, nephron, solute)
            if balance:
                from_fluxes, flow_drop = balance
                ratio = from_fluxes / flow_drop if abs(flow_drop) > 1e-9 else float("nan")
                st.success(
                    f"**Mass balance:** apical + paracellular {solute} flux integrated over the luminal "
                    f"surface = **{from_fluxes:,.1f} pmol/min**; drop in luminal {solute} flow along the "
                    f"segment = **{flow_drop:,.1f} pmol/min** (ratio {ratio:.4f})."
                )

            st.download_button(
                "Download these profiles as CSV",
                df[["pathway", "position", "value", "density"]]
                  .rename(columns={"value": "flux_model_units", "density": "flux_pmol_per_min_cm2"})
                  .to_csv(index=False).encode("utf-8"),
                file_name=f"fluxes_{scenario}_{segment}_{solute}_{nephron}.csv", mime="text/csv",
            )

# ============================================================
#  One pathway across scenarios
# ============================================================
with tab_many:
    all_scenarios = scenario_list()
    selected = nav.multiselect(
        st, "Scenarios to compare", all_scenarios, "compare", fallback=all_scenarios[:2],
        format_func=lambda s: SCENARIO_LABEL.get(s, s),
    )
    broken = [s for s in selected if segment_broken(s, segment)]
    usable = [s for s in selected if s not in broken]
    if broken:
        names = ", ".join(SCENARIO_LABEL.get(s, s) for s in broken)
        st.warning(f"**{names}** did not converge in `{segment}` and is left out.")

    frames = [T.profiles(s, segment, nephron, solute).assign(scenario=s) for s in usable]
    frames = [f for f in frames if not f.empty]
    if not frames:
        st.warning("No flux data for the selected combination.")
    else:
        everything = pd.concat(frames, ignore_index=True)
        everything = everything[everything["value"].notna()]
        pathways = list(dict.fromkeys(everything["pathway"]))
        # open on a specific transporter rather than a pathway total, when there is one
        specific = [p for p in pathways if p not in T.PATHWAY_TOTALS.values()]
        default = specific[0] if specific else pathways[0]
        pathway = st.selectbox("Pathway", pathways, index=pathways.index(default),
                               key=f"transporters_pathway_{segment}_{solute}")
        one = everything[everything["pathway"] == pathway]

        fig = make_chart(one, "position", "density", "scenario",
                         f"{segment} — {pathway} — {solute} ({nephron})",
                         x_label, y_label, color_label="Scenario", height=480,
                         color_map=SCENARIO_COLOR)
        fig.add_hline(y=0, line_dash="dot", opacity=0.35)
        figure(fig, caption=f"{pathway} in the {segment} ({nephron_phrase(nephron)}), {solute}, "
                            f"one line per scenario",
               note=f"Flux density in {T.FLUX_UNIT_LABEL} of luminal surface.")

        table = summary_table(one, "scenario")
        if integrable:
            totals = {}
            for s in table.index:
                per_pathway = T.segment_totals(s, segment, nephron, solute).set_index("pathway")["total"]
                totals[s] = per_pathway.get(pathway, float("nan"))
            table["whole segment (pmol/min)"] = pd.Series(totals).round(1)
            reference = table.index[0]
            base = table.loc[reference, "whole segment (pmol/min)"]
            if base:
                table[f"vs {reference} (%)"] = ((table["whole segment (pmol/min)"] - base) / abs(base) * 100).round(1)
        style.table(table.rename_axis("scenario"), index=True)
        st.caption(f"Inlet, outlet and mean are flux densities, in {T.FLUX_UNIT_LABEL} of luminal surface.")

# ============================================================
#  Reading guide
# ============================================================
with st.expander("Units, sign and how they were verified"):
    st.markdown(f"""
**Units.** The model writes these fluxes in its internal, nondimensional units; they are shown here
as a flux density per unit luminal surface, **{T.FLUX_UNIT_LABEL} = model value × {T.FLUX_UNIT:.0f}**
(href × Cref of the model's nondimensionalisation). The dataset's own unit label for these rows
("pmol/min") is not correct and is not used.

**Verification.** For Na⁺ and K⁺, the apical + paracellular flux integrated over the luminal surface
(π · diameter · length) must equal the drop in luminal flow along the segment. It does: the two agree
to six decimal places in {", ".join(T.CLOSES_EXACTLY)} for every scenario and nephron type, and within
1% in {", ".join(T.CLOSES_WITHIN_1PCT)}. The check for the current selection is shown under the chart.
CNT and the collecting ducts are coalescing tubules whose intercalated-cell pathways are not exported,
so no whole-segment total is given for them.

**Sign.** A flux is positive from the first to the second compartment of its membrane: for an apical
membrane lumen → cell, for a basolateral membrane cell → interstitial side. A negative value means
net movement the other way.

**Pathway totals vs transporters.** *Apical entry* and *Paracellular* are the model's totals for Na⁺
and K⁺ across the apical membrane and the tight junction. The other series are single transporters.
""")
    rows = [(t, ", ".join(m), "apical" if all(T.side(x) == "apical" for x in m)
             else "basolateral" if all(T.side(x) == "basolateral" for x in m) else "apical + basolateral")
            for (seg, t), m in T.MEMBRANES.items() if seg == segment]
    if rows:
        st.markdown(f"**Transporters of `{segment}` and their membranes** (from the model's parameter files)")
        style.table(pd.DataFrame(rows, columns=["transporter", "membrane(s)", "side"]))
        st.caption("Where a transporter sits on several basolateral membranes, the dataset does not keep "
                   "the membrane label, so those profiles are summed (total basolateral flux).")
