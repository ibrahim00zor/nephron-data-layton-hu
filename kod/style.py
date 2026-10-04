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

SERIF = "'Source Serif 4', Georgia, 'Times New Roman', serif"
MONO = "'IBM Plex Mono', Menlo, Consolas, monospace"

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
# - what is MEASURED (the line of a chart, a rule) is drawn along a ruler: its position is
#   exact, only its texture is that of graphite. Data is never displaced.
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


def _rule(colour, weight):
    """A line ruled in pencil: straight, but with the grain and the uneven pressure of graphite."""
    return _svg_url(
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 6' preserveAspectRatio='none'>"
        "<filter id='t' x='0' y='0' width='100%' height='100%'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.5 0.9' numOctaves='2' seed='5'/>"
        "<feColorMatrix type='matrix' values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.5 1.55'/>"
        "<feComposite in='SourceGraphic' operator='in'/></filter>"
        f"<g filter='url(#t)' fill='none' stroke='{colour}' stroke-linecap='round'>"
        f"<path d='M3,3.1 C210,2.7 430,3.5 650,3 S1010,2.8 1197,3.2' stroke-width='{weight}'/>"
        f"<path d='M60,3.5 C330,3.1 720,3.4 1140,2.9' stroke-width='{weight * 0.55:.2f}' opacity='0.45'/>"
        "</g></svg>")


RULE_STRONG = _rule(GRAPHITE, 1.25)
RULE_LIGHT = _rule("#8d8573", 1.0)

# Filters the page's own SVG (the charts) can refer to. Written once, with the stylesheet.
DEFS = (
    "<svg xmlns='http://www.w3.org/2000/svg' aria-hidden='true' "
    "style='position:absolute;width:0;height:0;overflow:hidden'><defs>"
    # graphite: erodes a line with the tooth of the paper; it does not move it
    "<filter id='nd-graphite' filterUnits='userSpaceOnUse' x='-80' y='-80' width='2600' height='1700' "
    "color-interpolation-filters='sRGB'>"
    "<feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' seed='7' result='grain'/>"
    "<feColorMatrix in='grain' type='matrix' values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.25 1.5' result='tooth'/>"
    "<feComposite in='SourceGraphic' in2='tooth' operator='in'/></filter>"
    "</defs></svg>"
)

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
        yaxis=dict(showgrid=True, gridcolor=RULE_SOFT, gridwidth=1, griddash="dot", **axis),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                    font=dict(family=SERIF, size=12.5, color=INK_SOFT),
                    title=dict(font=dict(family=MONO, size=10.5, color=MUTED))),
        hoverlabel=dict(bgcolor=PAPER, bordercolor=RULE, font=dict(family=MONO, size=12, color=INK)),
        margin=dict(l=56, r=16, t=46, b=46),
    ))


# ============================================================
#  Stylesheet
# ============================================================
CSS = f"""
<style>
/* ---------- page ---------- */
[data-testid="stMainBlockContainer"] {{ max-width: 1120px; padding-top: 3.6rem; padding-bottom: 4rem; }}
[data-testid="stHeader"] {{ background: {PAPER}; }}
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
/* the wordmark: the mark from st.logo, and the name set beside it in the page's own serif
   (on the Home page the logo sits in a div, elsewhere in a link back to Home) */
[data-testid="stSidebarHeader"] > :first-child {{ display: flex; align-items: center; gap: 0.5rem; }}
[data-testid="stSidebarHeader"] > :first-child::after {{
  content: "Nephron Data"; font-family: {SERIF}; font-weight: 600; font-size: 1.14rem;
  letter-spacing: -0.012em; color: {INK}; white-space: nowrap;
}}
[data-testid="stPageLink-NavLink"] {{ padding-left: 0; }}
[data-testid="stPageLink-NavLink"]:hover {{ background: transparent; }}
[data-testid="stPageLink-NavLink"] p {{ color: {ACCENT}; text-decoration: underline; text-underline-offset: 3px; }}
[data-testid="stPageLink-NavLink"]:hover p {{ color: {INK}; }}

/* ---------- building blocks ---------- */
.nd-kicker {{
  font-family: {MONO}; font-size: 0.68rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: {ACCENT}; margin: 0 0 -0.75rem;
}}
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

/* ---------- paper and pencil (see the note above DEFS) ---------- */
[data-testid="stMain"] {{ background-image: {PAPER_TEXTURE}; background-attachment: local; }}
[data-testid="stSidebarContent"] {{ background-image: {PAPER_TEXTURE}; background-attachment: local; }}
[data-testid="stHeader"] {{ background-image: {PAPER_TEXTURE}; }}

hr {{ border: 0; height: 6px; background: {RULE_LIGHT} center / 100% 6px no-repeat; }}
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

/* a chart is drawn on the same sheet: no box of its own under it */
.js-plotly-plot .main-svg {{ background: transparent !important; }}
.js-plotly-plot .main-svg .bg {{ fill: transparent !important; }}

/* the lines of a chart are graphite: textured, never displaced */
.js-plotly-plot .cartesianlayer .scatterlayer,
.js-plotly-plot .cartesianlayer .xlines-above,
.js-plotly-plot .cartesianlayer .ylines-above {{ filter: url(#nd-graphite); }}
</style>
"""


def apply():
    """Register the chart template and write the stylesheet (once per run, from app.py)."""
    pio.templates["nephron"] = _template()
    pio.templates.default = "nephron"
    st.markdown(CSS + DEFS, unsafe_allow_html=True)


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


def kicker(text):
    """Small label above a page title (the section the page belongs to)."""
    st.markdown(f"<div class='nd-kicker'>{html.escape(text)}</div>", unsafe_allow_html=True)


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
