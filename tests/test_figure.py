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


def test_mark_is_well_formed():
    _parse(figure.mark())
    _parse(figure.mark(background="#ffffff"))
