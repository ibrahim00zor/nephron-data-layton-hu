"""
style.py — How the app looks.

The idea is a printed physiology monograph: ink on paper, a serif for reading, a monospace
for numbers and labels, thin rules instead of boxes, one accent colour, and charts drawn
like journal figures. Colours and fonts of Streamlit's own widgets are set in
.streamlit/config.toml; everything else is here:

- the palette and the colour of each series,
- the Plotly template,
- the stylesheet,
- a few small HTML building blocks (kicker, note, ledger, bibliography entry).
"""
import html
import re
from urllib.parse import quote

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ============================================================
#  Palette
# ============================================================
INK = "#1d1b18"
INK_SOFT = "#3a362f"
MUTED = "#6f685c"
FAINT = "#9a927f"
RULE = "#d6cebc"
RULE_SOFT = "#e6dfcf"
PAPER = "#faf7f0"
PAPER_DEEP = "#f1ecdf"
ACCENT = "#8c2f1b"        # dark brick red — the only accent
GOOD = "#3f5e30"          # a pass mark, used sparingly

GRAPHITE = "#2e2a26"      # the pencil: drawings, rules, the lines of a chart

# The reading face and the counting face: the ones Streamlit ships (see .streamlit/config.toml).
SERIF = "'Source Serif', 'Source Serif 4', Georgia, 'Times New Roman', serif"
MONO = "'Source Code Pro', 'IBM Plex Mono', Menlo, Consolas, monospace"

# Series colours: earthy and print-like, ordered so that neighbours differ clearly.
SERIES = [
    "#8c2f1b",  # brick
    "#27496d",  # slate blue
    "#b0791a",  # ochre
    "#4f6b3a",  # moss
    "#6d3b5e",  # plum
    "#3f7f8c",  # teal
    "#1d1b18",  # ink
    "#c0652a",  # burnt orange
    "#5a7fa3",  # steel
    "#8a8f3a",  # olive
    "#9a5a7a",  # mauve
    "#7a7265",  # warm grey
]

# One colour per scenario, shared by every chart that overlays scenarios:
# female scenarios in warm tones, male scenarios in blue tones.
SCENARIO_COLOR = {
    "F_normal":   "#8c2f1b",
    "F_diab_mod": "#c0652a",
    "F_HT":       "#a8861f",
    "F_SGLT2":    "#7a2f5a",
    "M_normal":   "#27496d",
    "M_SGLT2":    "#3f7f8c",
}

# Superficial nephron against the juxtamedullary ones (a ramp, shallow to deep).
NEPHRON_COLOR = {
    "sup": "#8c2f1b",
    "jux1": "#a9bdd0", "jux2": "#86a3bd", "jux3": "#6388a8", "jux4": "#446c90", "jux5": "#27496d",
}

REFERENCE_SERIES = "#4a463e"   # the baseline in a "case vs normal" chart


# ============================================================
#  Paper and pencil
# ============================================================
# The page is meant to feel like paper that has been drawn on, without pretending:
# - the paper has a tooth (a grain so slight it is felt more than seen);
# - what is DRAWN (the nephron) is drawn by hand: the line wanders a little and is found in
#   two passes, and tone is hatched (see nephron_figure.py);
# - what is MEASURED (the line of a chart) is drawn along a ruler and left exactly as it is.
#
# Every pencil mark on the page (a rule, an underline, a frame, a tick) is a small SVG drawn
# here, with its unevenness in the path itself, and used as a CSS background. Nothing depends
# on the browser applying a filter to the page: in Safari a CSS `filter: url(#...)` on the
# lines of a chart made them disappear (2026-10), so the page uses none.
def _svg_url(svg):
    return 'url("data:image/svg+xml,' + quote(svg, safe="/:=,;'() ") + '")'


# the tooth of the paper: a fine grain, and a much slower unevenness of tone under it
_GRAIN = _svg_url(
    "<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'>"
    "<filter id='g' x='0' y='0' width='100%' height='100%'>"
    "<feTurbulence type='fractalNoise' baseFrequency='0.72 0.86' numOctaves='3' seed='8' stitchTiles='stitch'/>"
    "<feColorMatrix type='matrix' values='0 0 0 0 0.30  0 0 0 0 0.25  0 0 0 0 0.17  0 0 0 0.14 -0.015'/>"
    "</filter><rect width='260' height='260' filter='url(#g)'/></svg>")
_MOTTLE = _svg_url(
    "<svg xmlns='http://www.w3.org/2000/svg' width='900' height='900'>"
    "<filter id='m' x='0' y='0' width='100%' height='100%'>"
    "<feTurbulence type='fractalNoise' baseFrequency='0.006' numOctaves='2' seed='21' stitchTiles='stitch'/>"
    "<feColorMatrix type='matrix' values='0 0 0 0 0.45  0 0 0 0 0.36  0 0 0 0 0.22  0 0 0 0.10 -0.03'/>"
    "</filter><rect width='900' height='900' filter='url(#m)'/></svg>")
PAPER_TEXTURE = f"{_GRAIN}, {_MOTTLE}"


def _tooth(width, height):
    """The grain of graphite for a drawing `width` by `height` (in its own units). The region
    is given outright: a region relative to a nearly flat line would cut the line away."""
    return (f"<filter id='t' filterUnits='userSpaceOnUse' x='0' y='0' width='{width}' height='{height}'>"
            "<feTurbulence type='fractalNoise' baseFrequency='0.5 0.9' numOctaves='2' seed='5'/>"
            "<feColorMatrix type='matrix' values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.5 1.6'/>"
            "<feComposite in='SourceGraphic' operator='in'/></filter>")


