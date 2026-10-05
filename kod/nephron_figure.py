"""
nephron_figure.py — The nephron, drawn once and used three ways.

One hand-placed geometry (a superficial nephron and the collecting duct it drains into,
with the long loops of the juxtamedullary nephrons drawn in hairline below it) gives:

- plate(...)   : the figure on the Home page, tinted and labelled with model output;
- locator(...) : a small map for the sidebar that marks the selected segment;
- mark(...)    : the logo and the favicon.

Everything is plain SVG built as a string. How the drawings look under the pointer is CSS
(`STYLES`, written to the page once by ui_kit.apply_frame). What they do is ordinary links:
every part that can be clicked is an <a class="nd-go"> with a real address (see nav.href),
and events.py answers those links in place. `cards(...)` makes the small cards that
events.py shows beside the pointer.

The plate is drawn the way a pencil study is: the outline is found in two passes (a looser
one under the firmer one), the line wanders slightly, and tone is hatched over a pale wash,
the hatching growing darker with the value. A segment without data keeps a broken outline
and stays empty. The wander and the grain are in the drawing itself (see hand.py): nothing
is filtered by the browser, so nothing has to be worked out again when the pointer moves.

The drawing is a schematic, not anatomy to scale. It follows the layout of the model:
the superficial nephron has a short loop that turns at the outer-inner medullary boundary
(no LDL, no LAL); the collecting duct (CCD, OMCD, IMCD) is shared by all nephrons. The
model has no vasculature, so none is drawn.
"""
import html
import random

from hand import FIRM, LOOSE, tooth
from style import ACCENT, GRAPHITE, INK, INK_SOFT, MONO, MUTED, PAPER, RULE, SERIF

# ============================================================
#  Geometry (SVG user units; y grows downward)
# ============================================================
VIEW = (44, 14, 452, 610)             # x, y, width, height of the plate
CORTEX_END, OUTER_END = 250, 430      # y of the cortex / outer medulla / inner medulla boundaries
GLOMERULUS = (238, 100, 20)           # centre x, centre y, radius of Bowman's capsule
WALL = 2.4                            # twice the thickness of the tubule wall
PAPILLA = 598                         # y where the collecting duct opens


def _catmull(points, before=None, after=None):
    """A smooth path through the points (Catmull-Rom, written as cubic Beziers).
    `before` and `after` only set the direction in which the curve leaves and arrives."""
    pts = [before or points[0]] + list(points) + [after or points[-1]]
    d = [f"M{points[0][0]:g},{points[0][1]:g}"]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:g},{p2[1]:g}")
    return " ".join(d)


_PT = [(221, 100), (202, 84), (184, 100), (164, 82), (144, 96), (134, 120),
       (150, 140), (172, 130), (192, 146), (210, 142), (218, 160)]
_DCT = [(268, 104), (268, 88), (282, 68), (300, 82), (318, 62), (336, 78), (352, 64)]
_CNT = [(352, 64), (370, 60), (384, 72), (388, 92)]

# code -> path, outer width, and the two ends (the tint runs from the first to the second).
# The thick limb starts just before the bend, so the bend is one piece.
SEGMENTS = {
    "PT":   dict(d=_catmull(_PT, before=(238, 100), after=(218, 190)), w=11, ends=((221, 100), (218, 160))),
    "S3":   dict(d="M218,160 L218,250", w=10, ends=((218, 160), (218, 250))),
    "SDL":  dict(d="M218,250 L218,392", w=5, ends=((218, 250), (218, 392))),
    "mTAL": dict(d="M218,392 L218,401 A25,25 0 0 0 268,401 L268,250", w=9, ends=((268, 426), (268, 250))),
    "cTAL": dict(d="M268,250 L268,104", w=9, ends=((268, 250), (268, 104))),
    "DCT":  dict(d=_catmull(_DCT, before=(268, 130), after=_CNT[1]), w=10, ends=((268, 104), (352, 64))),
    "CNT":  dict(d=_catmull(_CNT, before=_DCT[-2], after=(388, 120)), w=9, ends=((352, 64), (388, 92))),
    "CCD":  dict(d="M388,92 L388,250", w=10, ends=((388, 92), (388, 250))),
    "OMCD": dict(d="M388,250 L388,430", w=11, ends=((388, 250), (388, 430))),
    "IMCD": dict(d=f"M388,430 L388,{PAPILLA}", w=13, ends=((388, 430), (388, PAPILLA))),
}
ORDER = list(SEGMENTS)

