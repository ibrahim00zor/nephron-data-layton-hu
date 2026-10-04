"""
nephron_figure.py — The nephron, drawn once and used three ways.

One hand-placed geometry (a superficial nephron and the collecting duct it drains into,
with the long loops of the juxtamedullary nephrons drawn in hairline below it) gives:

- plate(...)   : the figure on the Home page, tinted and labelled with model output;
- locator(...) : a small map for the sidebar that marks the selected segment;
- mark(...)    : the logo and the favicon.

Everything is plain SVG built as a string: no JavaScript, nothing to load. What the
drawings do when the pointer is over them is CSS (`STYLES`, written to the page once by
ui_kit.apply_frame); what they do on a click is an ordinary link (see nav.href).

The drawing is a schematic, not anatomy to scale. It follows the layout of the model:
the superficial nephron has a short loop that turns at the outer-inner medullary boundary
(no LDL, no LAL); the collecting duct (CCD, OMCD, IMCD) is shared by all nephrons. The
model has no vasculature, so none is drawn.
"""
import html

from style import ACCENT, FAINT, INK, INK_SOFT, MONO, MUTED, PAPER, RULE, SERIF

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


def _usable(pair):
    """A (inlet, outlet) pair that can be drawn: both present, finite and not negative."""
    if not pair:
        return False
    return all(v is not None and v == v and v >= 0 for v in pair)


def _number(value):
    return value is not None and value == value and value >= 0


# ============================================================
#  Behaviour under the pointer (CSS, written to the page once)
# ============================================================
def _styles():
    hot = list(SEGMENTS) + list(LOOPS) + ["glom", "md"]
    rules = [f"""
/* ---------- the plate ---------- */
.nd-plate a {{ text-decoration: none; cursor: pointer; }}
.nd-plate .nd-hot {{ cursor: help; }}
.nd-plate .nd-wall, .nd-plate .nd-code {{ transition: stroke .18s, fill .18s; }}
.nd-plate .nd-read, .nd-plate .nd-mark {{ opacity: 0; transition: opacity .18s; pointer-events: none; }}
.nd-plate .nd-hint {{ transition: opacity .18s; }}
.nd-plate svg:has(.nd-seg:hover, .nd-hot:hover) .nd-hint {{ opacity: 0; }}
.nd-plate a.nd-seg:hover .nd-code {{ fill: {ACCENT}; }}
.nd-where a {{ cursor: pointer; }}
.nd-where .nd-loc {{ transition: stroke .15s; }}
.nd-where a:hover .nd-loc {{ stroke: {ACCENT}; }}

/* the plate is drawn in, in the order the fluid meets the segments */
@keyframes nd-draw {{ from {{ stroke-dashoffset: 1; opacity: 0; }} 8% {{ opacity: 1; }} to {{ stroke-dashoffset: 0; opacity: 1; }} }}
@keyframes nd-fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.nd-plate .nd-draw {{ stroke-dasharray: 1; animation: nd-draw .5s ease-out both; }}
.nd-plate .nd-fade {{ animation: nd-fade .5s ease-out both; }}
@media (prefers-reduced-motion: reduce) {{
  .nd-plate .nd-draw, .nd-plate .nd-fade {{ animation: none; }}
}}"""]
    for code in hot:
        rules.append(
            f".nd-plate svg:has([data-seg='{code}']:hover) .nd-wall[data-wall='{code}'] {{ stroke: {ACCENT}; }}\n"
            f".nd-plate svg:has([data-seg='{code}']:hover) [data-for='{code}'] {{ opacity: 1; }}")
    # what is under the pointer on the plate is also marked on the small map in the sidebar
    for code in list(SEGMENTS) + list(GHOST):
        rules.append(f"body:has(.nd-plate [data-seg='{code}']:hover) .nd-where [data-loc='{code}'] "
                     f"{{ stroke: {ACCENT}; }}")
    for nephron in LOOPS:
        rules.append(f"body:has(.nd-plate [data-seg='{nephron}']:hover) .nd-where [data-loop] "
                     f"{{ stroke: {ACCENT}; }}")
    return "<style>" + "\n".join(rules) + "</style>"


STYLES = _styles()