def _drawn(width, height, strokes, stretch=True, size=None):
    """A pencil mark as a CSS image. strokes: (path, colour, weight, opacity). With `stretch`
    it follows the shape of the box it is put in; with `size` it has a size of its own."""
    fit = " preserveAspectRatio='none'" if stretch else ""
    own = f" width='{size[0]}' height='{size[1]}'" if size else ""
    body = "".join(f"<path d='{d}' stroke='{colour}' stroke-width='{weight}' opacity='{opacity}'/>"
                   for d, colour, weight, opacity in strokes)
    return _svg_url(
        f"<svg xmlns='http://www.w3.org/2000/svg'{own} viewBox='0 0 {width} {height}'{fit}>"
        f"{_tooth(width, height)}<g filter='url(#t)' fill='none' stroke-linecap='round' "
        f"stroke-linejoin='round'>{body}</g></svg>")


def _rule(colour, weight, upright=False):
    """A line ruled in pencil: straight, with the uneven pressure of graphite. Lying down by
    default; `upright` for a line that runs down the page."""
    if upright:
        return _drawn(6, 1200, [("M3.1,3 C2.7,210 3.5,430 3,650 S2.8,1010 3.2,1197", colour, weight, 1),
                                ("M3.5,60 C3.1,330 3.4,720 2.9,1140", colour, round(weight * 0.55, 2), 0.45)])
    return _drawn(1200, 6, [("M3,3.1 C210,2.7 430,3.5 650,3 S1010,2.8 1197,3.2", colour, weight, 1),
                            ("M60,3.5 C330,3.1 720,3.4 1140,2.9", colour, round(weight * 0.55, 2), 0.45)])


RULE_STRONG = _rule(GRAPHITE, 1.3)
RULE_LIGHT = _rule("#7d7566", 1.05)
RULE_ACCENT = _rule(ACCENT, 1.5)
UPRIGHT_STRONG = _rule(GRAPHITE, 1.3, upright=True)
UPRIGHT_LIGHT = _rule("#7d7566", 1.05, upright=True)
UPRIGHT_ACCENT = _rule(ACCENT, 1.6, upright=True)


def _underline(colour, weight=1.7):
    """The quick line drawn under a title: one stroke, and a shorter, lighter one after it."""
    return _drawn(120, 10, [("M2,5.4 C30,3.7 72,6.5 118,4.3", colour, weight, 1),
                            ("M9,7.5 C42,6.3 80,8 110,6.7", colour, round(weight * 0.55, 2), 0.5)])


UNDERLINE = _underline(ACCENT)                 # under the title of a page
UNDERLINE_SOFT = _underline(GRAPHITE, 1.3)     # under the heading of a section, under the name
# under a link: a single stroke that follows the words
LINK_LINE = _drawn(200, 6, [("M1,3.5 C42,2.3 118,4.5 199,2.9", ACCENT, 1.25, 0.9)])
LINK_LINE_QUIET = _drawn(200, 6, [("M1,3.5 C42,2.3 118,4.5 199,2.9", MUTED, 1.1, 0.8)])
# a ring drawn round a letter; a tick and a cross in a list of checks; the dash before an item
RING = _drawn(24, 24, [("M12.6,3.1 C6.4,2.5 2.5,7.4 3.2,12.7 C3.9,18.7 9.1,21.7 14.3,20.6 "
                        "C19.5,19.5 21.9,14.7 20.8,9.9 C19.9,5.7 15.7,2.9 10.4,4", GRAPHITE, 1.2, 0.9)])
TICK = _drawn(18, 16, [("M2.4,8.8 C4.4,10.4 6,12.4 7.1,14.2 C9.6,9 13.1,4.4 16.4,1.8", GOOD, 1.9, 1)])
CROSS = _drawn(16, 16, [("M3,3.4 C6.6,6.8 9.8,10 13.4,13.2", ACCENT, 1.8, 1),
                        ("M13,2.8 C9.8,6.4 6.6,9.6 2.8,13.4", ACCENT, 1.8, 1)])
DASH = _drawn(20, 8, [("M2,4.6 C7,3.4 13,5 18,3.6", GRAPHITE, 1.7, 0.85)])


def _frame(colour, weight=2.3):
    """A box drawn by hand, for `border-image`: four ruled lines that overshoot where they
    meet, and a lighter second pass on two of them. It has a size of its own (60 x 30 px)
    so that the corners (7 px) stay what they are and only the sides stretch."""
    return _drawn(120, 60, [
        ("M2,4.6 C30,3.2 80,5.4 118,3.8", colour, weight, 1),
        ("M116.2,1.5 C117.4,20 115.4,40 116.6,58.5", colour, weight, 1),
        ("M118.5,56 C85,57.4 35,54.9 1.5,56.6", colour, weight, 1),
        ("M3.8,58.8 C2.6,40 4.8,20 3.6,1.2", colour, weight, 1),
        ("M7,7 C40,5.6 78,7.4 113,6", colour, round(weight * 0.5, 2), 0.4),
        ("M6.2,54 C5.4,38 7,22 6,8", colour, round(weight * 0.5, 2), 0.4),
    ], stretch=False, size=(60, 30))


FRAME = _frame(GRAPHITE)
FRAME_QUIET = _frame("#7d7566", 2.0)
FRAME_ACCENT = _frame(ACCENT, 2.6)


def _hatch(step, opacity):
    """Pencil hatching, as a tile: what a button looks like when it is shaded in."""
    return _svg_url(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{step}' height='{step}'>"
        f"<path d='M-1,{step + 1} L{step + 1},-1 M-1,1 L1,-1 M{step - 1},{step + 1} L{step + 1},{step - 1}' "
        f"stroke='{GRAPHITE}' stroke-width='0.8' opacity='{opacity}'/></svg>")


HATCH = _hatch(7, 0.26)
HATCH_DENSE = _hatch(5, 0.4)

# A small figure is read, not operated: no toolbar over it, no zooming by accident.
QUIET_CHART = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False}

