"""The drawing of the Interactive Anatomy page, and how the site moves between pages."""
import os
import re
import sys
import xml.dom.minidom

from streamlit.testing.v1 import AppTest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOD = os.path.join(REPO, "kod")
APP = os.path.join(KOD, "app.py")
sys.path.insert(0, KOD)

import anatomy_figure as anatomy   # noqa: E402
import events                      # noqa: E402
import nav                         # noqa: E402

TIMEOUT = 180


def _values(codes, start=100.0):
    return {code: {"entry": start + 10 * i, "exit": start + 14 * i + 3,
                   "profile": [(k / 20, start + 10 * i + k) for k in range(21)]}
            for i, code in enumerate(codes)}


def _draw(long_loop=False, leave_out=(), **more):
    shown = anatomy.order(long_loop)
    values = _values([code for code in shown if code not in leave_out])
    flow = {code: 5.0 + 8 * i for i, code in enumerate(shown)}
    links = {code: f"anatomy?segment={code}&scenario=F_HT" for code in shown}
    return anatomy.figure(shown, values, 8.0, 262.0, anatomy.YL_OR_RD, "Na concentration", "mM",
                          flow, 0.9, 100.0, [(0.0, 300.0), (0.55, 420.0), (1.0, 734.0)],
                          links=links, long_loop=long_loop, **more)


def test_the_drawing_is_well_formed_and_every_segment_can_be_clicked():
    for long_loop in (False, True):
        svg = _draw(long_loop)
        xml.dom.minidom.parseString(svg)              # '&' in links must be escaped
        shown = anatomy.order(long_loop)
        for code in shown:
            assert f"id='na-p-{code}'" in svg and f"class='nd-wall' data-part='{code}'" in svg, code
            assert f"class='na-tube' data-part='{code}'" in svg, code
            # once on the drawing, once in the chart beside it
            assert svg.count(f"data-seg='{code}'") == 2, code
        assert svg.count("class='nd-go'") == 2 * len(shown)


def test_nothing_is_left_for_the_browser_to_filter_or_fetch():
    # the old drawing was a document in a frame: D3 and two fonts from elsewhere, three filters
    svg = _draw(True)
    assert "<filter" not in svg and "filter=" not in svg
    assert "http://" not in svg.replace("http://www.w3.org/2000/svg", "") and "https://" not in svg
    with open(os.path.join(KOD, "views", "anatomy.py"), encoding="utf-8") as f:
        page = f.read()
    assert "iframe" not in page and "components" not in page
    assert not os.path.exists(os.path.join(KOD, "d3_components"))


def test_the_short_loop_is_closed_and_the_tubule_is_one_line():
    short, long_ = anatomy.layout(False), anatomy.layout(True)
    assert "LDL" not in short and "LAL" not in short          # as in the model: no thin limbs below it
    assert list(long_) == anatomy.SEGMENTS
    for lines in (short, long_):
        codes = list(lines)
        for before, after in zip(codes, codes[1:]):
            # each segment starts exactly where the one before it ends
            assert lines[before]["firm"].split(" ")[-1] == lines[after]["firm"].split(" ")[0][1:], (before, after)
            assert lines[before]["length"] > 10
    # the bend of the short loop lies above the outer-inner medullary boundary
    numbers = [float(v) for v in re.findall(r"-?\d+\.?\d*", short["mTAL"]["firm"])]
    assert max(numbers[1::2]) < anatomy.OUTER_END


def test_colour_thickness_and_pace_follow_the_data():
    assert anatomy.shade(anatomy.YL_OR_RD, 8, 8, 262) == anatomy.YL_OR_RD[0]
    assert anatomy.shade(anatomy.YL_OR_RD, 262, 8, 262) == anatomy.YL_OR_RD[-1]
    assert anatomy.shade(anatomy.YL_OR_RD, -5, 8, 262) == anatomy.YL_OR_RD[0]      # clamped
    assert anatomy.shade(anatomy.VIRIDIS, 5, 5, 5) == anatomy.VIRIDIS[0]           # no span, no error
    assert anatomy.thickness(0.9, 0.9, 100) == 3 and anatomy.thickness(100, 0.9, 100) == 20
    assert anatomy.thickness(10, 0.9, 100) < anatomy.thickness(50, 0.9, 100)
    assert anatomy.pace(100, 0.9, 100) < anatomy.pace(10, 0.9, 100)                # more flow, faster
    svg = _draw()
    assert f"stop-color='{anatomy.shade(anatomy.YL_OR_RD, 100.0, 8.0, 262.0)}'" in svg   # PT enters at 100


def test_ticks_are_round_and_lie_inside():
    for low, high in ((7.3, 268.1), (0.0, 1.0), (-3.0, 3.0), (1200.0, 98000.0), (5.0, 5.0)):
        first, step, count = anatomy.ticks(low, high)
        assert step > 0 and 1 <= count <= 12, (low, high, count)
        assert first >= low - 1e-9 and first + (count - 1) * step <= max(high, first) + 1e-9


def test_a_segment_without_data_is_left_empty():
    svg = _draw(leave_out=("IMCD",))
    xml.dom.minidom.parseString(svg)
    wall = re.search(r"<use href='#na-p-IMCD' class='nd-wall'[^>]*>", svg).group(0)
    assert "stroke-dasharray" in wall                       # a broken outline
    assert "stroke-dasharray" not in re.search(r"<use href='#na-p-PT' class='nd-wall'[^>]*>", svg).group(0)
    assert "data-for='IMCD'" not in svg                     # nothing to mark on the scale or in the chart
    assert svg.count("class='na-line'") == len(anatomy.order(False)) - 1


