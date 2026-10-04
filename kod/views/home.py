"""home.py — Home: what this is, three places to start, how to find your way, what to keep in mind."""
import streamlit as st
import plotly.express as px

import nav
import nephron_figure
import style
from ui_kit import q, DB, SCENARIO_LABEL, segment_broken

# ============================================================
#  Masthead, with the plate: the nephron of the active scenario
# ============================================================
scenario = nav.get("scenario")


def _plate_values(scenario):
    """Lumen osmolality at the inlet and outlet of each segment: the superficial nephron,
    then the collecting duct. Segments that did not converge are left out."""
    df = q(
        f"""SELECT segment, arg_min(value, position) AS inlet, arg_max(value, position) AS outlet
            FROM {DB}
            WHERE condition=? AND variable='osmolality' AND compartment='Lumen'
                  AND nephron IN ('sup', 'merged')
            GROUP BY segment""",
        [scenario],
    )
    return {row.segment: (row.inlet, row.outlet) for row in df.itertuples()
            if not segment_broken(scenario, row.segment)}


text, figure = st.columns(2, gap="large")
with text:
    st.markdown(
        "<h1>Nephron Data <span class='nd-title-sub'>(Layton/Hu)</span></h1>"
        "<p class='nd-lede'>A mathematical model of the human nephron, laid out so it can be read: "
        "what happens to water and to each solute, segment by segment, in six scenarios.</p>"
        "<div class='nd-byline'>İbrahim Zor · 2026 · "
        "<a href='https://doi.org/10.5281/zenodo.20489610' target='_blank'>doi:10.5281/zenodo.20489610</a> · "
        "<a href='https://github.com/ibrahim00zor/nefron-veri-gezgini' target='_blank'>source on GitHub</a></div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "The numbers come from the epithelial transport model of the Layton group "
        "(Hu, McDonough & Layton 2021, *iScience*), run for a healthy woman and a healthy man, "
        "for moderate diabetes, for hypertension, and for SGLT2 inhibition in each sex. "
        "Nothing here re-implements the model. The app only reads its output and shows it: "
        "the concentration of a solute along a segment, how much of a change is mass and how much "
        "is water, how the scenarios differ, and what each transporter carries."
    )
    st.markdown(
        "<div class='nd-label' style='margin-top:0.6rem;'>In the dataset</div>"
        "<div style='font-size:0.95rem;line-height:1.7;margin-top:0.2rem;'>"
        "6 scenarios · 12 segments · 15 solutes<br>"
        "superficial and five juxtamedullary nephrons<br>"
        "lumen, cell and interstitium<br>"
        "17 transporters, with their fluxes</div>",
        unsafe_allow_html=True,
    )

with figure:
    values = _plate_values(scenario)
    missing = [code for code in nephron_figure.ORDER if code not in values]
    st.markdown(
        "<figure class='nd-plate'>" + nephron_figure.plate(values) +
        "<figcaption><b>Fig. 1.</b> The superficial nephron of the model and the collecting duct it "
        "drains into. The tint and the numbers are the osmolality of the tubular fluid (mOsm) where "
        f"it leaves each segment, in <i>{SCENARIO_LABEL.get(scenario, scenario)}</i>; change the "
        "scenario in the left panel and the figure follows. "
        + (f"{', '.join(missing)} did not converge in this scenario (n.c.). " if missing else "")
        + "Schematic, not to scale; the model has no vasculature, so none is drawn.</figcaption></figure>",
        unsafe_allow_html=True,
    )
    if st.button("Open the interactive drawing →", key="home_plate", width="stretch"):
        nav.go("anatomy", back_label="Fig. 1 on the Home page")

# ============================================================
#  Three places to start — each opens the matching page with its selection applied
# ============================================================
st.markdown("### Three places to start")
st.caption("Each panel is a question the model can answer. The link under it opens the full page "
           "with the same selection already made.")


def _panel_head(letter, what, how):
    st.markdown(
        f"<div class='nd-panel-head'><span class='letter'>{letter}</span><span class='what'>{what}</span>"
        f"<span class='how'>{how}</span></div>",
        unsafe_allow_html=True,
    )


def _panel_chart(df, color, color_map=None, category_orders=None):
    fig = px.line(df, x="position", y="value", color=color, height=190,
                  color_discrete_map=color_map, category_orders=category_orders or {})
    fig.update_layout(margin=dict(l=8, r=48, t=4, b=8), showlegend=False,
                      xaxis_title=None, yaxis_title=None)
    fig.update_traces(line=dict(width=1.8))

    # Each line is named where it ends, instead of in a legend. Names that would collide
    # are moved apart (top to bottom, at least 13 px between them).
    low, high = df["value"].min(), df["value"].max()
    px_per_unit = 150 / ((high - low) or 1)
    previous = None
    for trace in sorted(fig.data, key=lambda t: t.y[-1], reverse=True):
        at = (trace.y[-1] - low) * px_per_unit
        if previous is not None and previous - at < 13:
            at = previous - 13
        previous = at
        fig.add_annotation(x=trace.x[-1], y=trace.y[-1], text=trace.name, showarrow=False,
                           xanchor="left", xshift=5, yshift=at - (trace.y[-1] - low) * px_per_unit,
                           font=dict(size=12.5, color=trace.line.color))
    return fig


a, b, c = st.columns(3, gap="medium")