# ============================================================
#  Charts: drawn like figures in a journal
# ============================================================
def _template():
    axis = dict(
        showline=True, linecolor=GRAPHITE, linewidth=1.2,
        ticks="outside", ticklen=4, tickcolor=INK_SOFT,
        tickfont=dict(family=MONO, size=11.5, color=MUTED),
        title=dict(font=dict(family=SERIF, size=13.5, color=INK_SOFT), standoff=10),
        zeroline=False, automargin=True,
    )
    return go.layout.Template(layout=dict(
        font=dict(family=SERIF, size=14, color=INK),
        title=dict(font=dict(family=SERIF, size=15.5, color=INK), x=0, xanchor="left", pad=dict(l=4)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=SERIES,
        xaxis=dict(showgrid=False, **axis),
        yaxis=dict(showgrid=True, gridcolor="rgba(46, 42, 38, 0.13)", gridwidth=1, **axis),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                    font=dict(family=SERIF, size=12.5, color=INK_SOFT),
                    title=dict(font=dict(family=SERIF, size=12.5, color=MUTED))),
        hoverlabel=dict(bgcolor=PAPER, bordercolor=RULE, font=dict(family=MONO, size=12, color=INK)),
        margin=dict(l=56, r=16, t=46, b=46),
    ))


# ============================================================
#  Stylesheet
# ============================================================
CSS = f"""
<style>
/* ---------- page ---------- */
[data-testid="stMainBlockContainer"] {{ max-width: 1120px; padding-top: 0; padding-bottom: 4rem; }}
/* Streamlit's own bar is emptied and let through: the masthead takes its place */
[data-testid="stHeader"] {{ background: transparent !important; pointer-events: none; }}
[data-testid="stHeader"] button, [data-testid="stHeader"] a {{ pointer-events: auto; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ line-height: 1.62; }}
h1 {{ letter-spacing: -0.018em; line-height: 1.08; }}
h2 {{ letter-spacing: -0.012em; }}
h3, h4, h5 {{ letter-spacing: -0.005em; }}
hr {{ border: 0; border-top: 1px solid {RULE}; margin: 1.5rem 0 1.3rem; }}
[data-testid="stCaptionContainer"] {{ color: {MUTED}; }}
[data-testid="stCaptionContainer"] p {{ font-size: 0.92rem; line-height: 1.5; }}

/* the listener for clicks and keys (events.py) draws nothing and takes no room */
[data-testid="stElementContainer"]:has([data-testid^="stBidiComponent"]) {{ display: none; }}

/* ---------- labels and numbers ---------- */
[data-testid="stWidgetLabel"] p {{
  font-family: {MONO}; font-size: 0.7rem; letter-spacing: 0.09em; text-transform: uppercase; color: {MUTED};
}}
[data-testid="stMetricLabel"] p {{
  font-family: {MONO}; font-size: 0.68rem; letter-spacing: 0.09em; text-transform: uppercase; color: {MUTED};
}}
[data-testid="stMetricValue"] {{ font-family: {MONO}; letter-spacing: -0.02em; color: {INK}; }}
[data-testid="stMetricDelta"] {{
  font-family: {MONO}; font-size: 0.8rem; background: transparent; border-radius: 0; padding: 0; color: {MUTED};
}}
[data-testid="stMetricDelta"] svg {{ width: 0.85rem; height: 0.85rem; }}

/* ---------- notices: a rule and a label, not a coloured box ---------- */
[data-testid="stAlertContainer"] {{
  background: transparent; border: 0; border-left: 2px solid {INK_SOFT}; border-radius: 0;
  padding: 0.1rem 0 0.15rem 1rem;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]),
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{ border-left-color: {ACCENT}; }}
[data-testid="stAlertContainer"] p {{ font-size: 0.97rem; line-height: 1.55; }}
[data-testid^="stAlertContent"]::before {{
  display: block; font-family: {MONO}; font-size: 0.66rem; letter-spacing: 0.14em;
  text-transform: uppercase; color: {MUTED}; margin-bottom: 0.15rem;
}}
[data-testid="stAlertContentInfo"]::before {{ content: "Note"; }}
[data-testid="stAlertContentSuccess"]::before {{ content: "Result"; }}
[data-testid="stAlertContentWarning"]::before {{ content: "Caution"; color: {ACCENT}; }}
[data-testid="stAlertContentError"]::before {{ content: "Error"; color: {ACCENT}; }}

/* ---------- buttons ---------- */
[data-testid="stBaseButton-secondary"] {{
  background: transparent; border: 1px solid {INK_SOFT}; color: {INK}; box-shadow: none;
}}
[data-testid="stBaseButton-secondary"]:hover {{ background: {INK}; border-color: {INK}; color: {PAPER}; }}
[data-testid="stBaseButton-secondary"]:hover p {{ color: {PAPER}; }}
[data-testid="stBaseButton-primary"] {{ box-shadow: none; }}
[data-testid="stButton"] button p, [data-testid="stDownloadButton"] button p {{ font-size: 0.95rem; }}

/* ---------- tabs, expanders ---------- */
[data-testid="stTab"] p {{ font-size: 1rem; }}
[data-testid="stExpander"] details {{
  border: 0; border-top: 1px solid {RULE}; border-bottom: 1px solid {RULE}; border-radius: 0; background: transparent;
}}
[data-testid="stExpander"] summary p {{ font-size: 0.97rem; }}
[data-testid="stExpander"] summary:hover p {{ color: {ACCENT}; }}

/* ---------- containers with a border: a ruled frame, not a card ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 0; }}

/* ---------- sidebar ---------- */
[data-testid="stSidebarNavLink"] {{ border-radius: 0; background: transparent; padding-left: 0.6rem; border-left: 2px solid transparent; }}
[data-testid="stSidebarNavLink"]:hover {{ background: transparent; border-left-color: {RULE}; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: transparent; border-left-color: {ACCENT}; }}
[data-testid="stSidebarNavLink"][aria-current="page"] p {{ color: {INK}; font-weight: 600; }}
[data-testid="stSidebarNavLink"] p {{ font-size: 0.98rem; color: {INK_SOFT}; }}
[data-testid="stNavSectionHeader"] p {{
  font-family: {MONO}; font-size: 0.66rem; letter-spacing: 0.14em; text-transform: uppercase; color: {MUTED}; font-weight: 400;
}}
[data-testid="stSidebar"] hr {{ margin: 1rem 0 0.9rem; }}
[data-testid="stPageLink-NavLink"] {{ padding-left: 0; }}
[data-testid="stPageLink-NavLink"]:hover {{ background: transparent; }}
[data-testid="stPageLink-NavLink"] p {{ color: {ACCENT}; text-decoration: underline; text-underline-offset: 3px; }}
[data-testid="stPageLink-NavLink"]:hover p {{ color: {INK}; }}

/* ---------- building blocks ---------- */
.nd-label {{
  font-family: {MONO}; font-size: 0.66rem; letter-spacing: 0.14em; text-transform: uppercase; color: {MUTED};
}}
.nd-lede {{ font-size: 1.22rem; line-height: 1.5; color: {INK_SOFT}; max-width: 44rem; margin: 0.2rem 0 0.9rem; }}
.nd-byline {{ font-family: {MONO}; font-size: 0.78rem; color: {MUTED}; letter-spacing: 0.01em; }}
.nd-byline a {{ color: {ACCENT}; }}
.nd-title-sub {{ font-weight: 400; color: {MUTED}; font-size: 0.6em; letter-spacing: 0; }}

.nd-note {{ border-left: 2px solid {INK_SOFT}; padding: 0.05rem 0 0.1rem 1rem; margin: 0.2rem 0 0.4rem; }}
.nd-note.accent {{ border-left-color: {ACCENT}; }}
.nd-note.accent .nd-label {{ color: {ACCENT}; }}
.nd-note .nd-label {{ display: block; margin-bottom: 0.15rem; }}
.nd-note .body {{ font-size: 0.97rem; line-height: 1.55; }}
.nd-pending {{ color: {MUTED}; font-style: italic; font-size: 0.97rem; margin: 0.1rem 0 0.3rem; }}

.nd-panel-head {{ border-top: 1px solid {INK_SOFT}; padding-top: 0.45rem; }}
.nd-panel-head .letter {{ font-family: {MONO}; font-size: 0.72rem; color: {ACCENT}; margin-right: 0.5rem; }}
.nd-panel-head .what {{ font-weight: 600; }}
.nd-panel-head .how {{
  display: block; color: {MUTED}; font-size: 0.9rem; line-height: 1.4; margin-top: 0.1rem;
  min-height: 2.8em;   /* two lines, so the charts and buttons of neighbouring panels line up */
}}
.nd-subhead {{ border-top: 1px solid {INK_SOFT}; padding-top: 0.45rem; font-weight: 600; margin-bottom: 0.3rem; }}

.nd-cite {{
  font-size: 0.82rem; color: {MUTED}; border-top: 1px solid {RULE}; padding-top: 0.4rem; margin-top: 0.2rem;
  line-height: 1.5;
}}
.nd-cite a {{ color: {MUTED}; }}

.nd-ledger {{ margin: 0.2rem 0 0.6rem; border-bottom: 1px solid {RULE}; }}
.nd-ledger .row {{ border-top: 1px solid {RULE}; }}
.nd-ledger summary, .nd-ledger .cells {{
  display: grid; grid-template-columns: 34% 1fr 1fr auto; column-gap: 0.9rem; align-items: baseline;
  padding: 0.55rem 0;
}}
.nd-ledger summary {{ cursor: pointer; list-style: none; }}
.nd-ledger summary::-webkit-details-marker {{ display: none; }}
.nd-ledger .name {{ font-weight: 600; transition: color 0.15s; }}
.nd-ledger summary .name::after {{
  content: "+"; font-family: {MONO}; font-weight: 400; font-size: 0.78rem; color: {FAINT}; margin-left: 0.45rem;
}}
.nd-ledger details[open] summary .name::after {{ content: "−"; }}
.nd-ledger summary:hover .name {{ color: {ACCENT}; }}
.nd-ledger .value {{ font-family: {MONO}; font-size: 0.88rem; }}
.nd-ledger .target {{ color: {MUTED}; font-size: 0.88rem; }}
.nd-ledger .mark {{ font-family: {MONO}; font-size: 0.8rem; text-align: right; white-space: nowrap; }}
.nd-ledger .mark.pass {{ color: {GOOD}; }}
.nd-ledger .mark.fail {{ color: {ACCENT}; font-weight: 500; }}
.nd-ledger .mark.quiet {{ color: {FAINT}; }}
.nd-ledger .how {{
  margin: 0 0 0.85rem calc(34% + 0.9rem); padding-left: 0.8rem; border-left: 1px solid {RULE};
  color: {INK_SOFT}; font-size: 0.92rem; line-height: 1.5; max-width: 38rem;
}}
.nd-ledger .how a {{ white-space: nowrap; }}

.nd-ref {{ padding-left: 1.5rem; text-indent: -1.5rem; margin: 0.7rem 0; font-size: 0.95rem; line-height: 1.5; }}
.nd-ref .nd-label {{ margin-right: 0.45rem; }}
.nd-ref a {{ font-family: {MONO}; font-size: 0.8rem; }}
.nd-ref .gloss {{ display: block; text-indent: 0; color: {MUTED}; font-size: 0.86rem; font-style: italic; margin-top: 0.1rem; }}

dl.nd-issues {{ margin: 0.3rem 0 0; }}
dl.nd-issues dt {{ border-top: 1px solid {RULE}; padding-top: 0.7rem; font-weight: 600; }}
dl.nd-issues dt .nd-label {{ display: inline-block; min-width: 5.2rem; }}
dl.nd-issues dt .nd-label.done {{ color: {GOOD}; }}
dl.nd-issues dd {{ margin: 0.2rem 0 0.9rem 5.2rem; color: {INK_SOFT}; font-size: 0.95rem; line-height: 1.55; }}
dl.nd-issues code {{ font-size: 0.82rem; }}

figure.nd-plate {{ margin: 1.5rem 0 0; border-top: 1px solid {INK_SOFT}; padding-top: 0.5rem; }}
figure.nd-plate figcaption {{ font-size: 0.84rem; line-height: 1.5; color: {MUTED}; margin-top: 0.5rem; }}
figure.nd-plate figcaption b {{ color: {INK_SOFT}; font-weight: 600; }}

.nd-reading {{
  display: flex; align-items: baseline; gap: 0.55rem; flex-wrap: wrap;
  border-top: 1px solid {INK_SOFT}; padding-top: 0.5rem; margin-top: 0.3rem;
}}
.nd-reading b {{ font-weight: 600; font-size: 1.05rem; color: {ACCENT}; }}
.nd-reading i {{ color: {INK_SOFT}; }}
.nd-reading .nd-side-meta {{ margin-left: auto; }}

.nd-colophon {{
  border-top: 1px solid {INK_SOFT}; padding-top: 0.7rem; margin-top: 2.2rem;
  font-size: 0.84rem; color: {MUTED}; line-height: 1.6;
}}
.nd-colophon b {{ color: {INK_SOFT}; font-weight: 600; }}
.nd-print {{ font-family: {MONO}; font-size: 0.74rem; border-bottom: 1px dotted {FAINT}; cursor: help; }}

/* ---------- terms that explain themselves under the pointer ---------- */
abbr[title] {{ text-decoration: none; border-bottom: 1px dotted {FAINT}; cursor: help; }}

/* ---------- the link beside a title: a pilcrow; a click also copies the address ---------- */
[data-testid="stHeaderActionElements"] a {{
  text-decoration: none; display: inline-block; width: 0; overflow: visible; white-space: nowrap;   /* takes no room in the line */
}}
[data-testid="stHeaderActionElements"] a svg {{ display: none; }}
[data-testid="stHeaderActionElements"] a::after {{
  content: "¶"; font-family: {SERIF}; font-weight: 400; font-size: 0.72em; color: {FAINT};
  margin-left: 0.35rem; transition: color 0.15s;
}}
[data-testid="stHeaderActionElements"] a:hover::after {{ color: {ACCENT}; }}
#nd-flash {{
  position: fixed; left: 50%; bottom: 1.6rem; transform: translate(-50%, 0.6rem); z-index: 1000000;
  background: {INK}; color: {PAPER}; font-family: {MONO}; font-size: 0.74rem; letter-spacing: 0.04em;
  padding: 0.45rem 0.85rem; opacity: 0; transition: opacity 0.2s, transform 0.2s; pointer-events: none;
}}
#nd-flash.on {{ opacity: 1; transform: translate(-50%, 0); }}

/* ---------- the keys card (shown by "?") ---------- */
.nd-keys {{
  display: none; position: fixed; right: 1.4rem; bottom: 1.4rem; width: 20rem; z-index: 999999;
  background: {PAPER}; border: 1px solid {INK_SOFT}; box-shadow: 4px 4px 0 {RULE_SOFT};
  padding: 0.8rem 1rem 0.75rem; text-align: left;
}}
body.nd-keys-on .nd-keys {{ display: block; }}
.nd-keys dl {{
  display: grid; grid-template-columns: 1.5rem 1fr; gap: 0.3rem 0.6rem; margin: 0.55rem 0 0.6rem;
  font-size: 0.88rem; color: {INK}; align-items: baseline;
}}
.nd-keys dt {{
  font-family: {MONO}; font-size: 0.78rem; text-align: center; border: 1px solid {RULE};
  height: 1.4rem; line-height: 1.3rem;
}}
.nd-keys dd {{ margin: 0; line-height: 1.35; }}

/* ---------- a row of small nephrons, one per scenario ---------- */
.nd-six {{ display: flex; flex-wrap: wrap; gap: 0.6rem 1.7rem; margin: 0.5rem 0 1rem; }}
.nd-six figure {{ margin: 0; display: flex; flex-direction: column; align-items: center; }}
.nd-six figcaption {{
  font-family: {MONO}; font-size: 0.68rem; color: {MUTED}; margin-top: 0.35rem; text-align: center; line-height: 1.4;
}}
.nd-six figcaption i {{ display: block; font-style: normal; color: {ACCENT}; }}
.nd-colophon a {{ color: {MUTED}; }}
.nd-where {{ display: flex; gap: 0.9rem; align-items: center; }}
.nd-side-title {{ font-size: 1.12rem; font-weight: 600; line-height: 1.2; margin-bottom: 0.1rem; }}
.nd-side-meta {{ font-family: {MONO}; font-size: 0.72rem; color: {MUTED}; line-height: 1.6; }}
.nd-side-about {{ font-size: 0.9rem; color: {INK_SOFT}; font-style: italic; line-height: 1.45; margin: -0.3rem 0 0.2rem; }}

/* ---------- paper and pencil (see the note at PAPER_TEXTURE) ---------- */
[data-testid="stMain"] {{ background-image: {PAPER_TEXTURE}; background-attachment: local; }}
[data-testid="stSidebarContent"] {{ background-image: {PAPER_TEXTURE}; background-attachment: local; }}


hr {{ border: 0; height: 6px; background: {RULE_LIGHT} center / 100% 6px no-repeat; }}
/* the heads of the three Home panels are as tall as their tallest, so the charts line up */
.nd-panel-head {{ min-height: 6.6rem; }}
.nd-panel-head, .nd-subhead, figure.nd-plate, .nd-reading, .nd-colophon {{
  border-top: 0; background: {RULE_STRONG} top left / 100% 6px no-repeat; padding-top: 0.7rem;
}}
.nd-cite, .nd-ledger .row, dl.nd-issues dt {{
  border-top: 0; background: {RULE_LIGHT} top left / 100% 6px no-repeat;
}}
.nd-cite {{ padding-top: 0.6rem; }}
.nd-ledger .row {{ padding-top: 3px; }}
dl.nd-issues dt {{ padding-top: 0.85rem; }}
.nd-ledger {{ border-bottom: 0; background: {RULE_LIGHT} bottom left / 100% 6px no-repeat; padding-bottom: 5px; }}

/* ---------- the whole page in the hand of the figure ---------- */
/* labels are written the way the figure is annotated: small, italic, in the reading face */
[data-testid="stWidgetLabel"] p, [data-testid="stMetricLabel"] p, [data-testid="stNavSectionHeader"] p,
.nd-label, [data-testid^="stAlertContent"]::before, .nd-card .hint {{
  font-family: {SERIF}; font-style: italic; font-weight: 400; text-transform: none; letter-spacing: 0;
}}
[data-testid="stWidgetLabel"] p {{ font-size: 0.95rem; color: {INK_SOFT}; }}
[data-testid="stMetricLabel"] p, .nd-label {{ font-size: 0.92rem; color: {MUTED}; }}
[data-testid="stNavSectionHeader"] p {{ font-size: 0.92rem; color: {MUTED}; }}
[data-testid^="stAlertContent"]::before {{ font-size: 0.9rem; margin-bottom: 0.05rem; }}
.nd-card .hint {{ font-size: 0.8rem; }}
dl.nd-issues dt .nd-label {{ min-width: 5.2rem; }}

/* a title is underlined, quickly: in red pencil under a page, in graphite under a section */
[data-testid="stMain"] h1 {{
  background: {UNDERLINE} left bottom 0.25rem / 7.4rem 10px no-repeat; padding-bottom: 1.2rem;
}}
[data-testid="stMain"] h2 {{
  background: {UNDERLINE} left bottom 0.35rem / 4.6rem 9px no-repeat; padding-bottom: 1.05rem;
}}
[data-testid="stMain"] h3 {{
  background: {UNDERLINE_SOFT} left bottom 0.45rem / 2.5rem 7px no-repeat;
}}

/* ---------- the masthead: the name, the worlds, the pages of this world ---------- */
[data-testid="stElementContainer"]:has(.nd-masthead) {{
  position: sticky; top: 0; z-index: 900; padding-bottom: 0.3rem;
  background-color: {PAPER}; background-image: {PAPER_TEXTURE};
}}
.nd-masthead {{
  display: flex; align-items: flex-end; justify-content: space-between; gap: 0.4rem 2rem; flex-wrap: wrap;
  padding: 0.95rem 0 0.75rem; background: {RULE_STRONG} left bottom / 100% 6px no-repeat;
}}
body:has([data-testid="stSidebar"][aria-expanded="false"]) .nd-masthead {{ padding-left: 2.6rem; }}
a.nd-nav {{
  text-decoration: none !important; background-image: none !important; color: {INK_SOFT} !important;
  padding-bottom: 7px !important; font-size: 1rem; white-space: nowrap; transition: color 0.15s;
}}
a.nd-nav:hover {{ color: {ACCENT} !important; }}
a.nd-nav.on {{
  color: {INK} !important; font-weight: 600;
  background: {RULE_ACCENT} left bottom / 100% 6px no-repeat !important;
}}
a.nd-brand {{
  display: inline-flex; align-items: center; gap: 0.5rem; color: {INK} !important;
  font-weight: 600; font-size: 1.22rem; letter-spacing: -0.012em; padding-bottom: 0 !important;
}}
a.nd-brand svg {{ width: 30px; height: 30px; flex: none; }}
a.nd-brand span {{ padding-bottom: 6px; background: {UNDERLINE_SOFT} left bottom / 100% 6px no-repeat; }}
a.nd-brand small {{ font-weight: 400; font-size: 0.82rem; color: {MUTED}; letter-spacing: 0; align-self: flex-end;
  padding-bottom: 7px; }}
.nd-worlds {{ display: flex; gap: 0.3rem 1.7rem; flex-wrap: wrap; }}
.nd-pages {{
  display: flex; gap: 0.2rem 1.45rem; flex-wrap: wrap; padding: 0.6rem 0 0.5rem;
  background: {RULE_LIGHT} left bottom / 100% 6px no-repeat;
}}
.nd-pages a.nd-nav {{ font-size: 0.95rem; }}

/* ---------- the selection panel (the sidebar) ---------- */
[data-testid="stSidebarHeader"]::before {{
  content: "The selection"; font-family: {SERIF}; font-style: italic; font-size: 1.02rem; color: {MUTED};
}}

/* ---------- a figure is named under it ---------- */
.nd-figcap {{
  font-size: 0.9rem; line-height: 1.5; color: {INK_SOFT}; margin: -0.5rem 0 0.9rem; max-width: 46rem;
}}
.nd-figcap b {{ font-weight: 600; color: {INK}; padding-bottom: 2px;
  background: {UNDERLINE_SOFT} left bottom / 100% 5px no-repeat; }}
.nd-figcap .src {{ color: {MUTED}; font-style: italic; }}
.nd-figcap code {{ font-size: 0.8rem; }}

/* a link is underlined by hand, the line following the words */
[data-testid="stMarkdownContainer"] a:not([aria-label="Link to heading"]), .nd-byline a,
[data-testid="stPageLink-NavLink"] p {{
  text-decoration: none !important; padding-bottom: 2px;
  background: {LINK_LINE} left bottom / 100% 5px no-repeat;
  -webkit-box-decoration-break: clone; box-decoration-break: clone;
}}
.nd-colophon a, .nd-cite a {{ background-image: {LINK_LINE_QUIET} !important; }}

/* the dash before an item of a list */
[data-testid="stMarkdownContainer"] ul {{ list-style: none; }}
[data-testid="stMarkdownContainer"] ul > li {{ position: relative; }}
[data-testid="stMarkdownContainer"] ul > li::before {{
  content: ""; position: absolute; left: -1.1rem; top: 0.72em; width: 0.66rem; height: 0.3rem;
  background: {DASH} center / 100% 100% no-repeat;
}}

/* a letter that names a panel is ringed; "Fig. 1." is underlined; a check is ticked by hand */
.nd-panel-head .letter {{
  display: inline-block; width: 1.55rem; height: 1.55rem; line-height: 1.5rem; text-align: center;
  margin-right: 0.4rem; font-style: italic; font-family: {SERIF}; font-size: 0.95rem; color: {INK};
  background: {RING} center / 100% 100% no-repeat;
}}
figure.nd-plate figcaption b {{
  padding-bottom: 2px; background: {UNDERLINE_SOFT} left bottom / 100% 5px no-repeat;
}}
.nd-ledger .mark.pass, .nd-ledger .mark.fail {{ padding-left: 1.25rem; }}
.nd-ledger .mark.pass {{ background: {TICK} left 45% / 0.95rem 0.85rem no-repeat; }}
.nd-ledger .mark.fail {{ background: {CROSS} left 50% / 0.8rem 0.8rem no-repeat; }}

/* a field is a line to write on, not a box */
[data-testid="stSelectbox"] div[role="group"], [data-testid="stMultiSelect"] div[role="group"] {{
  background-color: transparent !important; border-color: transparent !important; border-radius: 0 !important;
  box-shadow: none !important;
  background-image: {RULE_STRONG}; background-position: left bottom; background-size: 100% 6px;
  background-repeat: no-repeat;
}}
[data-testid="stSelectbox"] div[role="group"]:hover, [data-testid="stSelectbox"] div[role="group"]:focus-within,
[data-testid="stMultiSelect"] div[role="group"]:hover, [data-testid="stMultiSelect"] div[role="group"]:focus-within {{
  background-image: {RULE_ACCENT};
}}
/* what has been chosen is boxed and lightly shaded */
[data-testid="stMultiSelectTagsContainer"] span[role="group"] > span {{
  background-color: transparent !important; background-image: {HATCH}; color: {INK} !important;
  border: 1px solid rgba(46, 42, 38, 0.55); border-radius: 2px;
}}
[data-testid="stMultiSelectTagsContainer"] span[role="group"] > span * {{ color: {INK} !important; fill: {INK} !important; }}

/* a button is a box drawn by hand; under the pointer it is shaded in */
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {{
  position: relative; background-color: transparent !important; border-color: transparent !important;
  color: {INK} !important; box-shadow: none !important;
}}
[data-testid="stBaseButton-secondary"]::before, [data-testid="stBaseButton-primary"]::before,
[class*="st-key-nd_frame"]::before, [data-testid="stCheckbox"] label > div:first-of-type::before {{
  content: ""; position: absolute; inset: -1px; pointer-events: none;
  border: 7px solid transparent; border-image: {FRAME} 7 / 7px stretch;
}}
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-secondary"]:focus-visible {{
  background-image: {HATCH}; color: {INK} !important;
}}
[data-testid="stBaseButton-secondary"]:hover p {{ color: {INK}; }}
[data-testid="stBaseButton-primary"] {{ background-image: {HATCH_DENSE}; }}
[data-testid="stBaseButton-primary"] p {{ color: {INK}; font-weight: 600; }}
[data-testid="stBaseButton-primary"]::before {{ border-image-source: {FRAME_ACCENT}; }}

/* a framed block (a container given a key that starts with nd_frame) is boxed by hand as well */
[class*="st-key-nd_frame"] {{ position: relative; border-color: transparent !important; }}
[class*="st-key-nd_frame"]::before {{ inset: 0; border-image-source: {FRAME_QUIET}; }}

/* a box to tick */
[data-testid="stCheckbox"] label > div:first-of-type {{
  position: relative; background-color: transparent !important; border-color: transparent !important;
}}
[data-testid="stCheckbox"] label > div:first-of-type::before {{ inset: -3px; border-width: 6px; border-image-width: 6px; }}
[data-testid="stCheckbox"] label > div:first-of-type polyline {{ stroke: {ACCENT} !important; stroke-width: 2.8; }}

/* tabs, folds, notes and the edge of the side panel are ruled in pencil too */
[data-testid="stTabs"] [role="tablist"] {{
  background: {RULE_LIGHT} left bottom / 100% 6px no-repeat; box-shadow: none !important; border: 0 !important;
}}
[data-testid="stTab"][aria-selected="true"] {{ background: {RULE_ACCENT} left bottom / 100% 6px no-repeat; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: {INK}; font-weight: 600; }}
[data-testid="stExpander"] details {{
  border: 0; background: {RULE_LIGHT} left bottom / 100% 6px no-repeat; padding: 0 0 3px;
}}
[data-testid="stExpanderDetails"] {{ border-top: 0 !important; }}
[data-testid="stAlertContainer"], .nd-note {{
  border-left: 0; background: {UPRIGHT_STRONG} left top / 6px 100% no-repeat; padding-left: 1.15rem;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]),
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]), .nd-note.accent {{
  background-image: {UPRIGHT_ACCENT};
}}
.nd-ledger .how {{ border-left: 0; background: {UPRIGHT_LIGHT} left top / 6px 100% no-repeat; padding-left: 0.95rem; }}
[data-testid="stSidebar"] {{ border-right-color: transparent !important; }}
[data-testid="stSidebarContent"] {{
  background-image: {UPRIGHT_LIGHT}, {PAPER_TEXTURE};
  background-position: right top, 0 0, 0 0; background-size: 6px 100%, auto, auto;
  background-repeat: no-repeat, repeat, repeat; background-attachment: local;
}}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
  border-left-color: transparent; background: {UPRIGHT_ACCENT} left center / 6px 78% no-repeat;
}}

/* a table is ruled by hand: words in the reading face, numbers in the counting face */
.nd-scroll {{ overflow-x: auto; margin: 0.2rem 0 0.7rem; }}
table.nd-table {{ width: 100%; border-collapse: collapse; font-size: 0.93rem; }}
table.nd-table th, table.nd-table td {{ border: 0; padding: 0.42rem 1.1rem 0.5rem 0; vertical-align: baseline; text-align: left; }}
table.nd-table th {{ font-style: italic; font-weight: 400; color: {MUTED}; white-space: nowrap; }}
table.nd-table thead tr {{ background: {RULE_STRONG} left bottom / 100% 6px no-repeat; }}
table.nd-table tbody tr {{ background: {RULE_LIGHT} left bottom / 100% 6px no-repeat; }}
table.nd-table tbody tr:hover td {{ color: {ACCENT}; }}
table.nd-table .num {{ text-align: right; font-family: {MONO}; font-size: 0.84rem; white-space: nowrap; }}
table.nd-table th.num {{ font-family: {SERIF}; font-size: 0.93rem; }}
table.nd-table td.key {{ font-weight: 600; white-space: nowrap; }}
table.nd-table td.code {{ font-family: {MONO}; font-size: 0.78rem; color: {INK_SOFT}; word-break: break-word; }}
table.nd-table th:last-child, table.nd-table td:last-child {{ padding-right: 0; }}

/* a chart is drawn on the same sheet: no box of its own under it */
.js-plotly-plot .main-svg {{ background: transparent !important; }}
.js-plotly-plot .main-svg .bg {{ fill: transparent !important; }}

/* the toolbar of a chart stays out of the way until it is wanted */
.js-plotly-plot .modebar {{ opacity: 0.45; }}
.js-plotly-plot .modebar-group {{ background: transparent !important; }}
</style>
"""


