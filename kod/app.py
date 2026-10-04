"""
app.py — Nephron Data (Layton/Hu) · entry point.

This file is the router. It runs on every page view and does the shared work once:
builds the sidebar menu from the page registry (nav.PAGES), applies the frame (theme,
CSS), renders the sidebar, and then runs the selected page. Page bodies live in views/.

Run with:  streamlit run kod/app.py
"""
import streamlit as st

import nav
from ui_kit import APP_NAME, apply_frame, render_sidebar

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
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_frame()
render_sidebar()
nav.render_origin()

selected.run()

nav.render_explore_bar()
