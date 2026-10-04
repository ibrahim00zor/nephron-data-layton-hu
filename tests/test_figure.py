"""The nephron drawing: the plate on the Home page, the sidebar locator, the mark."""
import os
import sys
import xml.dom.minidom

KOD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kod")
sys.path.insert(0, KOD)

import nephron_figure as figure   # noqa: E402

VALUES = {"PT": (298.5, 300.9), "S3": (300.9, 359.3), "SDL": (359.3, 579.9), "mTAL": (579.9, 253.3),
          "cTAL": (253.3, 98.8), "DCT": (98.8, 81.1), "CNT": (81.1, 286.0), "CCD": (290.2, 299.8),
          "OMCD": (299.8, 683.8), "IMCD": (683.8, 619.0)}


def _parse(svg):
    return xml.dom.minidom.parseString(svg)      # raises if the SVG is not well formed


def test_plate_labels_every_segment_with_its_outlet_value():
    svg = figure.plate(VALUES)
    _parse(svg)
    for code, (_, outlet) in VALUES.items():
        assert f">{code}</tspan>" in svg, code
        assert f">{outlet:.0f}</tspan>" in svg, code
    assert "n.c." not in svg


def test_plate_marks_a_segment_without_usable_data():
    for bad in (None, (683.4, -1128.8), (683.4, float("nan"))):
        values = dict(VALUES, IMCD=bad)
        if bad is None:
            del values["IMCD"]
        svg = figure.plate(values)
        _parse(svg)
        assert "n.c." in svg                      # not converged: no number ...
        assert "-1129" not in svg and "nan" not in svg
        assert "nd-t-IMCD" not in svg             # ... and no tint


def test_tone_is_hatched_and_follows_the_value():
    svg = figure.plate(VALUES)
    _parse(svg)
    for code in VALUES:                           # a wash and a mask for the hatching, per segment
        assert f"id='nd-t-{code}'" in svg and f"id='nd-m-{code}'" in svg, code
        assert f"mask='url(#nd-m-{code})'" in svg, code
    grey = lambda value: int(figure._level(value)[4:].split(",")[0])     # noqa: E731
    assert grey(80) < grey(300) < grey(750)       # the higher the value, the more hatching is let through
    assert grey(-5) == grey(80) and grey(9999) == grey(750)
    # a segment without data keeps a broken outline and gets no tone at all
    partial = figure.plate({k: v for k, v in VALUES.items() if k != "IMCD"})
    assert "stroke-dasharray='5 3.5'" in partial and "nd-m-IMCD" not in partial
    assert "stroke-dasharray='5 3.5'" not in svg


def test_tint_is_clamped_and_ordered():
    assert figure.tint(-50) == figure.tint(80) == figure.SCALE[0][1]
    assert figure.tint(5000) == figure.SCALE[-1][1]
    assert figure.tint(300) == figure.SCALE[1][1]


def test_locator_marks_one_segment():
    for code in list(figure.SEGMENTS) + list(figure.GHOST):
        svg = figure.locator(code)
        _parse(svg)
        assert svg.count(figure.ACCENT) == 1, code
    assert figure.ACCENT not in figure.locator(None)
    assert figure.ACCENT not in figure.locator("not a segment")


def test_figure_covers_the_segments_of_the_dataset():
    from ui_kit import SEG_ORDER_JUX
    assert set(figure.SEGMENTS) | set(figure.GHOST) == set(SEG_ORDER_JUX)
    assert set(figure.LABELS) == set(figure.SEGMENTS)


def test_plate_links_loops_and_selection():
    loops = [{"nephron": name, "depth": (i + 1) / 5, "value": 600 + 20 * i}
             for i, name in enumerate(figure.LOOPS)]
    links = {code: f"./?segment={code}&scenario=F_HT" for code in figure.ORDER}
    links["loops"] = "nephron_types?segment=LDL&scenario=F_HT"
    svg = figure.plate(VALUES, links=links, loops=loops, pinned="mTAL")
    _parse(svg)                                   # '&' in links must be escaped
    assert svg.count("class='nd-go'") == len(figure.ORDER) + 1     # every segment, and the loops
    assert svg.count("target='_self'") == len(figure.ORDER) + 1
    assert svg.count("nd-pinned") == 2            # the wall and the label of the selected segment
    assert "data-seg='loops'" in svg and "data-seg='glom'" in svg and "data-seg='md'" in svg
    assert svg.count("data-part='loops'") == 2 * len(loops)        # two limbs per loop
    # small targets are drawn after (on top of) the wide ones, or they could not be reached
    assert svg.index("data-seg='md'") > svg.index("data-seg='DCT'")
    assert svg.index("data-seg='glom'") > svg.index("data-seg='PT'")


def test_cards_say_what_they_are_given():
    html = figure.cards({
        "mTAL": {"head": "mTAL", "name": "Medullary Thick Ascending Limb",
                 "rows": [("osmolality", "580 → 253 mOsm"), ("Na⁺", "262 → 102 mM")],
                 "series": [580, 500, 400, 300, 253], "hint": "click to select"},
        "glom": {"head": "Glomerulus", "name": "Fluid enters at 100 nl/min & 298 mOsm."},
        "bad":  {"head": "IMCD", "rows": [("status", "did not converge")], "series": [float("nan"), None]},
    })
    _parse(f"<div>{html}</div>")                  # '&' in a note must be escaped
    assert html.count("class='nd-card'") == 3 and "data-for='mTAL'" in html
    assert "580 → 253 mOsm" in html and "Medullary Thick Ascending Limb" in html
    assert html.count("<polyline") == 1           # a line only where there are numbers to draw
    assert figure.sparkline([1.0]) == "" and figure.sparkline([]) == ""


def test_locator_links_and_struck_segments():
    links = {code: f"?segment={code}&solute=K" for code in list(figure.SEGMENTS) + list(figure.GHOST)}
    svg = figure.locator("PT", links=links, names={"IMCD": "Inner Medullary Collecting Duct"},
                         struck={"IMCD"}, depth=0.4, long_loop=True)
    _parse(svg)
    assert svg.count("<a ") == 12
    assert "Inner Medullary Collecting Duct (did not converge)" in svg
    assert svg.count(figure.ACCENT) == 2          # the marked segment and the struck one
    assert "<a " not in figure.locator("PT")      # without links it is only a picture


def test_hover_styles_cover_everything_that_can_be_pointed_at():
    assert set(figure.HOT) == set(figure.SEGMENTS) | {"loops", "glom", "md"}
    for key in figure.HOT:
        assert f"[data-seg='{key}']:hover" in figure.STYLES, key


def test_mark_is_well_formed():
    _parse(figure.mark())
    _parse(figure.mark(background="#ffffff"))
