"""
app.py — Nephron Data (Layton/Hu) · entry point.

This file is the frame. It runs on every page view and does the shared work once: routes
to the selected page, writes the stylesheet, answers a link that was just followed, draws
the masthead (the worlds and their pages), runs the page, and ends with the colophon. The
selection row under the masthead is drawn by the page itself (ui_kit.selection), since a page
says which fields it offers. Page bodies live in views/.

Run with:  streamlit run kod/app.py
"""
import streamlit as st

import events
import nav
import nephron_figure
import style
from clinical_cases import CASES
from ui_kit import APP_NAME, NEPHRONS, apply_frame, colophon, options, scenario_list, selection_in_words

# The pages. Streamlit only routes; the menu itself is the masthead (nav.render_masthead),
# so that it can show the two worlds and stay in view while the page scrolls.
page_objects = {
    key: st.Page(spec["path"], title=spec["title"], default=(key == "home"))
    for key, spec in nav.PAGES.items()
}
selected = st.navigation(list(page_objects.values()), position="hidden")
current = next((k for k, page in page_objects.items() if page is selected), "home")
nav.set_current_page(current)

st.set_page_config(
    page_title=f"{nav.title(current)} · {APP_NAME}",
    page_icon=nephron_figure.mark(background=style.PAPER),
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_frame()

# A link carries a selection (see nav.href). Opened from outside, it is read once, when the
# session starts. Clicked inside the app, it is answered in place (see events.py).
segments, solutes = options()
allowed = {
    "scenario": scenario_list(), "compare": scenario_list(), "case": list(CASES),
    "solute": solutes, "segment": segments, "nephron": NEPHRONS,
    "compartment": ["Lumen", "Cell", "Bath"],
}
nav.read_url(allowed)
followed = events.went(current)
if followed:
    target = nav.follow(followed, allowed)
    if target and target != current:
        st.switch_page(nav.path(target))
nav.render_masthead(nephron_figure.mark())

# Everything under the masthead is one block, named after the page, so that a page can be
# turned as a whole (see "Turning the page" in nav.py).
with st.container(key=nav.body_key(current)):
    nav.render_origin()
    nav.reset_figures()      # "Fig. 1" is the first figure of whatever page follows

    selected.run()

    nav.render_explore_bar(selection_in_words())
    colophon()
nav.write_url()     # the address now says what this page shows