def apply():
    """Register the chart template and write the stylesheet (once per run, from app.py)."""
    pio.templates["nephron"] = _template()
    pio.templates.default = "nephron"
    st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
#  Building blocks
# ============================================================
def inline(text):
    """Minimal inline Markdown -> HTML (**bold**, *italic*, `code`), for text placed inside raw HTML."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", out)
    out = re.sub(r"(?<![A-Za-z0-9])_([^_]+)_(?![A-Za-z0-9])", r"<i>\1</i>", out)
    return out


def note(text, label="Note", accent=False):
    """A margin-note style remark: label, rule, text."""
    st.markdown(
        f"<div class='nd-note{' accent' if accent else ''}'><span class='nd-label'>{html.escape(label)}</span>"
        f"<div class='body'>{inline(text)}</div></div>",
        unsafe_allow_html=True,
    )


def pending(text):
    """A place where content is still to be written."""
    st.markdown(f"<div class='nd-pending'>{inline(text)}</div>", unsafe_allow_html=True)


def ledger(rows):
    """A ruled list of checks. rows: (name, value, target, mark, mark_class[, how]).
    With `how` (HTML), the row opens on a click and says how the check is computed."""
    parts = []
    for name, value, target, mark, css, *rest in rows:
        cells = (f"<span class='name'>{html.escape(name)}</span><span class='value'>{html.escape(value)}</span>"
                 f"<span class='target'>{html.escape(target)}</span>"
                 f"<span class='mark {css}'>{html.escape(mark)}</span>")
        if rest and rest[0]:
            parts.append(f"<details class='row'><summary>{cells}</summary>"
                         f"<div class='how'>{rest[0]}</div></details>")
        else:
            parts.append(f"<div class='row'><div class='cells'>{cells}</div></div>")
    st.markdown(f"<div class='nd-ledger'>{''.join(parts)}</div>", unsafe_allow_html=True)


def _cell(value):
    """(text, is a number) for one value of a table."""
    if value is None or (isinstance(value, float) and value != value):
        return "—", True
    if isinstance(value, bool):
        return ("yes" if value else "no"), False
    if isinstance(value, int) or (hasattr(value, "dtype") and getattr(value.dtype, "kind", "") in "iu"):
        return f"{int(value):,}", True
    if isinstance(value, float) or (hasattr(value, "dtype") and getattr(value.dtype, "kind", "") == "f"):
        value = float(value)
        if value == int(value) and abs(value) < 1e15:
            return f"{int(value):,}", True
        text = f"{value:,.1f}" if abs(value) >= 1000 else f"{value:.4f}".rstrip("0").rstrip(".")
        return text, True
    return str(value), False


def table(df, index=False, code=()):
    """A table ruled by hand (HTML). Words are set in serif, numbers in mono and to the right.

    index: show the index as a first, emphasised column.
    code:  columns whose text is code (commands, file names): set small, in mono, and wrapped.
    """
    columns = list(df.columns)
    numeric = {c for c in columns if getattr(df[c].dtype, "kind", "O") in "iuf"}
    head = "".join(f"<th class='{'num' if c in numeric else ''}'>{html.escape(str(c))}</th>" for c in columns)
    if index:
        head = f"<th>{html.escape(str(df.index.name or ''))}</th>" + head
    body = []
    for key, row in zip(df.index, df.itertuples(index=False)):
        cells = [f"<td class='key'>{html.escape(str(key))}</td>"] if index else []
        for column, value in zip(columns, row):
            text, number = _cell(value)
            css = "num" if (number and column in numeric) else ("code" if column in code else "")
            cells.append(f"<td class='{css}'>{html.escape(text)}</td>")
        body.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f"<div class='nd-scroll'><table class='nd-table'><thead><tr>{head}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>",
        unsafe_allow_html=True,
    )