# ============================================================
#  Pieces shared by the drawings
# ============================================================
def _tube(code, fill, delay=None):
    seg = SEGMENTS[code]
    draw = f" pathLength='1' class='nd-wall nd-draw' style='animation-delay:{delay:.2f}s'" if delay is not None \
        else " class='nd-wall'"
    fade = f" class='nd-fade' style='animation-delay:{delay + 0.3:.2f}s'" if delay is not None else ""
    return (f"<path d='{seg['d']}' data-wall='{code}' fill='none' stroke='{INK}' stroke-width='{seg['w']}' "
            f"stroke-linecap='round' stroke-linejoin='round'{draw}/>",
            f"<path d='{seg['d']}' fill='none' stroke='{fill}' stroke-width='{seg['w'] - WALL:g}' "
            f"stroke-linejoin='round'{fade}/>")


def _glomerulus(fill):
    cx, cy, r = GLOMERULUS
    tuft = "".join(
        f"<circle cx='{cx + dx}' cy='{cy + dy}' r='6.4' fill='{PAPER}' stroke='{INK_SOFT}' stroke-width='0.8'/>"
        for dx, dy in ((-6, -5), (5, -7), (8, 4), (-2, 8), (-9, 3), (0, 0))
    )
    return (f"<circle cx='{cx}' cy='{cy}' r='{r}' data-wall='glom' class='nd-wall' fill='{fill}' "
            f"stroke='{INK}' stroke-width='1.2'/>{tuft}")


# A wide, invisible stroke over a line: the area that can be pointed at and clicked.
_HIT = "fill='none' stroke='transparent' pointer-events='stroke'"


def _link(href, body, attrs=""):
    """Wrap in a link when there is one to follow, in a plain group otherwise."""
    if href:
        return f"<a href='{html.escape(href, quote=True)}' target='_self' {attrs}>{body}</a>"
    return f"<g {attrs}>{body}</g>"


