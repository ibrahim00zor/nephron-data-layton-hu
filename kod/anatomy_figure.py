"""
anatomy_figure.py — The nephron of the Interactive Anatomy page: one drawing, coloured and
sized by the data, with the profile along the nephron beside it.

It is built the way the figure of the Home page is (nephron_figure.py): as one SVG, written
as text, drawn by the same hand (hand.py) and answered by the same script (events.py). A
segment is an ordinary link; what is under the pointer is named on the drawing and in the
chart alike; the page writes the figure again when a choice changes, and the browser moves
from one to the other (colours and widths are eased, see STYLES).

Until 2026-10 this figure was a separate document in a frame, drawn by D3 and roughened by
filters. In Safari it took some 120 ms to paint and was painted again for every step of
the flow; a change of solute loaded the frame anew; and the frame cut the drawing off below
the outer medulla. None of that is left: no frame, no library, no font fetched from
elsewhere, no filter.

What the drawing encodes is unchanged:
- colour:    the concentration of the chosen solute where the fluid enters and leaves a
             segment, or its load (flux) there;
- thickness: the water flowing through the segment;
- the dots:  the same flow, as speed;
- the ground: the interstitial osmolality the model is given.

The drawing is a schematic. As in the model, the superficial nephron has a short loop that
turns at the outer-inner medullary boundary (no thin limbs below it); the bend is drawn as
part of the thick limb, as on the Home figure.
"""
import html
import math
from functools import lru_cache

from hand import Hand, along, through, tooth
from nephron_figure import _HIT, _link
from style import ACCENT, GRAPHITE, INK, INK_SOFT, MONO, MUTED, PAPER, SERIF

# ============================================================
#  Geometry (SVG user units; y grows downward)
# ============================================================
W, H = 1000, 915
SHEET = 612                           # the drawing takes the left of the figure, up to here
CORTEX_END, OUTER_END = 254, 522      # y of the cortex / outer medulla / inner medulla boundaries
DEPTH = 940                           # the depth over which the interstitial gradient is laid
GLOMERULUS = (105, 120, 22)
REACH = 34                            # width of the area around a segment that can be pointed at

# code -> (points of its line, width when there is no flow to size it by), in the order of
# the flow. This is a juxtamedullary nephron: the thin limbs reach into the inner medulla.
# Of the two thin limbs only the straight parts are given here; the bend that joins them is
# added in layout().
_LONG = {
    "PT":   ([(120, 135), (140, 120), (170, 140), (200, 125), (230, 140), (255, 128), (275, 145)], 12),
    "S3":   ([(275, 145), (275, 175), (270, 210), (268, 250)], 10),
    "SDL":  ([(268, 250), (265, 310), (262, 380), (260, 440), (258, 510)], 5),
    "LDL":  ([(258, 510), (256, 580), (255, 650), (256, 720), (258, 790), (258, 811)], 5),
    "LAL":  ([(336, 811), (336, 790), (333, 720), (332, 650), (334, 580), (336, 510)], 6),
    "mTAL": ([(336, 510), (338, 440), (340, 380), (342, 310), (344, 250)], 10),
    "cTAL": ([(344, 250), (346, 210), (348, 175), (350, 145)], 10),
    "DCT":  ([(350, 145), (370, 125), (395, 140), (418, 120), (440, 140)], 9),
    "CNT":  ([(440, 140), (460, 130), (478, 142)], 8),
    "CCD":  ([(478, 142), (480, 180), (482, 220), (483, 250)], 9),
    "OMCD": ([(483, 250), (485, 320), (487, 400), (488, 510)], 10),
    "IMCD": ([(488, 510), (490, 600), (492, 700), (494, 790), (495, 870)], 12),
}
SEGMENTS = list(_LONG)
_BEND = 39                            # half the distance between the two limbs of a loop

# code -> where its name is written: x, y, text-anchor
LABELS = {
    "PT": (190, 108, "middle"), "S3": (245, 195, "end"), "SDL": (238, 380, "end"),
    "LDL": (233, 680, "end"), "LAL": (355, 680, "start"), "mTAL": (362, 380, "start"),
    "cTAL": (374, 220, "start"), "DCT": (395, 108, "middle"), "CNT": (462, 116, "middle"),
    "CCD": (508, 195, "start"), "OMCD": (510, 400, "start"), "IMCD": (516, 750, "start"),
}

# The same two passes as on the Home figure, at the scale of this drawing.
FIRM = Hand(seed=4, wavelength=62, reach=1.9)
LOOSE = Hand(seed=23, wavelength=42, reach=2.6)


