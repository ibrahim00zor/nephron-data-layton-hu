"""
Smoke and navigation tests, using Streamlit's AppTest (no browser needed).

Run:   python tests/test_app.py        (plain script, prints a report)
or:    pytest tests/                   (if pytest is installed)

What is covered
- every page renders through the router without raising;
- the shared selection travels between pages and is not overwritten by a page that
  cannot show it;
- contextual jumps (home -> model pages, clinical case <-> model pages, scenario ->
  clinical case) land with the right selection and the back link returns to the origin;
- the validation page scores model outputs only.

One AppTest detail: a browser keeps the current page in the URL, AppTest does not follow
an in-app jump (st.switch_page) on the next interaction. `jump()` below therefore clicks
the button and then tells AppTest which page it landed on.
"""
import os
import re
import sys

from streamlit.testing.v1 import AppTest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOD = os.path.join(REPO, "kod")
APP = os.path.join(KOD, "app.py")
sys.path.insert(0, KOD)

import nav  # noqa: E402
from clinical_cases import CASES  # noqa: E402

TIMEOUT = 180


def ok(at):
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def new_app(page_key=None, **context):
    at = ok(AppTest.from_file(APP, default_timeout=TIMEOUT).run())
    for name, value in context.items():
        at.session_state[f"ctx_{name}"] = value
    if page_key or context:
        ok(at.switch_page(nav.path(page_key or "home")).run())
    return at


def page(at):
    return at.session_state["_nav_page"]


def main_select(at, label):
    for box in at.main.selectbox:
        if box.label.startswith(label):
            return box
    raise AssertionError(f"no selectbox starting with {label!r}; have {[b.label for b in at.main.selectbox]}")


def captions(at):
    return " ".join(c.value for c in at.main.caption)


def jump(at, key):
    """Click a navigating button, then sync AppTest to the page the app landed on."""
    ok(at.button(key=key).click().run())
    return ok(at.switch_page(nav.path(page(at))).run())


# ----------------------------------------------------------------------------
def test_every_page_renders_through_the_router():
    at = new_app()
    for key, spec in nav.PAGES.items():
        ok(at.switch_page(spec["path"]).run())
        assert page(at) == key, (key, page(at))                 # the router recognised the page
        assert any("<div class='nd-masthead'>" in m.value for m in at.main.markdown), key   # ... and drew the frame
        assert not at.sidebar.selectbox and not at.sidebar.markdown, key     # nothing lives in a side panel
        assert not at.error, f"{key}: {[e.value for e in at.error]}"


def test_the_selection_is_one_row_in_one_order():
    # every page of the model world shows the same five fields, in the same order and under the
    # same names; a field a page does not use is shown, but cannot be changed there
    for key in nav.in_section(nav.MODEL):
        at = new_app(key)
        labels = [box.label for box in at.main.selectbox][:5]
        assert labels == ["Scenario", "Solute", "Segment", "Nephron", "Compartment"], (key, labels)
    at = new_app("nephron")
    assert main_select(at, "Segment").disabled and not main_select(at, "Solute").disabled
    at = new_app("comparison")
    assert main_select(at, "Scenario").disabled                  # it sets several scenarios side by side
    # a reader chooses between nephron types; "merged" is read for the collecting duct without asking
    at = new_app("segment")
    assert "merged" not in main_select(at, "Nephron").options
    assert main_select(at, "Nephron").options[0] == "Superficial"
    assert "Interstitium" in main_select(at, "Compartment").options or main_select(at, "Compartment").disabled


def test_figures_speak_in_the_readers_words():
    at = new_app("comparison")
    text = " ".join(m.value for m in at.main.markdown)
    assert "<td class='key'>♀ Healthy female (baseline)</td>" in text      # the table of differences
    assert "<td class='key'>F_normal</td>" not in text
    names = {trace["name"] for chart in at.main.get("plotly_chart") for trace in __import__("json").loads(chart.proto.spec)["data"]}
    assert "♀ Healthy female (baseline)" in names and not names & {"F_normal", "F_diab_mod", "F_SGLT2"}
    at = new_app("segment")
    names = {trace["name"] for chart in at.main.get("plotly_chart") for trace in __import__("json").loads(chart.proto.spec)["data"]}
    assert names == {"tubular fluid", "interstitium"}, names
    at = new_app("types")
    names = {trace["name"] for chart in at.main.get("plotly_chart") for trace in __import__("json").loads(chart.proto.spec)["data"]}
    assert "superficial" in names and "juxtamedullary 5" in names and "jux5" not in names


def test_page_files_are_not_in_a_pages_folder():
    """A folder named pages/ re-enables Streamlit's legacy multipage mode, in which a directly
    opened URL (a bookmark, a shared link) runs the page file without the router."""
    assert not os.path.isdir(os.path.join(KOD, "pages"))
    for key, spec in nav.PAGES.items():
        assert os.path.isfile(os.path.join(KOD, spec["path"])), key


def test_selection_travels_between_pages():
    at = new_app("segment")
    main_select(at, "Solute").select("urea").run()
    main_select(at, "Segment").select("mTAL").run()
    main_select(at, "Nephron").select("jux3").run()
    assert [at.session_state[f"ctx_{name}"] for name in ("solute", "segment", "nephron")] == ["urea", "mTAL", "jux3"]

    ok(at.switch_page(nav.path("comparison")).run())
    assert main_select(at, "Solute").value == "urea"
    assert main_select(at, "Segment").value == "mTAL"
    assert main_select(at, "Nephron").value == "jux3"

    ok(at.switch_page(nav.path("nephron")).run())
    assert main_select(at, "Solute").value == "urea"
    assert main_select(at, "Nephron").value == "jux3"
    assert "carries over to the other pages" in captions(at)

    ok(at.switch_page(nav.path("anatomy")).run())
    assert main_select(at, "Segment").value == "mTAL"