# ============================================================
#  The plate (Home page)
# ============================================================
def plate(values, unit="mOsm", names=None, links=None, loops=None, notes=None, animate=True):
    """The annotated figure.

    values: {segment code: (inlet, outlet)}; a missing or unusable pair is drawn hatched
            and labelled "n.c." (not converged). The label of a segment is its outlet value.
    names:  {segment code: full name}, shown while the pointer is over the segment.
    links:  {segment code or loop name: href}, followed on a click.
    loops:  the long loops, shallowest first: [{"nephron", "depth" (0-1), "value" (at the bend)}].
            Without it one loop is drawn at full depth.
    notes:  {"glom": text, "md": text}, shown while the pointer is over the glomerulus or
            the macula densa.
    """
    names, links, notes = names or {}, links or {}, notes or {}
    loops = loops if loops is not None else [{"nephron": LOOPS[-1], "depth": 1.0, "value": None}]
    x0, y0, w, h = VIEW
    right = x0 + w
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{x0} {y0} {w} {h}' role='img' "
           f"aria-label='Schematic of the nephron with model output per segment' "
           f"style='width:100%;height:auto;display:block;'>"]

    # ---- definitions: tints, hatching, the open end at the papilla, the pencil
    out.append("<defs>")
    for code, seg in SEGMENTS.items():
        if _usable(values.get(code)):
            (x1, y1), (x2, y2) = seg["ends"]
            a, b = values[code]
            out.append(f"<linearGradient id='nd-t-{code}' gradientUnits='userSpaceOnUse' "
                       f"x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}'>"
                       f"<stop offset='0' stop-color='{tint(a)}'/><stop offset='1' stop-color='{tint(b)}'/>"
                       f"</linearGradient>")
    lo, hi = SCALE[0][0], SCALE[-1][0]
    stops = "".join(f"<stop offset='{(v - lo) / (hi - lo):.3f}' stop-color='{c}'/>" for v, c in SCALE)
    out.append(f"<linearGradient id='nd-t-scale' x1='0' y1='0' x2='1' y2='0'>{stops}</linearGradient>")
    out.append("<pattern id='nd-t-none' width='4' height='4' patternUnits='userSpaceOnUse' "
               f"patternTransform='rotate(45)'><rect width='4' height='4' fill='{PAPER}'/>"
               f"<line x1='0' y1='0' x2='0' y2='4' stroke='{FAINT}' stroke-width='1'/></pattern>")
    out.append(f"<clipPath id='nd-t-open'><rect x='{x0}' y='{y0}' width='{w}' height='{PAPILLA - y0}'/></clipPath>")
    # a slight unevenness of the line, as from a pencil on paper
    out.append(f"<filter id='nd-pencil' filterUnits='userSpaceOnUse' x='{x0}' y='{y0}' width='{w}' height='{h}'>"
               "<feTurbulence type='fractalNoise' baseFrequency='0.035' numOctaves='2' seed='11' result='grain'/>"
               "<feDisplacementMap in='SourceGraphic' in2='grain' scale='1.7' "
               "xChannelSelector='R' yChannelSelector='G'/></filter>")
    out.append("</defs>")

    # ---- zones
    zone = (f"font-family=\"{MONO}\" font-size='8.5' letter-spacing='1.6' fill='{FAINT}'")
    for y, name in ((y0, "CORTEX"), (CORTEX_END, "OUTER MEDULLA"), (OUTER_END, "INNER MEDULLA")):
        if y != y0:
            out.append(f"<line x1='{x0 + 6}' y1='{y}' x2='{right - 6}' y2='{y}' stroke='{RULE}' "
                       f"stroke-width='1' stroke-dasharray='2 4'/>")
        out.append(f"<text x='{x0 + 6}' y='{y + 15}' {zone}>{name}</text>")

    # ---- everything drawn in ink goes through the pencil
    out.append("<g filter='url(#nd-pencil)'>")
    for index, loop in enumerate(loops):
        for d in _loop(_half_width(index, len(loops)), loop["depth"]):
            out.append(f"<path d='{d}' data-wall='{loop['nephron']}' class='nd-wall' fill='none' "
                       f"stroke='{FAINT}' stroke-width='0.9'/>")

    # the tubule: all walls first, then the glomerulus, then all lumens on top, so that every
    # joint is open and the capsule opens into the proximal tubule. The duct is left open
    # at the papilla (the walls are clipped there).
    walls, lumens = [], []
    for index, code in enumerate(ORDER):
        fill = f"url(#nd-t-{code})" if _usable(values.get(code)) else "url(#nd-t-none)"
        wall, lumen = _tube(code, fill, delay=0.15 + 0.2 * index if animate else None)
        walls.append(wall)
        lumens.append(lumen)
    first = values.get("PT")
    out.append(f"<g clip-path='url(#nd-t-open)'>{''.join(walls)}</g>")
    out.append(_glomerulus(tint(first[0]) if _usable(first) else PAPER))
    out += lumens
    # macula densa: the plaque where the thick limb passes its own glomerulus
    out.append(f"<line x1='262.6' y1='92' x2='262.6' y2='110' data-wall='md' class='nd-wall' "
               f"stroke='{INK}' stroke-width='2.8'/>")
    out.append("</g>")

    italic = f"font-family=\"{SERIF}\" font-style='italic' fill='{MUTED}'"
    small = f"{italic} font-size='10.5'"
    outer = _half_width(len(loops) - 1, len(loops))
    out.append(f"<text x='{LOOP_AXIS - outer - 8}' y='500' text-anchor='end' {small}>LDL</text>")
    out.append(f"<text x='{LOOP_AXIS + outer + 8}' y='500' text-anchor='start' {small}>LAL</text>")

    # ---- what can be pointed at: the long loops, the glomerulus, the macula densa
    for index, loop in enumerate(loops):
        hit = "".join(f"<path d='{d}' {_HIT} stroke-width='4'/>"
                      for d in _loop(_half_width(index, len(loops)), loop["depth"]))
        out.append(_link(links.get(loop["nephron"]), hit, f"class='nd-seg' data-seg='{loop['nephron']}'"))
    cx, cy, r = GLOMERULUS
    out.append(f"<g class='nd-hot' data-seg='glom'><circle cx='{cx}' cy='{cy}' r='{r}' fill='transparent'/>"
               f"<text x='238' y='70' text-anchor='middle' {small}>glomerulus</text></g>")
    out.append(f"<g class='nd-hot' data-seg='md'><rect x='256' y='88' width='12' height='26' fill='transparent'/>"
               f"<text x='279' y='112' text-anchor='start' {small}>macula densa</text></g>")

    # ---- the segments: a generous area to point at, the code and the outlet value
    for index, (code, (x, y, anchor)) in enumerate(LABELS.items()):
        pair = values.get(code)
        shown = f"{pair[1]:.0f}" if _usable(pair) else "n.c."
        fade = f" class='nd-fade' style='animation-delay:{0.45 + 0.2 * index:.2f}s'" if animate else ""
        body = (
            f"<path d='{SEGMENTS[code]['d']}' {_HIT} stroke-width='{SEGMENTS[code]['w'] + 12}'/>"
            f"<text x='{x}' y='{y}' text-anchor='{anchor}'{fade}>"
            f"<tspan class='nd-code' font-family=\"{SERIF}\" font-weight='600' font-size='12.5' fill='{INK}'>"
            f"{html.escape(code)}</tspan>"
            f"<tspan dx='5' font-family=\"{MONO}\" font-size='10.5' fill='{MUTED}'>{shown}</tspan></text>")
        out.append(_link(links.get(code), body, f"class='nd-seg' data-seg='{code}'"))

    # ---- scale, with a mark for the segment under the pointer (line: inlet, triangle: outlet)
    bx, by, bw = 404, 578, 80

    def at(value):
        return bx + bw * (min(max(value, lo), hi) - lo) / (hi - lo)

    tick = f"font-family=\"{MONO}\" font-size='8.5' fill='{MUTED}' text-anchor='middle'"
    out.append(f"<rect x='{bx}' y='{by}' width='{bw}' height='6' fill='url(#nd-t-scale)' "
               f"stroke='{INK_SOFT}' stroke-width='0.6'/>")
    for v in (100, 300, 700):
        out.append(f"<line x1='{at(v):.1f}' y1='{by + 6}' x2='{at(v):.1f}' y2='{by + 9}' "
                   f"stroke='{INK_SOFT}' stroke-width='0.6'/>")
        out.append(f"<text x='{at(v):.1f}' y='{by + 18}' {tick}>{v}</text>")
    out.append(f"<text x='{bx}' y='{by - 9}' font-family=\"{MONO}\" font-size='8.5' letter-spacing='1' "
               f"fill='{MUTED}'>{html.escape(unit)}</text>")
    marks = {code: values[code] for code in ORDER if _usable(values.get(code))}
    marks.update({loop["nephron"]: (None, loop["value"]) for loop in loops if _number(loop.get("value"))})
    for code, (inlet, outlet) in marks.items():
        x = at(outlet)
        shape = (f"<path d='M{x - 3:.1f},{by - 6} L{x + 3:.1f},{by - 6} L{x:.1f},{by - 1} Z' fill='{ACCENT}'/>")
        if inlet is not None:
            shape += (f"<line x1='{at(inlet):.1f}' y1='{by - 6}' x2='{at(inlet):.1f}' y2='{by}' "
                      f"stroke='{ACCENT}' stroke-width='1'/>")
        out.append(f"<g class='nd-mark' data-for='{code}'>{shape}</g>")

    # ---- the reading line under the figure: what is under the pointer, in words
    ry = y0 + h - 7
    code_font = f"font-family=\"{SERIF}\" font-weight='600' fill='{INK}'"
    number = f"font-family=\"{MONO}\" font-size='10' fill='{INK_SOFT}'"
    out.append(f"<text class='nd-hint' x='{x0 + 6}' y='{ry}' {italic} font-size='10.5' fill-opacity='0.75'>"
               f"point at a segment for its values; click to open its profile</text>")

    def reading(key, head, name, tail):
        name_part = f"<tspan dx='6' {italic}>{html.escape(name)}</tspan>" if name else ""
        tail_part = f"<tspan dx='8' {number}>{html.escape(tail)}</tspan>" if tail else ""
        out.append(f"<text class='nd-read' data-for='{key}' x='{x0 + 6}' y='{ry}' font-size='11'>"
                   f"<tspan {code_font}>{html.escape(head)}</tspan>{name_part}{tail_part}</text>")

    for code in ORDER:
        pair = values.get(code)
        tail = f"{pair[0]:.0f} → {pair[1]:.0f} {unit}" if _usable(pair) else "did not converge in this scenario"
        reading(code, code, names.get(code, ""), tail)
    for loop in loops:
        tail = f"{loop['value']:.0f} {unit} at the bend" if _number(loop.get("value")) else ""
        reading(loop["nephron"], loop["nephron"], "long loop of a juxtamedullary nephron", tail)
    reading("glom", "Glomerulus", notes.get("glom", ""), "")
    reading("md", "Macula densa", notes.get("md", ""), "")

    out.append("</svg>")
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
    """A glomerulus and a loop. With `background`, on a rounded tile (for the browser tab)."""
    tile = f"<rect width='32' height='32' rx='6' fill='{background}'/>" if background else ""
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32'>"
        f"{tile}<circle cx='8.4' cy='10' r='4.8' fill='{ACCENT}'/>"
        f"<path d='M13.2,10 H16 a4,4 0 0 1 4,4 V22.5 a3.4,3.4 0 0 0 6.8,0 V6' fill='none' "
        f"stroke='{INK}' stroke-width='2.3' stroke-linecap='round'/></svg>"
    )
