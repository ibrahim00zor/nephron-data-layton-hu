"""
nephron_figure.py — The nephron, drawn once and used three ways.

One hand-placed geometry (a superficial nephron and the collecting duct it drains into,
with the long loop of the juxtamedullary nephrons as a dashed ghost) gives:

- plate(...)   : the figure on the Home page, tinted and labelled with model output;
- locator(...) : a small map for the sidebar that marks the selected segment;
- mark(...)    : the logo and the favicon.

Everything is plain SVG built as a string: no JavaScript, nothing to load.

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
VIEW = (44, 14, 452, 606)             # x, y, width, height of the plate
CORTEX_END, OUTER_END = 250, 430      # y of the cortex / outer medulla / inner medulla boundaries
GLOMERULUS = (238, 100, 20)           # centre x, centre y, radius of Bowman's capsule
WALL = 2.4                            # twice the thickness of the tubule wall


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

# code -> path, outer width, and the two ends (the tint runs from the first to the second)
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
    "IMCD": dict(d="M388,430 L388,598", w=13, ends=((388, 430), (388, 598))),
}
ORDER = list(SEGMENTS)

# The long loop of the juxtamedullary nephrons, shown as a ghost below the short one.
GHOST = {
    "LDL": "M221,434 L221,553 A22,22 0 0 0 243,575",
    "LAL": "M243,575 A22,22 0 0 0 265,553 L265,434",
}

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


# ============================================================
#  Pieces shared by the three drawings
# ============================================================
def _tube(code, fill):
    seg = SEGMENTS[code]
    return (f"<path d='{seg['d']}' fill='none' stroke='{INK}' stroke-width='{seg['w']}' "
            f"stroke-linecap='round' stroke-linejoin='round'/>",
            f"<path d='{seg['d']}' fill='none' stroke='{fill}' stroke-width='{seg['w'] - WALL:g}' "
            f"stroke-linejoin='round'/>")


def _glomerulus(fill):
    cx, cy, r = GLOMERULUS
    tuft = "".join(
        f"<circle cx='{cx + dx}' cy='{cy + dy}' r='6.4' fill='{PAPER}' stroke='{INK_SOFT}' stroke-width='0.8'/>"
        for dx, dy in ((-6, -5), (5, -7), (8, 4), (-2, 8), (-9, 3), (0, 0))
    )
    return (f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{fill}' stroke='{INK}' stroke-width='1.2'/>{tuft}")


# ============================================================
#  The plate (Home page)
# ============================================================
def plate(values, unit="mOsm"):
    """The annotated figure.

    values: {segment code: (inlet, outlet)}; a missing or unusable pair is drawn empty
    and labelled "n.c." (not converged). The label of a segment is its outlet value.
    """
    x0, y0, w, h = VIEW
    right = x0 + w
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{x0} {y0} {w} {h}' role='img' "
           f"aria-label='Schematic of the nephron with model output per segment' "
           f"style='width:100%;height:auto;display:block;'>"]

    # tints, one gradient per segment, from its inlet to its outlet
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
    out.append(f"<clipPath id='nd-t-open'><rect x='{x0}' y='{y0}' width='{w}' height='{598 - y0}'/></clipPath>")
    out.append("</defs>")

    # zones
    zone = (f"font-family=\"{MONO}\" font-size='8.5' letter-spacing='1.6' fill='{FAINT}'")
    for y, name in ((y0, "CORTEX"), (CORTEX_END, "OUTER MEDULLA"), (OUTER_END, "INNER MEDULLA")):
        if y != y0:
            out.append(f"<line x1='{x0 + 6}' y1='{y}' x2='{right - 6}' y2='{y}' stroke='{RULE}' "
                       f"stroke-width='1' stroke-dasharray='2 4'/>")
        out.append(f"<text x='{x0 + 6}' y='{y + 15}' {zone}>{name}</text>")

    # the long loop, as a ghost
    for d in GHOST.values():
        out.append(f"<path d='{d}' fill='none' stroke='{FAINT}' stroke-width='1.1' stroke-dasharray='3 3'/>")
    italic = f"font-family=\"{SERIF}\" font-style='italic' fill='{MUTED}'"
    small = f"{italic} font-size='10.5'"
    out.append(f"<text x='213' y='500' text-anchor='end' {small}>LDL</text>")
    out.append(f"<text x='273' y='500' text-anchor='start' {small}>LAL</text>")
    out.append(f"<text x='243' y='594' text-anchor='middle' {italic} font-size='9.5'>"
               f"long loop: juxtamedullary nephrons only</text>")

    # the tubule: all walls first, then the glomerulus, then all lumens on top, so that every
    # joint is open and the capsule opens into the proximal tubule. The duct is left open
    # at the papilla (the walls are clipped there).
    walls, lumens = [], []
    for code in ORDER:
        fill = f"url(#nd-t-{code})" if _usable(values.get(code)) else "url(#nd-t-none)"
        wall, lumen = _tube(code, fill)
        walls.append(wall)
        lumens.append(lumen)
    first = values.get("PT")
    out.append(f"<g clip-path='url(#nd-t-open)'>{''.join(walls)}</g>")
    out.append(_glomerulus(tint(first[0]) if _usable(first) else PAPER))
    out += lumens

    # macula densa: the plaque where the thick limb passes its own glomerulus
    out.append(f"<line x1='262.6' y1='92' x2='262.6' y2='110' stroke='{INK}' stroke-width='2.8'/>")
    out.append(f"<text x='238' y='70' text-anchor='middle' {small}>glomerulus</text>")
    out.append(f"<text x='279' y='112' text-anchor='start' {small}>macula densa</text>")

    # labels: segment code and its outlet value
    for code, (x, y, anchor) in LABELS.items():
        pair = values.get(code)
        value = f"{pair[1]:.0f}" if _usable(pair) else "n.c."
        out.append(
            f"<text x='{x}' y='{y}' text-anchor='{anchor}'>"
            f"<tspan font-family=\"{SERIF}\" font-weight='600' font-size='12.5' fill='{INK}'>{html.escape(code)}</tspan>"
            f"<tspan dx='5' font-family=\"{MONO}\" font-size='10.5' fill='{MUTED}'>{value}</tspan></text>")

    # scale
    bx, by, bw = 404, 580, 80
    tick = f"font-family=\"{MONO}\" font-size='8.5' fill='{MUTED}' text-anchor='middle'"
    out.append(f"<rect x='{bx}' y='{by}' width='{bw}' height='6' fill='url(#nd-t-scale)' "
               f"stroke='{INK_SOFT}' stroke-width='0.6'/>")
    for v in (100, 300, 700):
        tx = bx + bw * (v - lo) / (hi - lo)
        out.append(f"<line x1='{tx:.1f}' y1='{by + 6}' x2='{tx:.1f}' y2='{by + 9}' stroke='{INK_SOFT}' stroke-width='0.6'/>")
        out.append(f"<text x='{tx:.1f}' y='{by + 18}' {tick}>{v}</text>")
    out.append(f"<text x='{bx}' y='{by - 5}' font-family=\"{MONO}\" font-size='8.5' letter-spacing='1' "
               f"fill='{MUTED}'>{html.escape(unit)}</text>")

    out.append("</svg>")
    return "".join(out)


# ============================================================
#  The locator (sidebar)
# ============================================================
def locator(segment=None, width=58):
    """A small map of the nephron with one segment marked. LDL and LAL mark the ghost loop."""
    quiet, box = "#b3aa96", (122, 48, 284, 566)
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{box[0]} {box[1]} {box[2]} {box[3]}' "
           f"width='{width}' height='{width * box[3] / box[2]:.0f}' role='img' "
           f"aria-label='Position of the selected segment in the nephron' style='display:block;flex:none;'>"]
    for y in (CORTEX_END, OUTER_END):
        out.append(f"<line x1='{box[0]}' y1='{y}' x2='{box[0] + box[2]}' y2='{y}' stroke='{RULE}' "
                   f"stroke-width='3' stroke-dasharray='6 10'/>")
    for code, d in GHOST.items():
        on = code == segment
        dash = "" if on else " stroke-dasharray='10 9'"
        out.append(f"<path d='{d}' fill='none' stroke='{ACCENT if on else quiet}' "
                   f"stroke-width='{12 if on else 4}'{dash}/>")
    cx, cy, r = GLOMERULUS
    out.append(f"<circle cx='{cx}' cy='{cy}' r='{r - 2}' fill='none' stroke='{quiet}' stroke-width='6'/>")
    for code in ORDER:                      # the marked segment is drawn last, on top
        if code != segment:
            out.append(f"<path d='{SEGMENTS[code]['d']}' fill='none' stroke='{quiet}' stroke-width='6' "
                       f"stroke-linecap='round'/>")
    if segment in SEGMENTS:
        out.append(f"<path d='{SEGMENTS[segment]['d']}' fill='none' stroke='{ACCENT}' stroke-width='15' "
                   f"stroke-linecap='round'/>")
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