# The long loops of the juxtamedullary nephrons hang below the short one: same axis, wider
# and deeper from jux1 to jux5. `depth` (0-1) is how far into the inner medulla a loop reaches.
LOOP_AXIS, LOOP_TOP, LOOP_REACH = 243, 436, 140
LOOPS = ("jux1", "jux2", "jux3", "jux4", "jux5")
GHOST = ("LDL", "LAL")                # the two limbs of a long loop


def _loop(half_width, depth):
    """The two limbs of a long loop: (descending, ascending), meeting at the bend."""
    left, right = LOOP_AXIS - half_width, LOOP_AXIS + half_width
    turn = LOOP_TOP + max(depth, 0.08) * LOOP_REACH - half_width
    turn = max(turn, LOOP_TOP + 2)
    bottom = turn + half_width
    return (f"M{left:g},{LOOP_TOP} L{left:g},{turn:g} A{half_width:g},{half_width:g} 0 0 0 {LOOP_AXIS},{bottom:g}",
            f"M{LOOP_AXIS},{bottom:g} A{half_width:g},{half_width:g} 0 0 0 {right:g},{turn:g} L{right:g},{LOOP_TOP}")


def _half_width(index, count):
    """Loops are nested: the shallowest is the narrowest."""
    return 22 - 4 * (count - 1 - index)


# code -> where its label sits: x, y, text-anchor
LABELS = {
    "PT":   (124, 124, "end"),
    "S3":   (207, 212, "end"),
    "SDL":  (209, 344, "end"),
    "mTAL": (279, 344, "start"),
    "cTAL": (279, 192, "start"),
    "DCT":  (310, 48, "middle"),
    "CNT":  (368, 46, "start"),
    "CCD":  (400, 176, "start"),
    "OMCD": (401, 344, "start"),
    "IMCD": (402, 520, "start"),
}

# ============================================================
#  Tint: a value on a paper-to-brick scale
# ============================================================
SCALE = [(80.0, "#f8f3e7"), (300.0, "#e6c49a"), (750.0, ACCENT)]   # (value, colour) stops


def _mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    parts = [round(int(a[i:i + 2], 16) + (int(b[i:i + 2], 16) - int(a[i:i + 2], 16)) * t) for i in (0, 2, 4)]
    return "#" + "".join(f"{p:02x}" for p in parts)


def tint(value):
    """Colour of a value on SCALE (clamped at both ends)."""
    if value <= SCALE[0][0]:
        return SCALE[0][1]
    for (v0, c0), (v1, c1) in zip(SCALE, SCALE[1:]):
        if value <= v1:
            return _mix(c0, c1, (value - v0) / (v1 - v0))
    return SCALE[-1][1]


def _level(value):
    """Grey level (for a mask) of the hatching at a value: white is full hatching, black none."""
    lo, hi = SCALE[0][0], SCALE[-1][0]
    t = min(max((value - lo) / (hi - lo), 0.0), 1.0)
    g = round(255 * (0.05 + 0.95 * t))
    return f"rgb({g},{g},{g})"


def _usable(pair):
    """A (inlet, outlet) pair that can be drawn: both present, finite and not negative."""
    if not pair:
        return False
    return all(v is not None and v == v and v >= 0 for v in pair)


def _number(value):
    return value is not None and value == value and value >= 0


# ============================================================
#  How the drawings look under the pointer (CSS, written to the page once)
# ============================================================
HOT = list(SEGMENTS) + ["loops", "glom", "md"]      # everything on the plate that can be pointed at


