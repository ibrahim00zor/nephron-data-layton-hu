"""home.py — Home: what this is, the nephron as a figure you can point at, three places to
start, how to find your way, what to keep in mind."""
import streamlit as st
import plotly.express as px

import nav
import nephron_figure
import style
from ui_kit import (
    q, DB, SCENARIO_LABEL, loop_depths, neph_for, scalar, segment_broken, segment_names,
)

scenario = nav.get("scenario")


# ============================================================
#  What the figure needs from the dataset (all direct reads)
# ============================================================
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


def _plate_profiles(scenario):
    """For the cards: the lumen osmolality along each segment (thinned to about fifty points)
    and the lumen Na+ concentration at its two ends."""
    osm = q(
        f"""SELECT segment, position, value FROM {DB}
            WHERE condition=? AND variable='osmolality' AND compartment='Lumen'
                  AND nephron IN ('sup', 'merged')
            ORDER BY segment, position""",
        [scenario],
    )
    sodium = q(
        f"""SELECT segment, arg_min(value, position) AS inlet, arg_max(value, position) AS outlet
            FROM {DB}
            WHERE condition=? AND variable='con' AND solute='Na' AND compartment='Lumen'
                  AND nephron IN ('sup', 'merged')
            GROUP BY segment""",
        [scenario],
    )
    out = {}
    for segment, part in osm.groupby("segment"):
        series = part["value"].tolist()
        step = max(len(series) // 50, 1)
        out[segment] = {"osm": series[::step] + series[-1:]}
    for row in sodium.itertuples():
        out.setdefault(row.segment, {})["na"] = (row.inlet, row.outlet)
    return out


def _plate_loops(scenario):
    """The long loops of the five juxtamedullary nephrons: how deep each reaches (from the
    length the model gives its descending limb) and the lumen osmolality at its bend."""
    bends = q(
        f"""SELECT nephron, arg_max(value, position) AS bend FROM {DB}
            WHERE condition=? AND variable='osmolality' AND compartment='Lumen' AND segment='LDL'
            GROUP BY nephron""",
        [scenario],
    )
    bends = dict(zip(bends["nephron"], bends["bend"]))
    depths = loop_depths()
    return [{"nephron": name, "depth": depths.get(name, (i + 1) / len(nephron_figure.LOOPS)),
             "value": bends.get(name)}
            for i, name in enumerate(nephron_figure.LOOPS)]


def _plate_notes(scenario):
    """What the figure says about the glomerulus and the macula densa."""
    where = "compartment='Lumen' AND nephron='sup'"      # scalar() adds the scenario
    flow = scalar(f"SELECT value FROM {DB} WHERE {where} AND variable='water_volume' "
                  f"AND segment='PT' AND position=0", scenario)
    osm = scalar(f"SELECT value FROM {DB} WHERE {where} AND variable='osmolality' "
                 f"AND segment='PT' AND position=0", scenario)
    sodium = scalar(f"SELECT value FROM {DB} WHERE {where} AND variable='con' AND solute='Na' "
                    f"AND segment='cTAL' AND position=1", scenario)
    notes = {}
    if flow and osm:
        notes["glom"] = f"Fluid enters the proximal tubule at {flow:.0f} nl/min, {osm:.0f} mOsm."
    if sodium:
        notes["md"] = f"Lumen Na⁺ where the cTAL ends: {sodium:.0f} mM."
    return notes


def _plate_cards(values, profiles, loops, notes, names):
    """What each part of the figure says when it is pointed at."""
    entries = {}
    for code in nephron_figure.ORDER:
        entry = {"head": code, "name": names.get(code, ""), "hint": "click to select this segment"}
        pair = values.get(code)
        if pair is None:
            entry["rows"] = [("status", "did not converge")]
        else:
            entry["series"] = profiles.get(code, {}).get("osm")
            entry["rows"] = [("osmolality", f"{pair[0]:.0f} → {pair[1]:.0f} mOsm")]
            sodium = profiles.get(code, {}).get("na")
            if sodium:
                entry["rows"].append(("Na⁺", f"{sodium[0]:.0f} → {sodium[1]:.0f} mM"))
            entry["hint"] = "line: osmolality along the segment · click to select"
        entries[code] = entry
    bends = [(loop["nephron"], f"{loop['value']:.0f} mOsm at the bend")
             for loop in loops if loop.get("value") == loop.get("value") and loop.get("value") is not None]
    entries["loops"] = {"head": "Long loops", "name": "of the five juxtamedullary nephrons",
                        "rows": bends, "hint": "click to compare the nephron types"}
    if notes.get("glom"):
        entries["glom"] = {"head": "Glomerulus", "name": notes["glom"]}
    if notes.get("md"):
        entries["md"] = {"head": "Macula densa", "name": notes["md"]}
    return entries


def _panel_chart(df, color, color_map=None, category_orders=None, right=48):
    fig = px.line(df, x="position", y="value", color=color, height=190,
                  color_discrete_map=color_map, category_orders=category_orders or {})
    fig.update_layout(margin=dict(l=8, r=right, t=4, b=8), showlegend=False,
                      xaxis_title=None, yaxis_title=None)
    fig.update_traces(line=dict(width=1.8), hovertemplate="%{y:.4g}")

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


def _reading(scenario, segment, values, profiles):
    """Across the page, under the figure: the segment in the selection, read out. A click on
    the figure changes the selection, so this is where the figure answers."""
    nephron = nav.get("nephron")
    if segment in nephron_figure.GHOST and not str(nephron).startswith("jux"):
        nephron = "jux5"                         # the thin limbs exist only in a long loop
    elif nephron == "merged":
        nephron = "sup"                          # "merged" is the collecting duct only
    shown = neph_for(segment, nephron)
    name = segment_names().get(segment, "")
    st.markdown(
        f"<div class='nd-reading'><span class='nd-label'>Selected on the figure</span>"
        f"<b>{segment}</b><i>{name}</i><span class='nd-side-meta'>{shown} nephron</span></div>",
        unsafe_allow_html=True,
    )
    chart, facts = st.columns([3, 2], gap="large")
    with chart:
        if segment_broken(scenario, segment):
            style.pending(f"{segment} did not converge in this scenario, so there is no profile to show.")
        else:
            df = q(
                f"""SELECT position, value, compartment AS series FROM {DB}
                    WHERE condition=? AND variable='osmolality' AND segment=? AND nephron=?
                          AND compartment IN ('Lumen', 'Bath')
                    ORDER BY compartment, position""",
                [scenario, segment, shown],
            )
            if df.empty:
                style.pending(f"No profile for {segment} in the {shown} nephron.")
            else:
                df["series"] = df["series"].map({"Lumen": "tubular fluid", "Bath": "interstitium"})
                st.plotly_chart(
                    _panel_chart(df, "series", {"tubular fluid": style.ACCENT,
                                                "interstitium": style.REFERENCE_SERIES}, right=92),
                    width="stretch", key="home_reading_chart", config=style.QUIET_CHART,
                )
                st.markdown(
                    f"<div class='nd-figcap'><b>Fig. {nav.next_figure()}.</b> Osmolality (mOsm) along the "
                    f"{segment}, from where the fluid enters (0) to where it leaves (1). The interstitium "
                    f"is what the model is given. <span class='src'>Model output "
                    f"(Hu, McDonough &amp; Layton 2021).</span></div>",
                    unsafe_allow_html=True,
                )
    with facts:
        pair, sodium = values.get(segment), profiles.get(segment, {}).get("na")
        rows = []
        if pair and shown in ("sup", "merged"):
            rows.append(("osmolality", f"{pair[0]:.0f} → {pair[1]:.0f} mOsm"))
            if sodium:
                rows.append(("Na⁺", f"{sodium[0]:.0f} → {sodium[1]:.0f} mM"))
        if rows:
            st.markdown(
                "<div class='nd-label'>Tubular fluid, inlet → outlet</div><table class='nd-table'><tbody>"
                + "".join(f"<tr><td class='key'>{label}</td><td class='num'>{text}</td></tr>"
                          for label, text in rows) + "</tbody></table>",
                unsafe_allow_html=True,
            )
        st.markdown("<div class='nd-label' style='margin-top:0.5rem;'>Look closer</div>",
                    unsafe_allow_html=True)
        row = st.container(horizontal=True, gap="small")
        if row.button("Segment Profile →", key="home_read_seg"):
            nav.go("segment", back_label="Fig. 1 on the Home page", segment=segment, nephron=nephron)
        if row.button("Transporters →", key="home_read_trn"):
            nav.go("transporters", back_label="Fig. 1 on the Home page", segment=segment, nephron=nephron)
        if row.button("Interactive drawing →", key="home_plate"):
            nav.go("anatomy", back_label="Fig. 1 on the Home page")


# ============================================================
#  Masthead, with the plate: the nephron of the active scenario
# ============================================================
text, figure = st.columns(2, gap="large")
with text:
    st.markdown(
        "<h1>A model of the human nephron, laid out so it can be read</h1>"
        "<p class='nd-lede'>What happens to water and to each solute, segment by segment, "
        "in six scenarios.</p>"
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
    profiles = _plate_profiles(scenario)
    loops = _plate_loops(scenario)
    selected = nav.get("segment")
    missing = [code for code in nephron_figure.ORDER if code not in values]
    # a click on a segment selects it here (the reading below follows, and so does every other
    # page); a click on the long loops opens the comparison of the nephron types
    links = {code: nav.href(segment=code) for code in nephron_figure.ORDER}
    links["loops"] = nav.href("types", segment="LDL")
    st.markdown(
        "<figure class='nd-plate'>"
        + nephron_figure.plate(values, links=links, loops=loops, pinned=selected)
        + nephron_figure.cards(_plate_cards(values, profiles, loops,
                                            _plate_notes(scenario), segment_names()))
        + f"<figcaption><b>Fig. {nav.next_figure()}.</b> The superficial nephron of the model and the "
        "collecting duct it "
        "drains into. The tint and the numbers are the osmolality of the tubular fluid (mOsm) where "
        f"it leaves each segment, in <i>{SCENARIO_LABEL.get(scenario, scenario)}</i>. Point at a part "
        "for its values; click a segment to select it. In hairline: the long loops of the five "
        "juxtamedullary nephrons, to the relative depths the model gives them. "
        + (f"{', '.join(missing)} did not converge in this scenario (n.c.). " if missing else "")
        + "Schematic, not to scale; the model has no vasculature, so none is drawn.</figcaption></figure>",
        unsafe_allow_html=True,
    )

_reading(scenario, selected, values, profiles)

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
                                                "♂": style.SCENARIO_COLOR["M_normal"]}), width='stretch', config=style.QUIET_CHART)
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
    _panel_head("b", "Does diabetes change glucose?", "Glucose in the PT lumen, normal and diabetes (mM)")
    st.plotly_chart(_panel_chart(df, "series", {"normal": style.REFERENCE_SERIES,
                                                "diabetes": style.SCENARIO_COLOR["F_diab_mod"]}),
                    width='stretch', config=style.QUIET_CHART)
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
                    width='stretch', config=style.QUIET_CHART)
    if st.button("Open in Whole Nephron →", key="home_q3", width="stretch"):
        nav.go("nephron", back_label="starting point c, the interstitium",
               scenario="F_normal", solute="Na", compartment="Bath", nephron="sup")

# ============================================================
#  Finding your way
# ============================================================
#  Finding your way
# ============================================================
st.markdown("### Finding your way")
left, right = st.columns([3, 2], gap="large")
with left:
    st.markdown(f"""
The line at the top of every page has two worlds and a back room.

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

*About* says how to cite this, under which licence it is, and where to report an error.
""")
with right:
    style.note(
        "The panel on the left holds what is selected: the scenario, and the solute, segment, "
        "nephron and compartment you last chose on any page. It stays with you: the next page opens "
        "on it, and the address of the page carries it, so a copied address opens the same view. "
        "A clinical case opens the model pages on its own scenarios, and a scenario links back to "
        "its case.",
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
