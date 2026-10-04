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
        assert len(at.sidebar.selectbox) == 1, key              # ... and rendered the sidebar
        assert not at.error, f"{key}: {[e.value for e in at.error]}"


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
    assert "urea · mTAL · jux3" in " ".join(m.value for m in at.sidebar.markdown)

    ok(at.switch_page(nav.path("comparison")).run())
    assert main_select(at, "Solute").value == "urea"
    assert main_select(at, "Segment").value == "mTAL"
    assert main_select(at, "Nephron type").value == "jux3"

    ok(at.switch_page(nav.path("nephron")).run())
    assert main_select(at, "Solute").value == "urea"
    assert main_select(at, "Nephron type").value == "jux3"
    assert "carries over to the other pages" in captions(at)

    ok(at.switch_page(nav.path("anatomy")).run())
    assert main_select(at, "Highlighted segment").value == "mTAL"


def test_restricted_page_does_not_overwrite_selection():
    at = new_app("segment")
    main_select(at, "Segment").select("CCD").run()

    # Nephron Types excludes collecting-duct segments: it shows a fallback and says so ...
    ok(at.switch_page(nav.path("types")).run())
    assert main_select(at, "Segment").value == "PT"
    assert any("collecting-duct segment" in i.value for i in at.info)
    # ... but the selection itself is untouched, so other pages still open on CCD.
    assert at.session_state["ctx_segment"] == "CCD"
    ok(at.switch_page(nav.path("segment")).run())
    assert main_select(at, "Segment").value == "CCD"


def test_reset_selection():
    at = new_app("segment", solute="urea", segment="mTAL")
    ok(at.button(key="_sidebar_reset").click().run())
    assert main_select(at, "Solute").value == "Na" and main_select(at, "Segment").value == "PT"
    assert not [b for b in at.sidebar.button if b.key == "_sidebar_reset"]   # nothing left to reset


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
    at = new_app()
    assert not [b for b in at.sidebar.button if b.key == "_sidebar_case"]   # F_normal has no case
    at.sidebar.selectbox[0].select("F_HT").run()
    at = jump(at, "_sidebar_case")
    assert page(at) == "clinical"
    assert at.session_state["ctx_case"] == "Hypertension"
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
    assert at.sidebar.selectbox[0].value == "F_SGLT2"
    assert main_select(at, "Segment").value == "cTAL"

    at = jump(at, "_nav_back")
    at = jump(at, "case_SGLT2_ana")
    assert page(at) == "anatomy"
    assert main_select(at, "Highlighted segment").value == "cTAL"


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