with a:
    df = q(
        f"""SELECT position, value, condition AS series FROM {DB}
            WHERE variable='con' AND solute='Na' AND segment='mTAL'
                  AND compartment='Lumen' AND nephron='sup'
                  AND condition IN ('F_normal','M_normal')
            ORDER BY condition, position""",
        [],
    )
    df["series"] = df["series"].map({"F_normal": "♀", "M_normal": "♂"})
    _panel_head("a", "Does sex change the thick limb?", "Na⁺ in the mTAL lumen, ♀ and ♂ (mM)")
    st.plotly_chart(_panel_chart(df, "series", {"♀": style.SCENARIO_COLOR["F_normal"],
                                                "♂": style.SCENARIO_COLOR["M_normal"]}), width='stretch')
    if st.button("Open in Comparison →", key="home_q1", width="stretch"):
        nav.go("comparison", back_label="starting point a, sex difference",
               compare=["F_normal", "M_normal"], solute="Na", segment="mTAL",
               nephron="sup", compartment="Lumen")

with b:
    df = q(
        f"""SELECT position, value, condition AS series FROM {DB}
            WHERE variable='con' AND solute='glu' AND segment='PT'
                  AND compartment='Lumen' AND nephron='sup'
                  AND condition IN ('F_normal','F_diab_mod')
            ORDER BY condition, position""",
        [],
    )
    df["series"] = df["series"].map({"F_normal": "normal", "F_diab_mod": "diabetes"})
    _panel_head("b", "What does diabetes do to glucose?", "Glucose in the PT lumen, normal and diabetes (mM)")
    st.plotly_chart(_panel_chart(df, "series", {"normal": style.REFERENCE_SERIES,
                                                "diabetes": style.SCENARIO_COLOR["F_diab_mod"]}),
                    width='stretch')
    if st.button("Open in Comparison →", key="home_q2", width="stretch"):
        nav.go("comparison", back_label="starting point b, diabetes",
               compare=["F_normal", "F_diab_mod"], solute="glu", segment="PT",
               nephron="sup", compartment="Lumen")

with c:
    df = q(
        f"""SELECT position, value, segment FROM {DB}
            WHERE variable='osmolality' AND compartment='Bath' AND nephron='merged'
                  AND condition='F_normal' AND segment IN ('CCD','OMCD','IMCD')
            ORDER BY segment, position""",
        [],
    )
    _panel_head("c", "What is the tubule placed in?",
                "Interstitial osmolality along the collecting duct (mOsm) — a model input")
    st.plotly_chart(_panel_chart(df, "segment", category_orders={"segment": ["CCD", "OMCD", "IMCD"]}),
                    width='stretch')
    if st.button("Open in Whole Nephron →", key="home_q3", width="stretch"):
        nav.go("nephron", back_label="starting point c, the interstitium",
               scenario="F_normal", solute="Na", compartment="Bath", nephron="sup")

# ============================================================
#  Finding your way
# ============================================================
st.markdown("### Finding your way")
left, right = st.columns([3, 2], gap="large")
with left:
    st.markdown(f"""
The menu has two worlds and a back room.

**{nav.MODEL}** is the model itself. *Segment Profile* follows one solute through one segment and
says how much of the change is mass and how much is water. *Whole Nephron* strings the segments
together from proximal tubule to papilla. *Nephron Types* sets the superficial nephron against the
five juxtamedullary ones. *Comparison* overlays scenarios. *Transporters* shows what each transporter
and each pathway carries. *Interactive Anatomy* draws the nephron and colours it with the data.

**{nav.CLINICAL}** holds the clinical cases, each built on one of the scenarios. Its text is still
to be written; the model data behind each case is already there.

**{nav.QUALITY}** is where the model is checked: *Validation* tests the output against physiology,
*Data Integrity* lists what is in the dataset and what did not converge, and *Model & Provenance*
gives the exact command behind every scenario.
""")
with right:
    style.note(
        "Choose a scenario in the left panel, then a solute and a segment on any page. That selection "
        "stays with you: the next page opens on it. A clinical case opens the model pages on its own "
        "scenarios, and a scenario links back to its case.",
        label="The selection travels",
    )

# ============================================================
#  What to keep in mind
# ============================================================
st.markdown("### What to keep in mind")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown(
        "<div class='nd-subhead'>The interstitium is an input</div>\n\n"
        "The composition of the fluid around the tubule is prescribed, not computed: it is specified "
        "at the cortex, at the outer–inner medullary boundary and at the papillary tip, and "
        "interpolated linearly in between (Layton & Layton 2019, Table 2). The ~734 mOsm at the "
        "papillary tip is therefore a setting, the same in all six scenarios, and not a prediction. "
        "It is below the ~1200 mOsm reported for maximal antidiuresis. The model has no vasculature "
        "and does not simulate how the medullary gradient is generated.",
        unsafe_allow_html=True)
with c2:
    st.markdown(
        "<div class='nd-subhead'>Six scenarios out of ten</div>\n\n"
        "Ten scenarios were attempted. Four did not converge in the model's Newton solver and are "
        "not in the dataset: `F_diab_severe`, `F_ACE`, `F_obese`, `F_UNX`. In two of the six that "
        "are, the inner-medullary collecting duct did not converge either; those segments are hidden "
        "rather than drawn. This is a numerical limit of the model.",
        unsafe_allow_html=True)