def _styles():
    rules = [f"""
/* ---------- the plate ---------- */
.nd-plate {{ position: relative; }}
.nd-plate a {{ text-decoration: none; cursor: pointer; }}
.nd-plate .nd-hot {{ cursor: help; }}
.nd-plate [data-part], .nd-plate .nd-wall, .nd-plate .nd-code {{
  transition: opacity .18s ease-out, stroke .18s ease-out, stroke-width .18s ease-out, fill .18s ease-out;
}}
.nd-plate .nd-mark {{ opacity: 0; transition: opacity .18s ease-out; pointer-events: none; }}
.nd-plate [data-seg]:hover .nd-code {{ fill: {ACCENT}; }}
/* What is under the pointer is named on the drawing by events.py (data-hot), and on the
   small map in the sidebar. While something is pointed at, the rest of the tubule steps back. */
.nd-plate svg[data-hot] [data-part] {{ opacity: 0.28; }}
.nd-plate .nd-ghost {{ transition: opacity .18s ease-out; }}
.nd-plate svg[data-hot] .nd-ghost {{ opacity: 0.08; }}
/* A segment that has just been clicked is marked at once (data-pick), until the page answers. */
.nd-plate svg[data-pick] .nd-wall {{ stroke: {GRAPHITE}; }}
.nd-plate svg[data-pick] tspan.nd-code {{ fill: {INK}; }}
.nd-where a {{ cursor: pointer; }}
.nd-where .nd-loc {{ transition: stroke .15s; }}
.nd-where a:hover .nd-loc {{ stroke: {ACCENT}; }}

/* the card beside the pointer (placed by events.py) */
.nd-card {{
  position: fixed; left: 0; top: 0; z-index: 999990; pointer-events: none; width: 15.5rem;
  visibility: hidden; opacity: 0; transition: opacity .12s ease-out, visibility 0s linear .12s;
  background: {PAPER}; border: 1px solid {INK_SOFT}; box-shadow: 3px 3px 0 rgba(29, 27, 24, 0.10);
  padding: 0.55rem 0.7rem 0.5rem; font-family: {SERIF}; color: {INK}; text-align: left;
}}
.nd-card.on {{ visibility: visible; opacity: 1; transition: opacity .12s ease-out; will-change: transform; }}
.nd-card .head {{ font-weight: 600; font-size: 1rem; line-height: 1.2; }}
.nd-card .name {{ font-style: italic; color: {MUTED}; font-size: 0.86rem; line-height: 1.3; margin-bottom: 0.3rem; }}
.nd-card dl {{ display: grid; grid-template-columns: auto 1fr; gap: 0.05rem 0.6rem; margin: 0.25rem 0 0.1rem; }}
.nd-card dt {{ font-size: 0.8rem; color: {MUTED}; }}
.nd-card dd {{ margin: 0; font-family: {MONO}; font-size: 0.76rem; color: {INK}; text-align: right; }}
.nd-card svg {{ display: block; margin: 0.3rem 0 0.1rem; }}
.nd-card .hint {{
  font-family: {SERIF}; font-style: italic; font-size: 0.8rem; line-height: 1.35;
  color: {MUTED}; margin-top: 0.35rem; border-top: 1px solid {RULE}; padding-top: 0.3rem;
}}

/* the plate is drawn in, in the order the fluid meets the segments */
@keyframes nd-draw {{ from {{ stroke-dashoffset: 1; opacity: 0; }} 8% {{ opacity: 1; }} to {{ stroke-dashoffset: 0; opacity: 1; }} }}
@keyframes nd-fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.nd-plate .nd-draw {{ stroke-dasharray: 1; animation: nd-draw .5s ease-out backwards; }}
.nd-plate .nd-fade {{ animation: nd-fade .5s ease-out backwards; }}
@media (prefers-reduced-motion: reduce) {{
  .nd-plate .nd-draw, .nd-plate .nd-fade {{ animation: none; }}
}}"""]
    named = list(SEGMENTS) + list(GHOST)        # every segment of the model (the thin limbs too)
    for code in named:
        rules.append(f".nd-plate svg[data-pick='{code}'] .nd-wall[data-part='{code}'] {{ stroke: {ACCENT}; }}\n"
                     f".nd-plate svg[data-pick='{code}'] [data-seg='{code}'] .nd-code {{ fill: {ACCENT}; }}")
    for code in HOT + list(GHOST):
        here = f".nd-plate svg[data-hot='{code}']"
        rules.append(f"{here} [data-part='{code}'] {{ opacity: 1; }}\n"
                     f"{here} .nd-wall[data-part='{code}'] {{ stroke: {ACCENT}; }}\n"
                     f"{here} [data-for='{code}'] {{ opacity: 1; }}")
    for code in named:
        rules.append(f".nd-where[data-hot='{code}'] [data-loc='{code}'] {{ stroke: {ACCENT}; }}")
    rules.append(f".nd-where[data-hot='loops'] [data-loop] {{ stroke: {ACCENT}; }}")
    return "<style>" + "\n".join(rules) + "</style>"


STYLES = _styles()


# ============================================================
#  Pieces shared by the drawings
# ============================================================
# A wide, invisible stroke over a line: the area that can be pointed at and clicked.
_HIT = "fill='none' stroke='transparent' pointer-events='stroke'"
REACH = 30      # width of that area around a segment of the plate


# The tubule is one line: each segment is drawn so that it meets the next without a corner.
_DRAWN = {hand: dict(zip(SEGMENTS, hand.chain([seg["d"] for seg in SEGMENTS.values()])))
          for hand in (FIRM, LOOSE)}


def _firm(code):
    """The path of a segment as the firm pass draws it."""
    return _DRAWN[FIRM][code]


