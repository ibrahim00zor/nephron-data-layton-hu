"""
app.py — Nephron Data (Layton/Hu) · entry point.

This file is the router. It runs on every page view and does the shared work once:
builds the sidebar menu from the page registry (nav.PAGES), applies the frame (theme,
CSS), renders the sidebar, and then runs the selected page. Page bodies live in views/.

Run with:  streamlit run kod/app.py
"""
import streamlit as st

import nav
import nephron_figure
import style
from clinical_cases import CASES
from ui_kit import APP_NAME, NEPHRONS, apply_frame, colophon, options, render_sidebar, scenario_list

# Menu: pages grouped into the two worlds (model / clinical) plus data & quality.
page_objects = {
    key: st.Page(spec["path"], title=spec["title"], default=(key == "home"))
    for key, spec in nav.PAGES.items()
}
menu = {}
for section in nav.SECTION_ORDER:
    keys = nav.in_section(section)
    if keys:
        menu[section] = [page_objects[k] for k in keys]

selected = st.navigation(menu, position="sidebar", expanded=True)
current = next((k for k, page in page_objects.items() if page is selected), "home")
nav.set_current_page(current)

st.set_page_config(
    page_title=f"{nav.title(current)} · {APP_NAME}",
    page_icon=nephron_figure.mark(background=style.PAPER),
    layout="wide",
    initial_sidebar_state="expanded",
)
st.logo(nephron_figure.mark(), size="large")
apply_frame()

# A link carries a selection (see nav.href): take it once, when the session starts.
segments, solutes = options()
nav.read_url({
    "scenario": scenario_list(), "compare": scenario_list(), "case": list(CASES),
    "solute": solutes, "segment": segments, "nephron": NEPHRONS,
    "compartment": ["Lumen", "Cell", "Bath"],
})
render_sidebar()
nav.render_origin()
if nav.PAGES[current]["section"]:
    style.kicker(nav.PAGES[current]["section"])     # which of the worlds this page belongs to

selected.run()

nav.render_explore_bar()
colophon()
nav.write_url()     # the address now says what this page shows
