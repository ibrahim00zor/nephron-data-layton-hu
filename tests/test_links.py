"""The selection in the address bar: a link opens the view it describes, and nothing else."""
import os
import re
import sys

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOD = os.path.join(ROOT, "kod")
APP = os.path.join(KOD, "app.py")
sys.path.insert(0, KOD)

import nav  # noqa: E402

TIMEOUT = 180


def open_with(**params):
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for name, value in params.items():
        at.query_params[name] = value
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def selection(at):
    return {name: at.session_state[f"ctx_{name}"] for name in nav.URL_FIELDS
            if f"ctx_{name}" in at.session_state}


def test_a_link_opens_its_selection():
    at = open_with(scenario="F_SGLT2", solute="urea", segment="LDL", nephron="jux3",
                   compare="F_normal,M_normal", case="Hypertension")
    got = selection(at)
    assert got["scenario"] == "F_SGLT2" and got["solute"] == "urea"
    assert got["segment"] == "LDL" and got["nephron"] == "jux3"
    assert got["compare"] == ["F_normal", "M_normal"] and got["case"] == "Hypertension"
    assert at.sidebar.selectbox[0].value == "F_SGLT2"


def test_values_that_do_not_exist_are_ignored():
    at = open_with(scenario="F_normal' OR '1'='1", solute="plutonium", segment="XYZ",
                   nephron="jux9", compartment="Sky", compare="nope,F_HT", case="none")
    got = selection(at)
    assert got.get("scenario", nav.DEFAULTS["scenario"]) == nav.DEFAULTS["scenario"]
    assert got.get("solute", nav.DEFAULTS["solute"]) == nav.DEFAULTS["solute"]
    assert got.get("segment", nav.DEFAULTS["segment"]) == nav.DEFAULTS["segment"]
    assert got.get("nephron", nav.DEFAULTS["nephron"]) == nav.DEFAULTS["nephron"]
    assert got.get("compartment", nav.DEFAULTS["compartment"]) == nav.DEFAULTS["compartment"]
    assert got.get("case", nav.DEFAULTS["case"]) == nav.DEFAULTS["case"]
    assert got["compare"] == ["F_HT"]            # the one scenario that exists is kept


def test_the_address_follows_the_selection():
    at = open_with()
    assert dict(at.query_params) == {}           # defaults are not written
    at.sidebar.selectbox[0].select("F_HT").run()
    assert not at.exception
    assert at.query_params["scenario"] == ["F_HT"] or at.query_params["scenario"] == "F_HT"


def test_the_sidebar_map_links_every_segment():
    at = open_with(segment="mTAL")
    html = " ".join(m.value for m in at.sidebar.markdown)
    links = re.findall(r"<a href='([^']*)'", html)
    assert len(links) == 12, links                # ten segments and the two thin limbs
    assert any("segment=cTAL" in link for link in links)
    assert "data-prev='" in html and "segment=SDL" in html     # the keys step along the nephron
    assert "data-next='" in html
