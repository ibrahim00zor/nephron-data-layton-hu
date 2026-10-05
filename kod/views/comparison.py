"""comparison.py — Multi-scenario overlay.
Shows several scenarios on one chart and produces a difference table."""
import streamlit as st
import plotly.express as px

import nav
import style
from ui_kit import (
    q, DB, figure, neph_for, nephron_phrase, selection, solute_word, compartment_word, scenario_word,
    options, scenario_list, SCENARIO_COLOR, SCENARIO_LABEL, NEPHRON_TYPES, valid_data, segment_broken,
)

all_scenarios = scenario_list()
segs, _ = options()

# The single scenario of the selection is not used here: this page sets several side by side.
chosen = selection(solute=["Na", "K", "Cl", "urea", "glu", "HCO3", "NH3", "NH4"], segment=segs,
                   nephron=NEPHRON_TYPES, compartment=["Lumen", "Cell", "Bath"], scenario=False)
solute, segment, nephron_req, compartment = (chosen[name] for name in ("solute", "segment", "nephron", "compartment"))
nephron = neph_for(segment, nephron_req)
name = solute_word(solute)

st.markdown("## Scenario Comparison")
st.caption("Two to four scenarios on one chart, for one solute in one segment, "
           "with a table of how they differ at the outlet.")

# Multi-scenario selection
selected = nav.multiselect(
    st, "Scenarios to compare (2–4 recommended)", all_scenarios, "compare",
    fallback=all_scenarios[:2],
    format_func=lambda s: SCENARIO_LABEL.get(s, s),
)

if len(selected) < 2:
    st.warning("Pick at least 2 scenarios.")
    st.stop()

# Fetch data
placeholders = ",".join(["?"] * len(selected))
df = q(
    f"""SELECT condition, position, value FROM {DB}
        WHERE condition IN ({placeholders})
              AND variable='con' AND solute=? AND segment=?
              AND compartment=? AND nephron=?
        ORDER BY condition, position""",
    [*selected, solute, segment, compartment, nephron],
)

# Remove scenarios that did not converge in this segment; then the NaN safety net.
broken = [s for s in selected if segment_broken(s, segment)]
if broken:
    df = df[~df["condition"].isin(broken)]
    names = ", ".join(SCENARIO_LABEL.get(s, s) for s in broken)
    st.warning(f"**{names}** **failed to converge** numerically in this segment ({segment}); "
               f"removed from the comparison. Distal/urine is only reliable in clean scenarios.")
df, _ = valid_data(df, "con")

if df.empty:
    st.warning("No valid data for the selected combination (e.g. LDL only in jux nephrons, "
               "or the selected scenarios did not converge in this segment).")
    st.stop()

# in the figure and the table a scenario goes by its name, not by its code
named = df.assign(scenario=df["condition"].map(scenario_word))
fig = px.line(
    named, x="position", y="value", color="scenario",
    title=f"{segment} — {name} ({compartment_word(compartment)})",
    labels={"position": "Position (0 = inlet, 1 = outlet)",
            "value": f"{name} (mM)", "scenario": "Scenario"},
    color_discrete_map={scenario_word(code): colour for code, colour in SCENARIO_COLOR.items()},
    category_orders={"scenario": [scenario_word(code) for code in selected]},
)
fig.update_layout(hovermode="x unified", height=500)
fig.update_traces(line=dict(width=2), hovertemplate="%{y:.4g}")
figure(fig, caption=f"{name} along the {segment} of {nephron_phrase(nephron)} ({compartment_word(compartment)}), "
                    f"one line per scenario")

# ============================================================
#  Difference table — inlet/outlet per scenario and diff vs reference
# ============================================================
st.markdown("### Differences between scenarios")

summary = (df.groupby("condition")
             .agg(inlet=("value", "first"),
                  outlet=("value", "last"),
                  min=("value", "min"),
                  max=("value", "max"))
             .round(2))
summary["change along segment (%)"] = ((summary["outlet"] - summary["inlet"]) / summary["inlet"] * 100).round(1)

# Let the user pick the reference scenario
present = [s for s in selected if s in summary.index]
ref = st.selectbox("Reference scenario (differences are computed against it)",
                   present, format_func=lambda s: SCENARIO_LABEL.get(s, s))
if ref in summary.index:
    ref_outlet = summary.loc[ref, "outlet"]
    summary["outlet vs reference (%)"] = ((summary["outlet"] - ref_outlet) / ref_outlet * 100).round(1)

style.table(summary.rename(index=scenario_word).rename_axis("scenario"), index=True)

# Automatic observation
if len(summary) >= 2 and "outlet vs reference (%)" in summary.columns:
    diffs = summary["outlet vs reference (%)"].abs().sort_values(ascending=False)
    biggest = diffs.index[0] if diffs.iloc[0] > 0 else None
    if biggest and biggest != ref:
        ratio = summary.loc[biggest, "outlet vs reference (%)"]
        st.info(
            f"Against {scenario_word(ref)}, the scenario that differs most is "
            f"{scenario_word(biggest)}: {name} at the outlet of the {segment} is "
            f"**{ratio:+.1f}%** different."
        )

# Download CSV
st.download_button(
    "Download this comparison data as CSV",
    df.to_csv(index=False).encode("utf-8"),
    file_name=f"comparison_{'_vs_'.join(selected)}_{segment}_{solute}.csv",
    mime="text/csv",
)