@lru_cache(maxsize=None)
def layout(long_loop):
    """The tubule of a nephron with a long loop, or with a short one:
    {code: {"firm", "loose", "ends", "width", "length"}}, in the order of the flow."""
    lines = {code: (through(points), points[0], points[-1], width) for code, (points, width) in _LONG.items()}
    if long_loop:
        # The loop of Henle turns in a hairpin: one smooth bend, not a corner. The descending
        # limb takes the first half of it and the ascending limb the second, so the two
        # segments of the model meet at the tip of the loop.
        down, up = _LONG["LDL"][0], _LONG["LAL"][0]
        tip = (297, 811 + _BEND)
        lines["LDL"] = (through(down) + f" A{_BEND},{_BEND} 0 0 0 {tip[0]},{tip[1]}", down[0], tip, 5)
        lines["LAL"] = (f"M{tip[0]},{tip[1]} A{_BEND},{_BEND} 0 0 0 336,811 " + through(up).split(" ", 1)[1],
                        tip, up[-1], 6)
    else:
        del lines["LDL"], lines["LAL"]
        short = [(268, 250), (265, 310), (262, 380), (260, 440), (259, 471)]
        lines["SDL"] = (through(short), short[0], short[-1], 5)
        limb = [(337, 471), (338, 440), (340, 380), (342, 310), (344, 250)]
        bend = f"M259,471 A{_BEND},{_BEND} 0 0 0 337,471 " + through(limb).split(" ", 1)[1]
        lines["mTAL"] = (bend, (298, 510), limb[-1], 10)       # the tint runs from the bend upward
    paths = [d for d, *_ in lines.values()]
    firm, loose = FIRM.chain(paths, 9.0), LOOSE.chain(paths, 9.0)
    out = {}
    for i, (code, (d, start, end, width)) in enumerate(lines.items()):
        points = along(d, 4.0)[0]
        length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
        out[code] = {"firm": firm[i], "loose": loose[i], "ends": (start, end), "width": width, "length": length}
    return out


def order(long_loop):
    return list(layout(bool(long_loop)))


# ============================================================
#  Scales
# ============================================================
# Colour ramps, as stops (ColorBrewer YlOrRd and YlOrBr; viridis), blended in between.
YL_OR_RD = ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#bd0026", "#800026"]
YL_OR_BR = ["#ffffe5", "#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02", "#993404", "#662506"]
VIRIDIS = ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"]


def shade(ramp, value, low, high):
    """Colour of a value on a ramp that runs from `low` to `high` (clamped at both ends)."""
    t = 0.0 if high <= low else min(max((value - low) / (high - low), 0.0), 1.0)
    at = t * (len(ramp) - 1)
    i = min(int(at), len(ramp) - 2)
    a, b, f = ramp[i].lstrip("#"), ramp[i + 1].lstrip("#"), at - i
    return "#" + "".join(f"{round(int(a[k:k + 2], 16) + (int(b[k:k + 2], 16) - int(a[k:k + 2], 16)) * f):02x}"
                         for k in (0, 2, 4))


def thickness(flow, low, high):
    """Width of a segment for the water flowing through it (3 to 20 units)."""
    t = 0.0 if high <= low else min(max((flow - low) / (high - low), 0.0), 1.0)
    return 3 + 17 * t


def pace(flow, low, high):
    """Seconds a dot takes to run along a segment: the more flow, the faster (7 s to 2.2 s)."""
    t = 0.0 if high <= low else min(max((flow - low) / (high - low), 0.0), 1.0)
    return 7.0 - 4.8 * t


def ticks(low, high, about=5):
    """Round numbers that span low..high: (first, step, how many)."""
    span = (high - low) or abs(high) or 1.0
    raw = span / about
    power = 10 ** math.floor(math.log10(raw))
    step = min((m * power for m in (1, 2, 2.5, 5, 10)), key=lambda s: abs(s - raw))
    first = math.ceil(low / step - 1e-9) * step
    count = int(math.floor((high - first) / step + 1e-9)) + 1
    return first, step, max(count, 0)


def _plain(value):
    """A number for an axis or a scale: as short as it can be said."""
    if value == 0:
        return "0"
    if abs(value) >= 100:
        return f"{value:,.0f}"
    if abs(value) >= 10:
        return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"
    return f"{value:.2g}"


