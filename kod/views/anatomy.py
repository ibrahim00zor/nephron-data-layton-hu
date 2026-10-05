"""anatomy.py — Interactive anatomy.
The nephron drawn and coloured with the data: colour by concentration or load, thickness by
water flow, the interstitial osmolality as the ground, and the profile along the nephron
beside it. The drawing itself is anatomy_figure.py; this page reads the data for it."""
import streamlit as st

import anatomy_figure
import nav
import nephron_figure
import style
from ui_kit import CD_SEGMENTS, DB, NEPHRONS, SOURCE_NOTE, options, q, segment_broken, segment_names

scenario = nav.get("scenario")

st.markdown("## Interactive Anatomy")
st.caption(
    "The nephron drawn, and coloured with the data. The colour of a segment is the concentration of "
    "the chosen solute, or its load; its thickness is the water flowing through it; and the ground "
    "it is drawn on is the interstitial osmolality the model is given. Point at a segment for its "
    "values, click it to select it. This page is still a beta."
)

# ============================================================
#  What to show (the first four are the shared selection)
# ============================================================
c1, c2, c3, c4 = st.columns(4)
segs, sol = options()
solute = nav.select(c1, "Solute", sol, "solute", fallback="Na")
compartment = nav.select(c2, "Compartment", ["Lumen", "Cell", "Bath"], "compartment", fallback="Lumen")
nephron = nav.select(c3, "Nephron", NEPHRONS, "nephron", fallback="sup",
                     help="The collecting duct (CCD, OMCD, IMCD) is shared by all nephrons and is "
                          "always read from the merged nephron.")
long_loop = str(nephron).startswith("jux")
drawn = anatomy_figure.order(long_loop)
focus = nav.select(c4, "Selected segment", segs, "segment", fallback="PT",
                   help="The segment in your selection. It is marked on the drawing and in the chart, "
                        "and it is the one the other pages open with. A click on the drawing changes it.")

COLOURS = ["concentration", "load (flux)"]


def _keep(name):
    st.session_state[f"_anatomy_{name}"] = st.session_state[f"anatomy_{name}"]


# these two belong to this page only; they are kept for the session, not carried elsewhere
st.session_state["anatomy_colour"] = st.session_state.get("_anatomy_colour", COLOURS[0])
st.session_state["anatomy_flow"] = st.session_state.get("_anatomy_flow", True)
c5, c6 = st.columns([1, 3], vertical_alignment="bottom")
colour = c5.selectbox("Colour shows", COLOURS, key="anatomy_colour", on_change=_keep, args=("colour",),
                      help="The concentration of the solute (mM), or its load: the amount of it that "
                           "flows along the lumen (pmol/min).")
dots = c6.checkbox("Show the flow as moving dots", key="anatomy_flow", on_change=_keep, args=("flow",))
by_load = colour == COLOURS[1]

# ============================================================
#  The data: one read for the tubule, one for the ground
# ============================================================
shared = ", ".join(f"'{code}'" for code in sorted(CD_SEGMENTS))
rows = q(
    f"""SELECT variable, segment, position, value FROM {DB}
        WHERE condition = ?
          AND ((variable = 'con' AND solute = ? AND compartment = ?)
            OR (variable = 'flow' AND solute = ? AND compartment = 'Lumen')
            OR (variable = 'water_volume' AND compartment = 'Lumen'))
          AND ((segment IN ({shared}) AND nephron = 'merged')
            OR (segment NOT IN ({shared}) AND nephron = ?))
        ORDER BY variable, segment, position""",
    [scenario, solute, compartment, solute, nephron],
)


