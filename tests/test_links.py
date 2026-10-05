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


def scenario_field(at):
    """The field the scenario is chosen in (on the Home page it stands beside the figure)."""
    return next(box for box in at.main.selectbox if box.label.startswith(("Scenario", "The figure shows")))


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
    assert scenario_field(at).value == "F_SGLT2"


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
    scenario_field(at).select("F_HT").run()
    assert not at.exception
    assert at.query_params["scenario"] == ["F_HT"] or at.query_params["scenario"] == "F_HT"


def test_the_small_map_links_every_segment():
    at = open_with(segment="mTAL")
    at.switch_page(nav.path("segment")).run()        # the map closes the selection row of a model page
    assert not at.exception, [str(e.value) for e in at.exception]
    html = next(m.value for m in at.main.markdown if "class='nd-where'" in m.value)
    links = re.findall(r"<a class='nd-go' href='([^']*)'", html)
    assert len(links) == 12, links                # ten segments and the two thin limbs
    assert any("segment=cTAL" in link for link in links)
    assert "data-prev='" in html and "segment=SDL" in html     # the keys step along the nephron
    assert "data-next='" in html


FOLLOW = """
import sys
sys.path.insert(0, {kod!r})
import streamlit as st
import nav

allowed = {{"scenario": ["F_normal", "F_HT"], "compare": ["F_normal", "F_HT"], "case": ["SGLT2"],
           "solute": ["Na", "K", "urea"], "segment": ["PT", "mTAL", "LDL"],
           "nephron": ["sup", "jux3"], "compartment": ["Lumen", "Cell", "Bath"]}}
nav.put(scenario="F_HT", solute="urea", nephron="jux3", segment="PT")
page = nav.follow({address!r}, allowed)
st.write(repr(page))
st.write("|".join(str(nav.get(name)) for name in ("scenario", "solute", "segment", "nephron")))
"""


def follow(address):
    at = AppTest.from_string(FOLLOW.format(kod=KOD, address=address), default_timeout=TIMEOUT).run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at.markdown[0].value.strip("`'"), at.markdown[1].value


def test_a_link_clicked_inside_the_app_acts_like_opening_it():
    # what the address names is applied; what it leaves out goes back to its default
    page, state = follow("segment_profile?segment=mTAL&solute=K")
    assert page == "segment" and state == "F_normal|K|mTAL|sup"
    page, state = follow("?scenario=F_HT&nephron=jux3")          # the Home page
    assert page == "home" and state == "F_HT|Na|PT|jux3"
    page, state = follow("./?segment=LDL")
    assert page == "home" and state == "F_normal|Na|LDL|sup"


def test_a_link_to_nowhere_changes_nothing():
    page, state = follow("no_such_page?segment=mTAL")
    assert page == "None" and state == "F_HT|urea|PT|jux3"
    page, state = follow("segment_profile?segment=DROP TABLE&solute=plutonium")
    assert page == "segment" and state == "F_normal|Na|PT|sup"   # unknown values fall to the defaults