def _tube(code, pair, delay=None):
    """One segment: its outline, the paper inside it, and its tone (a pale wash and hatching
    over it). Returns (outline, paper, tone, hatching); without data the outline is broken
    and there is no tone. The path itself is written once (as #nd-p-<code>) and used by
    every layer but the outline, which is drawn in and needs a length of its own."""
    seg, known = SEGMENTS[code], _usable(pair)
    drawn = delay is not None and known          # a broken outline is not drawn in
    draw = f" pathLength='1' class='nd-wall nd-draw' style='animation-delay:{delay:.2f}s'" \
        if drawn else " class='nd-wall'"
    fade = f" class='nd-fade' style='animation-delay:{delay + 0.3:.2f}s'" if drawn else ""
    broken = "" if known else " stroke-dasharray='5 3.5'"
    inner = f"href='#nd-p-{code}' fill='none' stroke-width='{seg['w'] - WALL:g}' stroke-linejoin='round'"
    outline = (f"<path d='{_firm(code)}' data-part='{code}' fill='none' stroke='{GRAPHITE}' "
               f"stroke-width='{seg['w']:g}' "
               f"stroke-linecap='{'round' if known else 'butt'}' stroke-linejoin='round'{broken}{draw}/>")
    paper = f"<use {inner} stroke='{PAPER}'/>"
    if not known:
        return outline, paper, "", ""
    tone = f"<use {inner} data-part='{code}' stroke='url(#nd-t-{code})' opacity='0.62'{fade}/>"
    hatching = f"<use {inner} data-part='{code}' stroke='url(#nd-hatch)' mask='url(#nd-m-{code})'{fade}/>"
    return outline, paper, tone, hatching


def _hatch():
    """The hatching: lines a little over three units apart, drawn with a pressure that is
    not even along them (three lines to a tile, each in pieces of its own)."""
    rng = random.Random(52)
    gap, tall = 3.3, 26.0
    lines = []
    for column in range(3):
        x, y = gap * (column + 0.5), 0.0
        while y < tall:
            length = min(rng.uniform(3.0, 7.5), tall - y)
            lines.append(f"<line x1='{x:g}' y1='{y:.1f}' x2='{x:g}' y2='{y + length:.1f}' stroke='{GRAPHITE}' "
                         f"stroke-width='0.8' opacity='{rng.uniform(0.58, 1.0):.2f}'/>")
            y += length
    return (f"<pattern id='nd-hatch' width='{3 * gap:g}' height='{tall:g}' patternUnits='userSpaceOnUse' "
            f"patternTransform='rotate(52)'>{''.join(lines)}</pattern>")


def _glomerulus(fill):
    cx, cy, r = GLOMERULUS
    tuft = "".join(
        f"<path d='{FIRM.circle(cx + dx, cy + dy, 6.4)}' fill='{PAPER}' stroke='{GRAPHITE}' stroke-width='0.8'/>"
        for dx, dy in ((-6, -5), (5, -7), (8, 4), (-2, 8), (-9, 3), (0, 0))
    )
    capsule = FIRM.circle(cx, cy, r)
    return (f"<g data-part='glom'><path d='{capsule}' fill='{PAPER}'/>"
            f"<path d='{capsule}' class='nd-wall' data-part='glom' "
            f"fill='{fill}' fill-opacity='0.62' stroke='{GRAPHITE}' stroke-width='1.2'/>{tuft}</g>")


def _link(href, body, attrs=""):
    """Wrap in a link when there is one to follow, in a plain group otherwise."""
    if href:
        return f"<a class='nd-go' href='{html.escape(href, quote=True)}' target='_self' {attrs}>{body}</a>"
    return f"<g {attrs}>{body}</g>"