def test_restricted_page_does_not_overwrite_selection():
    at = new_app("segment")
    main_select(at, "Segment").select("CCD").run()

    # Nephron Types excludes collecting-duct segments: it shows a fallback and says so ...
    ok(at.switch_page(nav.path("types")).run())
    assert main_select(at, "Segment").value == "PT"
    assert any("belongs to the collecting duct" in i.value for i in at.info)
    # ... but the selection itself is untouched, so other pages still open on CCD.
    assert at.session_state["ctx_segment"] == "CCD"
    ok(at.switch_page(nav.path("segment")).run())
    assert main_select(at, "Segment").value == "CCD"


def _note(at):
    return next(m.value for m in at.main.markdown if "<div class='nd-selection-note'>" in m.value)


def test_reset_selection():
    # the way back to the default selection is a link under the row: the address of this page
    # with nothing in it but what is not being reset (an address resets what it leaves out)
    at = new_app("segment", solute="urea", segment="mTAL", scenario="F_HT")
    link = re.search(r"<a class='nd-go' href='([^']*)' target='_self'>Reset the selection</a>", _note(at))
    assert link and link.group(1) == "segment_profile?scenario=F_HT", link
    at = new_app("segment")
    assert "Reset the selection" not in _note(at)                # nothing to reset


def test_home_question_opens_comparison_and_back_returns_home():
    at = jump(new_app(), "home_q1")
    assert page(at) == "comparison"
    assert main_select(at, "Solute").value == "Na"
    assert main_select(at, "Segment").value == "mTAL"
    assert at.main.multiselect[0].value == ["F_normal", "M_normal"]
    assert "Opened from **Home**" in captions(at)

    at = jump(at, "_nav_back")
    assert page(at) == "home"
    assert "Opened from" not in captions(at)


def test_back_link_disappears_once_the_user_moves_on():
    at = jump(new_app(), "home_q2")
    assert "Opened from **Home**" in captions(at)
    ok(at.switch_page(nav.path("segment")).run())          # user picks another page from the menu
    ok(at.switch_page(nav.path("comparison")).run())       # ... and later comes back
    assert "Opened from" not in captions(at)


def test_scenario_links_to_its_clinical_case():
    at = new_app("segment")
    assert "Clinical case" not in _note(at)                      # F_normal has no case
    main_select(at, "Scenario").select("F_HT").run()
    link = re.search(r"<a class='nd-go' href='([^']*)' target='_self'>Clinical case: [^<]* →</a>", _note(at))
    assert link and link.group(1).startswith("clinical?") and "case=Hypertension" in link.group(1), link
    # following it (events.py hands the address to nav.follow) opens that case
    at.session_state["ctx_case"] = "Hypertension"
    ok(at.switch_page(nav.path("clinical")).run())
    assert any(CASES["Hypertension"]["title"] in m.value for m in at.main.markdown)


def test_clinical_case_round_trip_into_model_world():
    case = CASES["SGLT2"]
    at = new_app("clinical", scenario="F_SGLT2", case="SGLT2")

    at = jump(at, "case_SGLT2_cmp")
    assert page(at) == "comparison"
    assert at.main.multiselect[0].value == ["F_normal", "F_SGLT2"]
    assert main_select(at, "Segment").value == "cTAL" and main_select(at, "Solute").value == "Na"
    assert case["title"] in captions(at)

    at = jump(at, "_nav_back")
    assert page(at) == "clinical" and at.session_state["ctx_case"] == "SGLT2"

    at = jump(at, "case_SGLT2_seg")
    assert page(at) == "segment"
    assert main_select(at, "Scenario").value == "F_SGLT2"
    assert main_select(at, "Segment").value == "cTAL"

    at = jump(at, "_nav_back")
    at = jump(at, "case_SGLT2_ana")
    assert page(at) == "anatomy"
    assert main_select(at, "Segment").value == "cTAL"


def test_clinical_model_numbers_unchanged():
    """Regression guard: the case metrics are computed from the data, not typed in."""
    at = new_app("clinical")
    metrics = {m.label: (m.value, m.delta) for m in at.metric}
    assert metrics["Na load to macula densa"] == ("571 pmol/min", "+38%"), metrics
    assert metrics["Macula densa Na conc."] == ("31 mM", "+19%"), metrics
    assert metrics["PT glucose outlet"] == ("8.5 mM", "+8.4 mM"), metrics


def test_validation_scores_outputs_only():
    """Prescribed inputs are shown but never scored; non-converged segments are not 'failures'."""
    at = new_app("validation")
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Output checks passed"] == "8 / 8", metrics
    text = " ".join(m.value for m in at.main.markdown)
    assert "Prescribed inputs" in text and "Corticomedullary gradient (interstitium)" in text

    # M_normal and F_diab_mod have a non-converged IMCD: the urine check must be n/a, not failed.
    for scenario in ("M_normal", "F_diab_mod"):
        at = new_app("validation", scenario=scenario)
        metrics = {m.label: m.value for m in at.metric}
        assert metrics["Output checks passed"] == "7 / 7", (scenario, metrics)
        text = " ".join(m.value for m in at.main.markdown)
        assert "IMCD did not converge" in text and "nan mOsm" not in text and "-1129" not in text


TESTS = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]

if __name__ == "__main__":
    failed = 0
    for test in TESTS:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:   # report every test, do not stop at the first failure
            failed += 1
            print(f"FAIL  {test.__name__}: {type(exc).__name__}: {str(exc)[:400]}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