def _thin(positions, values, most=48):
    """A profile for a small chart: about `most` points, the last one always kept."""
    step = max(len(values) // most, 1)
    pairs = list(zip(positions[::step], values[::step]))
    if (len(values) - 1) % step:
        pairs.append((positions[-1], values[-1]))
    return [(round(float(p), 4), float(v)) for p, v in pairs]


def _read(variable, digits):
    """{segment: entry, exit, mean, profile} of one variable; a segment that did not converge,
    or that has a gap, is left out whole."""
    out = {}
    for segment, part in rows[rows["variable"] == variable].groupby("segment", sort=False):
        if part.empty or part["value"].isna().any() or segment_broken(scenario, segment):
            continue
        values = part["value"].tolist()
        out[segment] = {
            "entry": float(values[0]), "exit": float(values[-1]), "mean": float(part["value"].mean()),
            "profile": [(p, round(v, digits)) for p, v in _thin(part["position"].tolist(), values)],
        }
    return out


concentration = _read("con", 4)
if not concentration:
    st.warning("No valid data for the selected filters.")
    st.stop()
# load and water flow are read where there is a concentration to go with them (as before)
load = {code: entry for code, entry in _read("flow", 2).items() if code in concentration}
water = {code: entry for code, entry in _read("water_volume", 4).items() if code in concentration}


def _span(data, low=0.0, high=100.0):
    ends = [v for entry in data.values() for v in (entry["entry"], entry["exit"])]
    return (min(ends), max(ends)) if ends else (low, high)


values = load if by_load else concentration
low, high = _span(values)
flow_low, flow_high = _span(water)
title = f"{solute} load" if by_load else f"{solute} concentration"
unit = "pmol/min" if by_load else "mM"

# The ground: the interstitial osmolality by depth, from the mean of the segments that lie there.
osm = q(
    f"""SELECT segment, nephron, AVG(value) AS osm FROM {DB}
        WHERE condition = ? AND variable = 'osmolality' AND compartment = 'Bath'
              AND nephron IN ('sup', 'merged')
        GROUP BY segment, nephron""",
    [scenario],
)
osm = {(row.segment, row.nephron): row.osm for row in osm.itertuples() if row.osm == row.osm}
DEPTHS = [("PT", "sup", 0.0), ("cTAL", "sup", 0.15), ("S3", "sup", 0.28), ("mTAL", "sup", 0.40),
          ("SDL", "sup", 0.55), ("OMCD", "merged", 0.55), ("IMCD", "merged", 1.0)]
interstitium = [(depth, round(osm[(segment, which)], 1)) for segment, which, depth in DEPTHS
                if (segment, which) in osm]

# ============================================================
#  What a segment says when it is pointed at
# ============================================================
names = segment_names()
cards = {}
for code in drawn:
    card = {"head": code, "name": names.get(code, ""), "hint": "click to select this segment"}
    if code in concentration:
        entry = concentration[code]
        card["rows"] = [("concentration", f"{entry['entry']:.1f} → {entry['exit']:.1f} mM")]
        if code in load:
            card["rows"].append(("load", f"{load[code]['entry']:,.0f} → {load[code]['exit']:,.0f} pmol/min"))
        if code in water:
            card["rows"].append(("water flow", f"{water[code]['mean']:.1f} nl/min (mean)"))
        if code in values:
            card["series"] = [v for _, v in values[code]["profile"]]
            card["hint"] = f"line: {'load' if by_load else 'concentration'} along the segment · click to select"
    elif segment_broken(scenario, code):
        card["rows"] = [("status", "did not converge")]
    else:
        card["rows"] = [("status", "no data for this choice")]
    cards[code] = card

# ============================================================
#  The figure
# ============================================================
links = {code: nav.href(segment=code) for code in drawn}
figure = anatomy_figure.figure(
    drawn, values, low, high, anatomy_figure.VIRIDIS if by_load else anatomy_figure.YL_OR_RD, title, unit,
    {code: entry["mean"] for code, entry in water.items()}, flow_low, flow_high, interstitium,
    links=links, long_loop=long_loop, dots=dots,
)
empty = [code for code in drawn if code not in concentration]
st.markdown(
    anatomy_figure.STYLES
    + "<figure class='nd-plate na-plate'>" + figure + nephron_figure.cards(cards)
    + f"<figcaption><b>Fig. {nav.next_figure()}.</b> The nephron of the model, with {style.inline(title)} "
    f"as colour (from where the fluid enters a segment to where it leaves it) and the water flow as "
    f"thickness. Beside it, the same quantity along the nephron. "
    + (f"{', '.join(empty)} {'has' if len(empty) == 1 else 'have'} no valid data for this choice and "
       f"{'is' if len(empty) == 1 else 'are'} left empty. " if empty else "")
    + f"Schematic, not to scale. <span class='src'>{SOURCE_NOTE}</span></figcaption></figure>",
    unsafe_allow_html=True,
)

# ============================================================
#  The selected segment, read out (a click on the drawing changes only this)
# ============================================================
if focus in drawn:
    width = anatomy_figure.wall(anatomy_figure.thickness(water[focus]["mean"], flow_low, flow_high)
                                if focus in water else anatomy_figure.layout(long_loop)[focus]["width"])
    facts = "".join(f"<tr><td class='key'>{label}</td><td class='num'>{text}</td></tr>"
                    for label, text in cards[focus].get("rows", ()))
    st.markdown(
        f"<div class='nd-reading {nav.changed('anatomy_reading', (scenario, solute, compartment, nephron, focus))}'>"
        f"<span class='nd-label'>Selected on the drawing</span><b>{focus}</b><i>{names.get(focus, '')}</i>"
        f"<span class='nd-side-meta'>{'merged' if focus in CD_SEGMENTS else nephron} nephron</span></div>"
        f"<table class='nd-table' style='max-width:30rem;'><tbody>{facts}</tbody></table>"
        + anatomy_figure.pin(focus, width + 1.2),
        unsafe_allow_html=True,
    )
    row = st.container(horizontal=True, gap="small")
    if row.button("Segment Profile →", key="anatomy_read_seg"):
        nav.go("segment", back_label="the drawing on Interactive Anatomy")
    if row.button("Transporters →", key="anatomy_read_trn"):
        nav.go("transporters", back_label="the drawing on Interactive Anatomy")
else:
    st.caption(f"{focus} is selected, but it is not part of this nephron: the thin limbs (LDL, LAL) exist "
               f"only in the long loop of a juxtamedullary nephron.")

st.markdown(
    "<div class='nd-note'><span class='nd-label'>The ground</span><div class='body'>"
    "The tint behind the drawing is the interstitial osmolality the model is <b>given</b> as an input: "
    "it is prescribed, not computed (Layton &amp; Layton 2019, Table 2). Its papillary value is about "
    "734 mOsm in every scenario; about 1200 mOsm is reported for maximal antidiuresis.</div></div>",
    unsafe_allow_html=True,
)