# ============================================================
#  How the figure moves (CSS, written to the page once, with the page)
# ============================================================
STYLES = f"""<style>
/* a change of solute, of scenario or of what the colour shows is eased, not cut */
.na-plate .na-tube, .na-plate .nd-wall, .na-plate .na-under {{
  transition: stroke-width .45s ease, stroke .18s ease-out, opacity .18s ease-out;
}}
.na-plate stop {{ transition: stop-color .45s ease; }}
.na-plate .na-line {{ transition: opacity .18s ease-out, stroke .18s ease-out, stroke-width .18s ease-out; }}
/* the flow: dots that run along a segment, the faster the more water it carries */
@keyframes na-flow {{ to {{ stroke-dashoffset: -1; }} }}
.na-plate .na-dots {{
  stroke-dasharray: 0.002 0.998; stroke-linecap: round; fill: none; pointer-events: none;
  animation: na-flow linear infinite;
}}
@media (prefers-reduced-motion: reduce) {{ .na-plate .na-dots {{ animation: none; }} }}
</style>"""


def pin(code, width):
    """The selected segment, marked on the drawing and in the chart (a rule of its own, as
    nephron_figure.pin: selecting a segment changes these lines and not the figure)."""
    code = html.escape(str(code), quote=True)
    return (f"<style class='nd-pin'>.na-plate .nd-wall[data-part='{code}'] {{ stroke: {ACCENT}; "
            f"stroke-width: {width:.2f}px; }} "
            f".na-plate [data-seg='{code}'] .nd-code {{ fill: {ACCENT}; }} "
            f".na-plate .na-line[data-part='{code}'] {{ stroke: {ACCENT}; stroke-width: 2.6px; }} "
            f".na-plate .na-band[data-for='{code}'] {{ opacity: 1; }}</style>")


# ============================================================
#  The figure
# ============================================================
def wall(width):
    """Width of the outline of a tube whose lumen is `width` wide: a pencil line of two
    units on either side of it."""
    return width + 4.0