# ============================================================
#  The plate (Home page)
# ============================================================
def plate(values, unit="mOsm", links=None, loops=None, animate=True):
    """The annotated figure.

    values: {segment code: (inlet, outlet)}; a missing or unusable pair is drawn hatched
            and labelled "n.c." (not converged). The label of a segment is its outlet value.
    links:  {segment code, or "loops": href}, followed on a click.
    loops:  the long loops, shallowest first: [{"nephron", "depth" (0-1), "value" (at the bend)}].
            Without it one loop is drawn at full depth.
    animate: draw the figure in, stroke by stroke (the first time it is shown).

    Neither what a part says when it is pointed at nor which segment is selected is in the
    figure: see cards() and pin(). The figure of a scenario is therefore always the same
    text, and a page that shows it again has nothing new to send or to lay out.
    """
    links = links or {}
    loops = loops if loops is not None else [{"nephron": LOOPS[-1], "depth": 1.0, "value": None}]
    x0, y0, w, h = VIEW
    right = x0 + w
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{x0} {y0} {w} {h}' role='img' "
           f"aria-label='Schematic of the nephron with model output per segment' "
           f"style='width:100%;height:auto;display:block;'>"]

    # ---- definitions: the tone of each segment, the hatch, the open end, the pencil
    lo, hi = SCALE[0][0], SCALE[-1][0]
    area = f"x='{x0}' y='{y0}' width='{w}' height='{h}'"
    out.append("<defs>")
    for code, seg in SEGMENTS.items():
        if _usable(values.get(code)):
            (x1, y1), (x2, y2) = seg["ends"]
            a, b = values[code]
            along = f"gradientUnits='userSpaceOnUse' x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}'"
            out.append(f"<linearGradient id='nd-t-{code}' {along}>"
                       f"<stop offset='0' stop-color='{tint(a)}'/><stop offset='1' stop-color='{tint(b)}'/>"
                       f"</linearGradient>")
            # the hatching is let through in proportion to the value, from inlet to outlet
            out.append(f"<linearGradient id='nd-g-{code}' {along}>"
                       f"<stop offset='0' stop-color='{_level(a)}'/><stop offset='1' stop-color='{_level(b)}'/>"
                       f"</linearGradient>")
            out.append(f"<mask id='nd-m-{code}' maskUnits='userSpaceOnUse' {area}>"
                       f"<rect {area} fill='url(#nd-g-{code})'/></mask>")
    stops = "".join(f"<stop offset='{(v - lo) / (hi - lo):.3f}' stop-color='{c}'/>" for v, c in SCALE)
    out.append(f"<linearGradient id='nd-t-scale' x1='0' y1='0' x2='1' y2='0'>{stops}</linearGradient>")
    out.append(f"<linearGradient id='nd-g-scale' x1='0' y1='0' x2='1' y2='0'>"
               f"<stop offset='0' stop-color='{_level(lo)}'/><stop offset='1' stop-color='{_level(hi)}'/>"
               f"</linearGradient>")
    out.append("<mask id='nd-m-scale' maskContentUnits='objectBoundingBox'>"
               "<rect width='1' height='1' fill='url(#nd-g-scale)'/></mask>")
    out.append(_hatch())
    out.append(f"<clipPath id='nd-t-open'><rect x='{x0}' y='{y0}' width='{w}' height='{PAPILLA - y0}'/></clipPath>")
    # the tooth of the paper, and the path of each segment as the firm pass draws it
    out.append(tooth(PAPER))
    out += [f"<path id='nd-p-{code}' d='{_firm(code)}'/>" for code in SEGMENTS]
    out.append("</defs>")

    # ---- zones: ruled in pencil, named quietly
    zone = f"font-family=\"{SERIF}\" font-style='italic' font-size='10.5' fill='{MUTED}'"
    for y, name in ((y0, "cortex"), (CORTEX_END, "outer medulla"), (OUTER_END, "inner medulla")):
        if y != y0:
            out.append(f"<path d='{LOOSE.line(x0 + 4, y, right - 4, y + 1.2)}' fill='none' "
                       f"stroke='{GRAPHITE}' stroke-width='0.7' opacity='0.42'/>")
        out.append(f"<text x='{x0 + 6}' y='{y + 15}' {zone}>{name}</text>")

    # ---- the drawing. Outlines first, then the glomerulus, then the lumens on top, so that
    # every joint is open and the capsule opens into the proximal tubule. The duct is left
    # open at the papilla (the outlines are clipped there).
    outlines, papers, tones, hatchings = [], [], [], []
    for index, code in enumerate(ORDER):
        parts = _tube(code, values.get(code), delay=0.15 + 0.2 * index if animate else None)
        for group, part in zip((outlines, papers, tones, hatchings), parts):
            group.append(part)
    known = [code for code in ORDER if _usable(values.get(code))]
    line = f"fill='none' stroke='{GRAPHITE}' stroke-linecap='round' stroke-linejoin='round'"
    grain = "fill='none' stroke='url(#nd-tooth)' stroke-linecap='round' stroke-linejoin='round'"
    # the looser pass: the line as it was first looked for
    loose = "".join(f"<path d='{_DRAWN[LOOSE][code]}' {line} stroke-width='{SEGMENTS[code]['w']}'/>"
                    for code in known)
    out.append(f"<g class='nd-ghost' opacity='0.3' clip-path='url(#nd-t-open)'>{loose}</g>")
    # the firm pass, and over it the tooth of the paper (specks of paper on the graphite)
    for index, loop in enumerate(loops):
        for d in _loop(_half_width(index, len(loops)), loop["depth"]):
            out.append(f"<path d='{FIRM.path(d, 4.0, 14.0)}' data-part='loops' class='nd-wall' fill='none' "
                       f"stroke='{GRAPHITE}' stroke-opacity='0.5' stroke-width='0.85'/>")
    specks = "".join(f"<use href='#nd-p-{code}' {grain} stroke-width='{SEGMENTS[code]['w'] + 0.8:g}'/>"
                     for code in known)
    out.append(f"<g clip-path='url(#nd-t-open)'>{''.join(outlines)}{specks}</g>")
    first = values.get("PT")
    out.append(_glomerulus(tint(first[0]) if _usable(first) else PAPER))
    out += papers + tones + hatchings
    # macula densa: the plaque where the thick limb passes its own glomerulus
    plaque = FIRM.line(262.6, 92, 262.6, 110, 6.0)
    out.append(f"<path d='{plaque}' data-part='md' class='nd-wall' fill='none' stroke='{GRAPHITE}' "
               f"stroke-width='2.8'/><path d='{plaque}' fill='none' stroke='url(#nd-tooth)' stroke-width='3.4'/>")

    italic = f"font-family=\"{SERIF}\" font-style='italic' fill='{MUTED}'"
    small = f"{italic} font-size='10.5'"
    outer = _half_width(len(loops) - 1, len(loops))

    # ---- what can be pointed at. Large areas first, small ones on top of them.
    deepest = max(loop["depth"] for loop in loops)
    reach = "".join(f"<path d='{d}' {_HIT} stroke-width='{REACH}'/>" for d in _loop(outer / 2, deepest))
    out.append(_link(links.get("loops"),
                     reach
                     + f"<text class='nd-code' x='{LOOP_AXIS - outer - 8}' y='500' text-anchor='end' {small}>LDL</text>"
                     + f"<text class='nd-code' x='{LOOP_AXIS + outer + 8}' y='500' text-anchor='start' {small}>LAL</text>",
                     "data-seg='loops'"))
    for index, (code, (x, y, anchor)) in enumerate(LABELS.items()):
        pair = values.get(code)
        shown = f"{pair[1]:.0f}" if _usable(pair) else "n.c."
        fade = f" class='nd-fade' style='animation-delay:{0.45 + 0.2 * index:.2f}s'" if animate else ""
        body = (
            f"<path d='{SEGMENTS[code]['d']}' {_HIT} stroke-width='{REACH}'/>"
            f"<text x='{x}' y='{y}' text-anchor='{anchor}'{fade}>"
            f"<tspan class='nd-code' font-family=\"{SERIF}\" font-weight='600' font-size='12.5' "
            f"fill='{INK}'>{html.escape(code)}</tspan>"
            f"<tspan dx='5' font-family=\"{MONO}\" font-size='10.5' fill='{MUTED}'>{shown}</tspan></text>")
        out.append(_link(links.get(code), body, f"data-seg='{code}'"))
    cx, cy, r = GLOMERULUS
    out.append(f"<g class='nd-hot' data-seg='glom'><circle cx='{cx}' cy='{cy}' r='{r + 2}' fill='transparent'/>"
               f"<text class='nd-code' x='238' y='70' text-anchor='middle' {small}>glomerulus</text></g>")
    out.append(f"<g class='nd-hot' data-seg='md'><rect x='255' y='86' width='11' height='30' fill='transparent'/>"
               f"<text class='nd-code' x='279' y='112' text-anchor='start' {small}>macula densa</text></g>")

    # ---- scale, with a mark for what is under the pointer (line: inlet, triangle: outlet)
    bx, by, bw = 404, 590, 80

    def at(value):
        return bx + bw * (min(max(value, lo), hi) - lo) / (hi - lo)

    tick = f"font-family=\"{MONO}\" font-size='8.5' fill='{MUTED}' text-anchor='middle'"
    out.append(f"<rect x='{bx}' y='{by}' width='{bw}' height='7' fill='url(#nd-t-scale)' fill-opacity='0.62'/>"
               f"<rect x='{bx}' y='{by}' width='{bw}' height='7' fill='url(#nd-hatch)' mask='url(#nd-m-scale)'/>"
               f"<rect x='{bx}' y='{by}' width='{bw}' height='7' fill='none' stroke='{GRAPHITE}' "
               f"stroke-width='0.7'/>")
    for v in (100, 300, 700):
        out.append(f"<line x1='{at(v):.1f}' y1='{by + 7}' x2='{at(v):.1f}' y2='{by + 10}' "
                   f"stroke='{GRAPHITE}' stroke-width='0.6'/>")
        out.append(f"<text x='{at(v):.1f}' y='{by + 19}' {tick}>{v}</text>")
    out.append(f"<text x='{bx}' y='{by - 9}' font-family=\"{MONO}\" font-size='8.5' letter-spacing='1' "
               f"fill='{MUTED}'>{html.escape(unit)}</text>")

    def triangle(value):
        x = at(value)
        return f"<path d='M{x - 3:.1f},{by - 6} L{x + 3:.1f},{by - 6} L{x:.1f},{by - 1} Z' fill='{ACCENT}'/>"

    for code in ORDER:
        if _usable(values.get(code)):
            inlet, outlet = values[code]
            out.append(f"<g class='nd-mark' data-for='{code}'>{triangle(outlet)}"
                       f"<line x1='{at(inlet):.1f}' y1='{by - 6}' x2='{at(inlet):.1f}' y2='{by}' "
                       f"stroke='{ACCENT}' stroke-width='1'/></g>")
    bends = "".join(triangle(loop["value"]) for loop in loops if _number(loop.get("value")))
    if bends:
        out.append(f"<g class='nd-mark' data-for='loops'>{bends}</g>")

    out.append("</svg>")
    return "".join(out)


