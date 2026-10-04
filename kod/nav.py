"""
nav.py — Page registry, shared selection context, and contextual navigation.

Two ideas live here:

1. REGISTRY (`PAGES`) — the single list of pages. app.py builds the sidebar menu from it,
   grouped into the project's two worlds (model / clinical) plus data & quality. Adding or
   removing a page is one entry here plus its file under views/.

2. CONTEXT — the user's current selection (scenario, solute, segment, nephron type,
   compartment, the scenarios being compared, the clinical case). It is kept in
   st.session_state under plain, non-widget keys, so it survives page changes: what you
   pick on one page is what the next page opens with. Widgets are bound to it with
   `select()` / `multiselect()`, and `go()` jumps to another page with a chosen context.
"""
import streamlit as st

# ============================================================
#  Page registry
# ============================================================
MODEL = "Model world"
CLINICAL = "Clinical world"
QUALITY = "Data & quality"
SECTION_ORDER = ["", MODEL, CLINICAL, QUALITY]

# key -> path (relative to app.py), menu title, section. Order here is menu order.
# The folder is deliberately NOT called "pages": Streamlit auto-discovers a pages/ folder as
# an old-style multipage app, and a directly opened URL would then bypass the router.
PAGES = {
    "home":       {"path": "views/home.py",            "title": "Home",                       "section": ""},
    "segment":    {"path": "views/segment_profile.py", "title": "Segment Profile",            "section": MODEL},
    "nephron":    {"path": "views/whole_nephron.py",   "title": "Whole Nephron",              "section": MODEL},
    "types":      {"path": "views/nephron_types.py",   "title": "Nephron Types",              "section": MODEL},
    "comparison": {"path": "views/comparison.py",      "title": "Comparison",                 "section": MODEL},
    "transporters": {"path": "views/transporters.py",  "title": "Transporters",               "section": MODEL},
    "anatomy":    {"path": "views/anatomy.py",         "title": "Interactive Anatomy (BETA)", "section": MODEL},
    "clinical":   {"path": "views/clinical.py",        "title": "Clinical Cases",             "section": CLINICAL},
    "validation": {"path": "views/validation.py",      "title": "Validation",                 "section": QUALITY},
    "integrity":  {"path": "views/data_integrity.py",  "title": "Data Integrity",             "section": QUALITY},
}


def path(page):
    return PAGES[page]["path"]


def title(page):
    return PAGES[page]["title"]


def in_section(section, exclude=None):
    return [k for k, spec in PAGES.items() if spec["section"] == section and k != exclude]


# ============================================================
#  Shared selection context
# ============================================================
DEFAULTS = {
    "scenario": "F_normal",
    "solute": "Na",
    "segment": "PT",
    "nephron": "sup",
    "compartment": "Lumen",
    "compare": ["F_normal", "F_diab_mod", "F_SGLT2"],
    "case": "SGLT2",
}
SELECTION = ("solute", "segment", "nephron", "compartment")   # what "Reset selection" restores

_PAGE_KEY = "_nav_page"       # key of the page being rendered (set by app.py each run)
_ORIGIN_KEY = "_nav_origin"   # where a contextual jump came from (for the back link)


def _k(name):
    return f"ctx_{name}"


def _default(name):
    v = DEFAULTS[name]
    return list(v) if isinstance(v, list) else v


def get(name):
    """Current value of a context field (initialised to its default on first use)."""
    if _k(name) not in st.session_state:
        st.session_state[_k(name)] = _default(name)
    return st.session_state[_k(name)]


def put(**selection):
    """Set context fields directly (used by jumps and buttons)."""
    for name, value in selection.items():
        st.session_state[_k(name)] = list(value) if isinstance(value, (list, tuple)) else value


def reset_selection():
    put(**{name: _default(name) for name in SELECTION})


def is_default_selection():
    return all(get(name) == DEFAULTS[name] for name in SELECTION)


def current_page():
    return st.session_state.get(_PAGE_KEY, "home")


def set_current_page(page):
    st.session_state[_PAGE_KEY] = page


# ------------------------------------------------------------
#  Widgets bound to the context
# ------------------------------------------------------------
def _push(name, wkey):
    st.session_state[_k(name)] = st.session_state[wkey]


def _wkey(name):
    return f"_w_{current_page()}_{name}"


def select(container, label, options, name, fallback=None, **kwargs):
    """Selectbox bound to context field `name`.

    If the context value is not offered on this page (e.g. a collecting-duct segment on a
    page that excludes them), the page shows `fallback` WITHOUT overwriting the context,
    so the original choice is still there on pages that can show it. The context changes
    only when the user picks something.
    """
    options = list(options)
    current = get(name)
    if current in options:
        shown = current
    elif fallback in options:
        shown = fallback
    else:
        shown = options[0]
    wkey = _wkey(name)
    st.session_state[wkey] = shown
    return container.selectbox(label, options, key=wkey, on_change=_push, args=(name, wkey), **kwargs)


def multiselect(container, label, options, name, fallback=None, **kwargs):
    """Multiselect bound to a list-valued context field (same rules as `select`)."""
    options = list(options)
    shown = [v for v in get(name) if v in options]
    if not shown:
        shown = [v for v in (fallback or []) if v in options]
    wkey = _wkey(name)
    st.session_state[wkey] = shown
    return container.multiselect(label, options, key=wkey, on_change=_push, args=(name, wkey), **kwargs)


# ============================================================
#  Contextual navigation
# ============================================================
def go(page, back_label=None, **selection):
    """Jump to `page` with the given selection applied.

    With `back_label`, the target page shows where the user came from and a link back.
    """
    put(**selection)
    if back_label:
        st.session_state[_ORIGIN_KEY] = {"from": current_page(), "target": page, "label": back_label}
    else:
        st.session_state.pop(_ORIGIN_KEY, None)
    st.switch_page(path(page))


def link(container, page, label=None):
    """Plain link to a page. The shared context travels with the user automatically."""
    container.page_link(path(page), label=label or title(page))


def render_origin():
    """Back link shown right after a contextual jump; dropped as soon as the user moves on."""
    origin = st.session_state.get(_ORIGIN_KEY)
    if not origin:
        return
    if origin["target"] != current_page() or origin["from"] not in PAGES:
        st.session_state.pop(_ORIGIN_KEY, None)
        return
    left, right = st.columns([4, 1.5])
    left.caption(f"Opened from **{title(origin['from'])}** — {origin['label']}")
    if right.button(f"← Back to {title(origin['from'])}", key="_nav_back", width="stretch"):
        st.session_state.pop(_ORIGIN_KEY, None)
        st.switch_page(path(origin["from"]))


def selection_summary():
    return " · ".join(str(get(name)) for name in SELECTION)


def render_explore_bar():
    """Footer on model-world pages: the same selection, continued on another page."""
    page = current_page()
    if PAGES.get(page, {}).get("section") != MODEL:
        return
    others = in_section(MODEL, exclude=page)
    if not others:
        return
    st.markdown("---")
    st.caption(f"Your selection (**{selection_summary()}**) carries over to the other pages — continue in:")
    for column, other in zip(st.columns(len(others)), others):
        link(column, other)