def figure(shown, values, low, high, ramp, title, unit, flow, flow_low, flow_high, interstitium,
           links=None, long_loop=False, dots=True):
    """The drawing, its scales and the profile along the nephron, as one SVG.

    shown:        the segments to draw, in the order of the flow (see order()).
    values:       {code: {"entry", "exit", "profile": [(position 0-1, value)]}} of what the
                  colour shows; a segment that is missing is drawn empty, with a broken outline.
    low, high:    the two ends of the colour scale; ramp: its colours; title, unit: its name.
    flow:         {code: mean water flow}; flow_low, flow_high: the two ends of the thickness scale.
    interstitium: [(depth 0-1, mOsm)], top to bottom: the ground the tubule is drawn on.
    links:        {code: href}, followed on a click.
    dots:         show the flow as dots that run along the segments.
    """
    links = links or {}
    lines = layout(bool(long_loop))
    shown = [code for code in shown if code in lines]
    serif, mono = f"font-family=\"{SERIF}\"", f"font-family=\"{MONO}\""
    italic = f"{serif} font-style='italic'"
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' role='img' "
           f"aria-label='The nephron, coloured and sized by model output, with the profile along it' "
           f"style='width:100%;height:auto;display:block;'>"]

    widths = {code: (thickness(flow[code], flow_low, flow_high) if code in flow else lines[code]["width"])
              for code in shown}

    # ---- definitions
    out.append("<defs>")
    # the tooth is coarse here: the line is thick enough to be broken up by it, as charcoal is
    out.append(tooth(PAPER, name="na-tooth", units=44, pixels=84, cover=0.6, cell=3))
    for code in shown:
        (x1, y1), (x2, y2) = lines[code]["ends"]
        if code in values:
            a = shade(ramp, values[code]["entry"], low, high)
            b = shade(ramp, values[code]["exit"], low, high)
        else:
            a = b = "#ede6d6"
        out.append(f"<linearGradient id='na-c-{code}' gradientUnits='userSpaceOnUse' x1='{x1}' y1='{y1}' "
                   f"x2='{x2}' y2='{y2}'><stop offset='0' stop-color='{a}'/><stop offset='1' stop-color='{b}'/>"
                   f"</linearGradient>")
        # the line of the segment, written once; its length is called 3, so that three dots
        # can run along it whatever its length
        out.append(f"<path id='na-p-{code}' d='{lines[code]['firm']}' pathLength='3'/>")
    stops = "".join(f"<stop offset='{i / 10:g}' stop-color='{shade(ramp, low + (high - low) * i / 10, low, high)}'/>"
                    for i in range(11))
    out.append(f"<linearGradient id='na-scale' x1='0' y1='0' x2='1' y2='0'>{stops}</linearGradient>")
    if len(interstitium) >= 2:
        osm_low, osm_high = min(v for _, v in interstitium), max(v for _, v in interstitium)
        ground = "".join(f"<stop offset='{depth:g}' stop-color='{shade(YL_OR_BR, osm, osm_low - 50, osm_high + 100)}'/>"
                         for depth, osm in interstitium)
        out.append(f"<linearGradient id='na-ground' gradientUnits='userSpaceOnUse' x1='0' y1='0' x2='0' "
                   f"y2='{DEPTH}'>{ground}</linearGradient>")
        key = "".join(f"<stop offset='{i / 10:g}' stop-color='"
                      f"{shade(YL_OR_BR, osm_low + (osm_high - osm_low) * i / 10, osm_low - 50, osm_high + 100)}'/>"
                      for i in range(11))
        out.append(f"<linearGradient id='na-ground-key' x1='0' y1='0' x2='0' y2='1'>{key}</linearGradient>")
    out.append(f"<marker id='na-arrow' viewBox='0 0 10 10' refX='8' refY='5' markerWidth='6' markerHeight='6' "
               f"orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='{ACCENT}' opacity='0.7'/></marker>")
    out.append("</defs>")

    # ---- the ground: the interstitium the model is given, and the three zones
    zone = f"{italic} font-size='12.5' fill='{MUTED}'"
    for y in (CORTEX_END, OUTER_END):
        out.append(f"<path d='{LOOSE.line(0, y, SHEET, y + 1.5, 16.0)}' fill='none' stroke='{GRAPHITE}' "
                   f"stroke-width='0.8' opacity='0.4'/>")
    for y, name in ((25, "cortex"), (CORTEX_END + 22, "outer medulla"), (OUTER_END + 22, "inner medulla")):
        out.append(f"<text x='12' y='{y}' {zone}>{name}</text>")
    if len(interstitium) >= 2:
        bar_x, bar_y, bar_h = SHEET - 22, 330, 300
        tick = f"{mono} font-size='10' fill='{MUTED}'"
        out.append(f"<rect x='{bar_x}' y='{bar_y}' width='11' height='{bar_h}' fill='url(#na-ground-key)' "
                   f"opacity='0.7'/><rect x='{bar_x}' y='{bar_y}' width='11' height='{bar_h}' fill='none' "
                   f"stroke='{GRAPHITE}' stroke-width='0.6' opacity='0.6'/>"
                   f"<text x='{bar_x + 11}' y='{bar_y - 9}' text-anchor='end' {tick}>mOsm</text>"
                   f"<text x='{bar_x - 5}' y='{bar_y + 8}' text-anchor='end' {tick}>{osm_low:.0f}</text>"
                   f"<text x='{bar_x - 5}' y='{bar_y + bar_h}' text-anchor='end' {tick}>{osm_high:.0f}</text>")

    # ---- the tubule: the looser pass, the firm outline with the tooth of the paper over it,
    # the colour inside, and the flow. The ground is washed in over the pencil and under the
    # colour: where the tooth shows through a line it shows the ground, and the colour of a
    # segment is not tinted by it.
    line = "fill='none' stroke-linecap='round' stroke-linejoin='round'"
    out.append("<g opacity='0.3'>" + "".join(
        f"<path d='{lines[code]['loose']}' class='na-under' data-part='{code}' {line} stroke='{GRAPHITE}' "
        f"stroke-width='{wall(widths[code]):.2f}'/>" for code in shown) + "</g>")
    for code in shown:
        dash = 3 / lines[code]["length"]          # one unit of the drawing, in the measure of the line
        broken = "" if code in values else f" stroke-dasharray='{6 * dash:.4f} {4 * dash:.4f}'"
        out.append(f"<use href='#na-p-{code}' class='nd-wall' data-part='{code}' {line} stroke='{GRAPHITE}' "
                   f"stroke-width='{wall(widths[code]):.2f}'{broken}/>")
    out.append("".join(f"<use href='#na-p-{code}' {line} stroke='url(#na-tooth)' "
                       f"stroke-width='{wall(widths[code]):.2f}'/>" for code in shown))
    if len(interstitium) >= 2:
        out.append(f"<rect x='0' y='0' width='{SHEET}' height='{H}' fill='url(#na-ground)' opacity='0.2' "
                   f"pointer-events='none'/>")
    # tubuloglomerular feedback: from the macula densa back to the afferent arteriole
    out.append(f"<path d='M348,150 C300,250 150,250 74,128' fill='none' stroke='{ACCENT}' stroke-width='1' "
               f"stroke-dasharray='5 4' opacity='0.45' marker-end='url(#na-arrow)'/>"
               f"<text x='205' y='236' text-anchor='middle' {italic} font-size='11' fill='{ACCENT}'>TGF →</text>")
    for code in shown:
        out.append(f"<use href='#na-p-{code}' class='na-tube' data-part='{code}' {line} "
                   f"stroke='url(#na-c-{code})' stroke-width='{widths[code]:.2f}'/>")
    if dots:
        for code in shown:
            if code not in flow:
                continue
            beat = pace(flow[code], flow_low, flow_high) / 3          # three dots to a segment
            size = min(max(widths[code] * 0.45, 2.6), 4.4)
            moving = (f"href='#na-p-{code}' class='na-dots' data-part='{code}' "
                      f"style='animation-duration:{beat:.2f}s'")
            out.append(f"<use {moving} stroke='{INK}' stroke-width='{size + 1.3:.1f}'/>"
                       f"<use {moving} stroke='{PAPER}' stroke-width='{size:.1f}'/>")

    # ---- the glomerulus, and the macula densa where the thick limb passes it
    cx, cy, r = GLOMERULUS
    out.append(f"<path d='{FIRM.circle(cx, cy, r)}' fill='{PAPER}' stroke='{GRAPHITE}' stroke-width='1.3'/>"
               + "".join(f"<path d='{FIRM.circle(cx + dx, cy + dy, rr)}' fill='{PAPER}' stroke='{GRAPHITE}' "
                         f"stroke-width='0.8'/>" for dx, dy, rr in ((-4, -3, 6), (5, -2, 5), (0, 5, 5), (-6, 4, 4), (6, 5, 4))))
    small = f"{italic} font-size='10' fill='{MUTED}'"
    out.append(f"<text x='{cx}' y='{cy - 30}' text-anchor='middle' {italic} font-size='12' fill='{ACCENT}'>glomerulus</text>"
               f"<text x='65' y='118' text-anchor='end' {small}>aff. →</text>"
               f"<text x='132' y='106' {small}>→ eff.</text>")
    out.append(f"<circle cx='350' cy='146' r='4.5' fill='{PAPER}' stroke='{INK}' stroke-width='1.4'/>"
               f"<text x='340' y='124' text-anchor='end' {italic} font-size='11' fill='{INK}'>macula densa</text>")
    out.append(f"<text x='495' y='{H - 16}' text-anchor='middle' {italic} font-size='11' fill='{INK_SOFT}'>↓ urine</text>")

    # ---- the names, and the areas that can be pointed at and clicked
    for code in shown:
        x, y, anchor = LABELS[code]
        body = (f"<use href='#na-p-{code}' {_HIT} stroke-width='{REACH}'/>"
                f"<text x='{x}' y='{y}' text-anchor='{anchor}'><tspan class='nd-code' {serif} font-weight='600' "
                f"font-size='13' fill='{INK}'>{code}</tspan></text>")
        out.append(_link(links.get(code), body, f"data-seg='{code}'"))

    # ---- beside the drawing: the two scales
    left, right = SHEET + 46, W - 14
    label = f"{italic} font-size='14' fill='{INK_SOFT}'"
    tick = f"{mono} font-size='11' fill='{MUTED}'"
    bar = 230
    out.append(f"<text x='{left}' y='30' {label}>{html.escape(title)} ({html.escape(unit)})</text>"
               f"<rect x='{left}' y='42' width='{bar}' height='12' fill='url(#na-scale)'/>"
               f"<rect x='{left}' y='42' width='{bar}' height='12' fill='none' stroke='{GRAPHITE}' "
               f"stroke-width='0.6' opacity='0.6'/>"
               f"<text x='{left}' y='70' {tick}>{_plain(low)}</text>"
               f"<text x='{left + bar}' y='70' text-anchor='end' {tick}>{_plain(high)}</text>")

    def on_scale(value):
        t = 0.0 if high <= low else min(max((value - low) / (high - low), 0.0), 1.0)
        return left + bar * t

    for code in shown:                    # where the segment under the pointer lies on the scale
        if code in values:
            a, b = on_scale(values[code]["entry"]), on_scale(values[code]["exit"])
            out.append(f"<g class='nd-mark' data-for='{code}'>"
                       f"<path d='M{b - 3.5:.1f},34 L{b + 3.5:.1f},34 L{b:.1f},40.5 Z' fill='{ACCENT}'/>"
                       f"<line x1='{a:.1f}' y1='34' x2='{a:.1f}' y2='41.5' stroke='{ACCENT}' stroke-width='1.1'/></g>")
    thin, thick = thickness(flow_low, flow_low, flow_high), thickness(flow_high, flow_low, flow_high)
    out.append(f"<text x='{left}' y='112' {label}>Thickness: water flow (nl/min)</text>"
               f"<line x1='{left + 2}' y1='132' x2='{left + 34}' y2='132' stroke='#9a927f' stroke-width='{thin:g}' "
               f"stroke-linecap='round'/><text x='{left + 44}' y='136' {tick}>{flow_low:.1f}</text>"
               f"<line x1='{left + 118}' y1='132' x2='{left + 146}' y2='132' stroke='#9a927f' stroke-width='{thick:g}' "
               f"stroke-linecap='round'/><text x='{left + 166}' y='136' {tick}>{flow_high:.1f}</text>")

    # ---- beside the drawing: the profile along the nephron, segment after segment
    profiled = [code for code in shown if code in values and len(values[code].get("profile") or ()) >= 2]
    if profiled:
        top, bottom = 232, 590
        every = [v for code in profiled for _, v in values[code]["profile"]]
        y_low, y_high = min(every), max(every)
        margin = (y_high - y_low) * 0.06 or abs(y_high) * 0.06 or 1.0
        y_low, y_high = y_low - margin, y_high + margin
        plot_left = left + 34

        def y_at(value):
            return bottom - (bottom - top) * (value - y_low) / (y_high - y_low)

        out.append(f"<text x='{left}' y='{top - 24}' {label}>{html.escape(title)} along the nephron "
                   f"({html.escape(unit)})</text>")
        first, step, count = ticks(y_low, y_high)
        for i in range(count):
            value = first + i * step
            y = y_at(value)
            out.append(f"<line x1='{plot_left}' y1='{y:.1f}' x2='{right}' y2='{y:.1f}' stroke='{GRAPHITE}' "
                       f"stroke-width='0.5' opacity='0.16'/>"
                       f"<text x='{plot_left - 7}' y='{y + 3.6:.1f}' text-anchor='end' {mono} font-size='10.5' "
                       f"fill='{MUTED}'>{_plain(round(value, 10))}</text>")
        room = (right - plot_left) / len(profiled)
        for i, code in enumerate(profiled):
            x0 = plot_left + room * i
            series = values[code]["profile"]
            points = " ".join(f"{x0 + room * min(max(p, 0.0), 1.0):.1f},{y_at(v):.1f}" for p, v in series)
            name_y = bottom + (17 if i % 2 == 0 else 31)
            body = (f"<rect class='nd-mark na-band' data-for='{code}' x='{x0:.1f}' y='{top}' width='{room:.1f}' "
                    f"height='{bottom - top}' fill='{ACCENT}' fill-opacity='0.07'/>"
                    f"<rect x='{x0:.1f}' y='{top}' width='{room:.1f}' height='{bottom - top + 36}' "
                    f"fill='transparent'/>"
                    f"<polyline class='na-line' data-part='{code}' points='{points}' fill='none' "
                    f"stroke='{GRAPHITE}' stroke-width='1.5' stroke-linejoin='round' stroke-linecap='round'/>"
                    f"<text x='{x0 + room / 2:.1f}' y='{name_y}' text-anchor='middle'>"
                    f"<tspan class='nd-code' {serif} font-size='11' fill='{MUTED}'>{code}</tspan></text>")
            out.append(_link(links.get(code), body, f"data-seg='{code}'"))
            if i:
                out.append(f"<line x1='{x0:.1f}' y1='{bottom}' x2='{x0:.1f}' y2='{bottom + 4}' "
                           f"stroke='{GRAPHITE}' stroke-width='0.6' opacity='0.6'/>")
        # what is measured is ruled: the axis is a straight line
        out.append(f"<line x1='{plot_left}' y1='{bottom}' x2='{right}' y2='{bottom}' stroke='{GRAPHITE}' "
                   f"stroke-width='1.1'/>")
        out.append(f"<text x='{left}' y='{bottom + 60}' {italic} font-size='12' fill='{MUTED}'>"
                   f"<tspan x='{left}'>Each segment from where the fluid enters it to where it</tspan>"
                   f"<tspan x='{left}' dy='16'>leaves it; the segments are given equal room.</tspan></text>")

    out.append("</svg>")
    return "".join(out)