def pin(code):
    """The selected segment, marked on the plate (its wall and its name in red pencil).
    A rule of its own, so that selecting a segment changes these two lines and not the figure."""
    if code not in SEGMENTS:
        return ""
    return (f"<style class='nd-pin'>.nd-plate .nd-wall[data-part='{code}'] {{ stroke: {ACCENT}; "
            f"stroke-width: {SEGMENTS[code]['w'] + 0.8:g}px; }} "
            f".nd-plate [data-seg='{code}'] .nd-code {{ fill: {ACCENT}; }}</style>")


# ============================================================
#  The cards shown beside the pointer
# ============================================================
def sparkline(series, width=216, height=38):
    """A small line through a series of numbers, its two ends marked and nothing else."""
    series = [v for v in series if _number(v)]
    if len(series) < 2:
        return ""
    low, high = min(series), max(series)
    span = (high - low) or 1.0
    pad = 4
    xs = [pad + (width - 2 * pad) * i / (len(series) - 1) for i in range(len(series))]
    ys = [height - pad - (height - 2 * pad) * (v - low) / span for v in series]
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='{width}' "
            f"height='{height}' role='img' aria-label='profile along the segment'>"
            f"<line x1='{pad}' y1='{height - 0.5}' x2='{width - pad}' y2='{height - 0.5}' "
            f"stroke='{RULE}' stroke-width='1'/>"
            f"<polyline points='{points}' fill='none' stroke='{INK}' stroke-width='1.3' "
            f"stroke-linejoin='round'/>"
            f"<circle cx='{xs[0]:.1f}' cy='{ys[0]:.1f}' r='2' fill='{PAPER}' stroke='{INK}' stroke-width='1'/>"
            f"<circle cx='{xs[-1]:.1f}' cy='{ys[-1]:.1f}' r='2.2' fill='{ACCENT}'/></svg>")