def test_the_flow_can_be_switched_off():
    assert "class='na-dots'" in _draw(dots=True)
    assert "class='na-dots'" not in _draw(dots=False)
    assert "prefers-reduced-motion" in anatomy.STYLES       # and it stands still for those who ask


def test_the_selection_is_marked_beside_the_drawing_not_in_it():
    rule = anatomy.pin("cTAL", 12.4)
    assert rule.startswith("<style class='nd-pin'>") and "[data-part='cTAL']" in rule
    assert "nd-pin" not in _draw()


def _open(page, **context):
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    assert not at.exception, [str(e.value) for e in at.exception]
    for name, value in context.items():
        at.session_state[f"ctx_{name}"] = value
    at.switch_page(nav.path(page)).run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def test_the_page_draws_the_selection_and_follows_the_colour_choice():
    at = _open("anatomy", segment="cTAL", solute="K")
    text = " ".join(m.value for m in at.main.markdown)
    assert "<figure class='nd-plate na-plate'>" in text and "K concentration (mM)" in text
    assert ".na-plate .nd-wall[data-part='cTAL']" in text   # the selected segment is marked
    assert "Selected on the drawing" in text and "<b>cTAL</b>" in text
    assert "target='_self' data-seg='LDL'" not in text      # a superficial nephron has no thin limbs
    assert "target='_self' data-seg='mTAL'" in text
    colour = next(box for box in at.main.selectbox if box.label.startswith("Colour shows"))
    colour.select("load (flux)").run()
    assert not at.exception, [str(e.value) for e in at.exception]
    text = " ".join(m.value for m in at.main.markdown)
    assert "K load (pmol/min)" in text and "K concentration (mM)" not in text
    # a juxtamedullary nephron has the long loop
    at = _open("anatomy", nephron="jux3", segment="LDL")
    text = " ".join(m.value for m in at.main.markdown)
    assert "target='_self' data-seg='LDL'" in text and "target='_self' data-seg='LAL'" in text
    assert ".na-plate .nd-wall[data-part='LDL']" in text


def test_a_collecting_duct_without_data_is_said_so():
    at = _open("anatomy", scenario="M_normal")              # IMCD did not converge there
    text = " ".join(m.value for m in at.main.markdown)
    assert "IMCD has no valid data" in text and "did not converge" in text


# ----------------------------------------------------------------------------
#  Moving between pages
# ----------------------------------------------------------------------------
def test_the_name_in_the_masthead_leads_home():
    # the address of the Home page is "./"; the script used to send it as "", which says nothing
    assert "|| './'" in events.JS
    allowed = {"scenario": ["F_normal"], "compare": ["F_normal"], "case": ["SGLT2"], "solute": ["Na", "K"],
               "segment": ["PT", "mTAL"], "nephron": ["sup"], "compartment": ["Lumen"]}
    script = f"""
import sys
sys.path.insert(0, {KOD!r})
import streamlit as st
import nav
nav.put(segment="mTAL")
st.session_state["to"] = [nav.follow(address, {allowed!r}) for address in ("./", "./?solute=K", "about", "", "nowhere")]
st.session_state["solute"] = nav.get("solute")
"""
    at = AppTest.from_string(script, default_timeout=60).run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert at.session_state["to"] == ["home", "home", "about", "home", None]
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    masthead = next(m.value for m in at.main.markdown if "<div class='nd-masthead'>" in m.value)
    assert re.search(r"<a class='nd-go nd-nav nd-brand' href='\./'", masthead)


def test_every_page_is_one_block_that_can_be_turned():
    for page in nav.PAGES:
        name = nav.slug(page)
        assert f".st-key-{nav.body_key(page)} " in nav.TURNING, page
        assert f"@keyframes nd-arrive-{name} " in nav.TURNING, page
    # the script names the page that is being left the way the stylesheet expects it
    assert "body[data-leaving='home'] .st-key-nd_page_home " in nav.TURNING
    assert "setAttribute('data-leaving', here() || 'home')" in events.JS
    assert "prefers-reduced-motion" in nav.TURNING


def test_a_block_settles_only_when_what_it_shows_changes():
    script = f"""
import sys
sys.path.insert(0, {KOD!r})
import streamlit as st
import nav
st.session_state["seen"] = [nav.changed("x", v) for v in ("PT", "PT", "S3", "S3", "PT")]
"""
    at = AppTest.from_string(script, default_timeout=60).run()
    a, b = "nd-settle-a", "nd-settle-b"
    assert at.session_state["seen"] == [a, a, b, b, a]


def test_the_paper_is_two_pictures_not_two_filters():
    import style
    assert "feTurbulence" not in style.PAPER_TEXTURE and "--nd-grain" in style.PAPER_TEXTURE
    assert "--nd-grain" in events.JS and "--nd-mottle" in events.JS
    # until the pictures are there the page has their mean tone, so nothing shifts when they arrive
    assert "linear-gradient(rgba(149, 137, 115, 0.047)" in style.PAPER_TEXTURE
    assert "[149, 137, 115], 0.047" in events.JS