def cards(entries):
    """The cards of a figure, as HTML to place beside it.

    entries: {key: {"head", "name", "rows": [(label, text)], "series": numbers or None, "hint"}}
    where key is what the card belongs to (a segment code, "loops", "glom", "md").
    """
    out = []
    for key, entry in entries.items():
        rows = "".join(f"<dt>{html.escape(label)}</dt><dd>{html.escape(text)}</dd>"
                       for label, text in entry.get("rows", ()))
        name = f"<div class='name'>{html.escape(entry['name'])}</div>" if entry.get("name") else ""
        hint = f"<div class='hint'>{html.escape(entry['hint'])}</div>" if entry.get("hint") else ""
        out.append(f"<div class='nd-card' data-for='{html.escape(key, quote=True)}'>"
                   f"<div class='head'>{html.escape(entry['head'])}</div>{name}"
                   f"{sparkline(entry['series']) if entry.get('series') else ''}"
                   f"{'<dl>' + rows + '</dl>' if rows else ''}{hint}</div>")
    return "".join(out)


# ============================================================
#  The locator (sidebar, and wherever a small nephron helps)
# ============================================================
def locator(segment=None, width=58, links=None, names=None, struck=(), depth=1.0, long_loop=False):
    """A small map of the nephron.

    segment:   the segment to mark (LDL and LAL mark the long loop).
    links:     {segment code: href}; with them every segment can be clicked.
    names:     {segment code: full name}, for the tooltip.
    struck:    segments to cross out (they did not converge).
    depth:     how deep the long loop reaches (0-1).
    long_loop: draw the long loop as a solid line (a juxtamedullary nephron is selected).
    """
    links, names, struck = links or {}, names or {}, set(struck)
    quiet, box = "#b3aa96", (122, 48, 284, 566)
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{box[0]} {box[1]} {box[2]} {box[3]}' "
           f"width='{width}' height='{width * box[3] / box[2]:.0f}' role='img' "
           f"aria-label='Position of the selected segment in the nephron' style='display:block;flex:none;'>"]
    for y in (CORTEX_END, OUTER_END):
        out.append(f"<line x1='{box[0]}' y1='{y}' x2='{box[0] + box[2]}' y2='{y}' stroke='{RULE}' "
                   f"stroke-width='3' stroke-dasharray='6 10'/>")

    def piece(code, d, loop=False):
        on, bad = code == segment, code in struck
        stroke = ACCENT if (on or bad) else quiet
        if on:
            dash, thick = "", 15 if not loop else 12
        elif bad:
            dash, thick = " stroke-dasharray='5 9'", 9
        elif loop and not long_loop:
            dash, thick = " stroke-dasharray='10 9'", 4
        else:
            dash, thick = "", 6
        tip = names.get(code, code)
        if bad:
            tip += " (did not converge)"
        tag = " data-loop='1'" if loop else ""
        body = (f"<title>{html.escape(tip)}</title>"
                f"<path d='{d}' class='nd-loc' data-loc='{code}'{tag} fill='none' "
                f"stroke='{stroke}' stroke-width='{thick}' stroke-linecap='round'{dash}/>")
        if links.get(code):
            body += f"<path d='{d}' {_HIT} stroke-width='34'/>"
        return _link(links.get(code), body)

    for code, d in zip(GHOST, _loop(22, depth)):
        out.append(piece(code, d, loop=True))
    cx, cy, r = GLOMERULUS
    out.append(f"<circle cx='{cx}' cy='{cy}' r='{r - 2}' fill='none' stroke='{quiet}' stroke-width='6'/>")
    marked_last = [c for c in ORDER if c != segment] + ([segment] if segment in SEGMENTS else [])
    for code in marked_last:                # the marked segment is drawn last, on top
        out.append(piece(code, SEGMENTS[code]["d"]))
    out.append("</svg>")
    return "".join(out)


# ============================================================
#  The mark (logo, favicon)
# ============================================================
def mark(background=None):
    """A glomerulus and a loop. Drawn by hand for the logo: the loop is found in two passes
    and the dot is not quite round. With `background` it sits on a rounded tile and is drawn
    plainly (for the browser tab, where it is a few pixels across)."""
    if background:
        return (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32'>"
            f"<rect width='32' height='32' rx='6' fill='{background}'/>"
            f"<circle cx='8.4' cy='10' r='4.8' fill='{ACCENT}'/>"
            f"<path d='M13.2,10 H16 a4,4 0 0 1 4,4 V22.5 a3.4,3.4 0 0 0 6.8,0 V6' fill='none' "
            f"stroke='{INK}' stroke-width='2.3' stroke-linecap='round'/></svg>"
        )
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32'>"
        "<g fill='none' stroke-linecap='round' stroke-linejoin='round'>"
        # the looser pass
        f"<path d='M12.2,10.9 C14.4,9.6 17.4,9.4 19.2,11.4 C20.6,13 20.2,15.4 20.5,17.6 L20.4,22.9 "
        f"C20.7,25.4 22.6,26.6 24.3,26.1 C26.3,25.5 27.2,23.6 26.9,21.6 L27.3,4.9' "
        f"stroke='{GRAPHITE}' stroke-width='1.1' opacity='0.38'/>"
        f"<path d='M8.9,4.6 C5.4,4.3 3,7.2 3.4,10.6 C3.8,14 6.8,15.9 9.9,15.2 C12.9,14.5 14.2,11.6 13.5,8.9 "
        f"C12.9,6.6 10.9,4.9 8.2,5.2' stroke='{GRAPHITE}' stroke-width='0.9' opacity='0.45'/>"
        # the firm pass
        f"<path d='M13.1,10.2 C14.8,9.7 16.6,9.6 18,10.6 C19.6,11.8 20,13.5 19.9,15.3 L20.1,22.3 "
        f"C20.2,24.7 21.7,26 23.6,25.8 C25.5,25.6 26.8,24.2 26.7,22.1 L26.6,5.9' "
        f"stroke='{INK}' stroke-width='2.15'/></g>"
        f"<path d='M8.5,5.4 C11.4,5.2 13.1,7.5 13,10 C12.9,12.7 10.9,14.7 8.3,14.6 C5.6,14.5 3.7,12.5 3.8,9.8 "
        f"C3.9,7.3 5.8,5.5 8.5,5.4 Z' fill='{ACCENT}'/></svg>"
    )
