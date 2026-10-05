"""
nav.py — Page registry, shared selection context, and contextual navigation.

Two ideas live here:

1. REGISTRY (`PAGES`) — the single list of pages, grouped into the project's two worlds
   (model / clinical) plus data & quality. The masthead at the top of every page is drawn
   from it (`render_masthead`): the worlds on the first line, the pages of the current
   world on the second. Adding or removing a page is one entry here plus its file under
   views/.

2. CONTEXT — the user's current selection (scenario, solute, segment, nephron type,
   compartment, the scenarios being compared, the clinical case). It is kept in
   st.session_state under plain, non-widget keys, so it survives page changes: what you
   pick on one page is what the next page opens with. Widgets are bound to it with
   `select()` / `multiselect()`, and `go()` jumps to another page with a chosen context.
"""
import html
import os
from urllib.parse import parse_qsl, urlencode

import streamlit as st

# ============================================================
#  Page registry
# ============================================================
MODEL = "Model world"
CLINICAL = "Clinical world"
QUALITY = "Data & quality"
SECTION_ORDER = ["", MODEL, CLINICAL, QUALITY]
WORLDS = (MODEL, CLINICAL, QUALITY)      # what the first line of the masthead offers

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
    "anatomy":    {"path": "views/anatomy.py",         "title": "Interactive Anatomy",        "section": MODEL},
    "clinical":   {"path": "views/clinical.py",        "title": "Clinical Cases",             "section": CLINICAL},
    "validation": {"path": "views/validation.py",      "title": "Validation",                 "section": QUALITY},
    "integrity":  {"path": "views/data_integrity.py",  "title": "Data Integrity",             "section": QUALITY},
    "provenance": {"path": "views/provenance.py",      "title": "Model & Provenance",         "section": QUALITY},
    "about":      {"path": "views/about.py",           "title": "About",                      "section": ""},
}


def path(page):
    return PAGES[page]["path"]


def title(page):
    return PAGES[page]["title"]


def slug(page):
    """A page as one word that can be part of a class name: the name of its file."""
    return os.path.splitext(os.path.basename(PAGES[page]["path"]))[0]


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


# ============================================================
#  The selection in the address bar
# ============================================================
# The address of a page always carries the selection it shows (only what differs from the
# defaults), so copying the address gives a link to exactly this view. A link opened in a
# new session is read once, at its start. The drawings link to pages the same way.
URL_FIELDS = ("scenario", "solute", "segment", "nephron", "compartment", "compare", "case")
_URL_READ = "_nav_url_read"


def url_path(page):
    """Address of a page: the name of its file; the Home page is the root."""
    if page == "home":
        return "./"
    return slug(page)


def query(**changes):
    """The selection (with `changes` applied) as URL parameters, defaults left out."""
    out = {}
    for name in URL_FIELDS:
        value = changes.get(name, get(name))
        if value != DEFAULTS[name]:
            out[name] = ",".join(value) if isinstance(value, (list, tuple)) else str(value)
    return out


def href(page=None, **changes):
    """Link to `page` (this page if omitted) on the current selection with `changes` applied."""
    params = urlencode(query(**changes))
    return url_path(page or current_page()) + (f"?{params}" if params else "")


def _apply(fields, allowed, reset):
    """Put the fields of an address into the selection. Only values listed in `allowed`
    are accepted. With `reset`, a field the address does not mention goes back to its
    default (an address says everything about a view; what it leaves out is the default)."""
    for name in URL_FIELDS:
        raw = fields.get(name)
        if isinstance(DEFAULTS[name], list):
            values = [v for v in raw.split(",") if v in allowed.get(name, ())] if raw else []
            if values:
                put(**{name: values})
                continue
        elif raw in allowed.get(name, ()):
            put(**{name: raw})
            continue
        if reset:
            put(**{name: _default(name)})


def read_url(allowed):
    """Once per session: take the selection from the address. `allowed` lists the values
    each field may take; anything else in the address is ignored."""
    if st.session_state.get(_URL_READ):
        return
    st.session_state[_URL_READ] = True
    _apply({name: st.query_params.get(name) for name in URL_FIELDS}, allowed, reset=False)


def follow(address, allowed):
    """Apply the address of an internal link ("page?field=value&...") to this session, as
    opening it would. Returns the page it leads to (None if the address names no page)."""
    name, _, params = str(address).partition("?")
    pages = {url_path(page).strip("./"): page for page in PAGES}
    page = pages.get(name.strip("./"))
    if page is None:
        return None
    _apply(dict(parse_qsl(params)), allowed, reset=True)
    st.session_state.pop(_ORIGIN_KEY, None)
    return page


def write_url():
    """Every run: keep the address in step with the selection."""
    wanted = query()
    if st.query_params.to_dict() != wanted:
        st.query_params.from_dict(wanted)


def neighbours(order, name="segment"):
    """Links to the previous and the next value of a field along `order` (None at the ends)."""
    current = get(name)
    if current not in order:
        return None, None
    i = order.index(current)
    before = href(**{name: order[i - 1]}) if i > 0 else None
    after = href(**{name: order[i + 1]}) if i < len(order) - 1 else None
    return before, after


# ============================================================
#  The masthead: where you are, and where you can go
# ============================================================
_FIGURES = "_nav_figures"     # how many figures the page has shown so far (see ui_kit.figure)


def _nav_link(page, label, on=False, extra=""):
    marked = " on" if on else ""
    return (f"<a class='nd-go nd-nav{marked}{extra}' href='{html.escape(href(page), quote=True)}' "
            f"target='_self'>{label}</a>")


def render_masthead(mark):
    """The head of every page. First line: the name (a link to the Home page) and the worlds.
    Second line: the pages of the world the reader is in. `mark` is the logo, as SVG.

    Every entry is an ordinary link that carries the selection (see `href`), answered in
    place by events.py."""
    here = current_page()
    section = PAGES[here]["section"]
    worlds = "".join(
        _nav_link(in_section(world)[0], html.escape(world), on=(world == section))
        for world in WORLDS if in_section(world)
    )
    worlds += _nav_link("about", "About", on=(here == "about"))
    pages = ""
    if section in WORLDS and len(in_section(section)) > 1:
        pages = "<nav class='nd-pages'>" + "".join(
            _nav_link(page, html.escape(title(page)), on=(page == here)) for page in in_section(section)
        ) + "</nav>"
    st.markdown(
        "<div class='nd-masthead'>"
        + _nav_link("home", f"{mark}<span>Nephron Data</span><small>Layton/Hu</small>", extra=" nd-brand")
        + f"<nav class='nd-worlds'>{worlds}</nav></div>{pages}",
        unsafe_allow_html=True,
    )


# ============================================================
#  Turning the page
# ============================================================
# A page is drawn inside one block (app.py), named after it. The block of a page that has
# just been opened fades in; the block of a page that is being left steps back at once, on
# the click (events.py names it on <body>), so that there is no moment at which the old page
# is cut off and the new one is not there yet. Each page has a fade of its own name: a block
# that changes its name starts its fade again, a block that stays where it is does not, so
# changing a selection on a page moves nothing.
def body_key(page):
    return f"nd_page_{slug(page)}"


def _turning():
    rules = []
    for page in PAGES:
        name = slug(page)
        leaving = "home" if page == "home" else name       # what events.py calls the page
        rules.append(
            f"@keyframes nd-arrive-{name} {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}\n"
            f".st-key-{body_key(page)} {{ animation: nd-arrive-{name} .34s ease-out; }}\n"
            f"body[data-leaving='{leaving}'] .st-key-{body_key(page)} "
            f"{{ opacity: 0; transition: opacity .14s ease-in; animation: none; }}")
    rules.append("@keyframes nd-settle-a { from { opacity: 0.25; } to { opacity: 1; } }\n"
                 "@keyframes nd-settle-b { from { opacity: 0.25; } to { opacity: 1; } }\n"
                 ".nd-settle-a { animation: nd-settle-a .26s ease-out; }\n"
                 ".nd-settle-b { animation: nd-settle-b .26s ease-out; }")
    rules.append("@media (prefers-reduced-motion: reduce) { [class*='st-key-nd_page_'], "
                 ".nd-settle-a, .nd-settle-b { animation: none !important; transition: none !important; } }")
    return "<style>" + "\n".join(rules) + "</style>"


TURNING = _turning()


def changed(name, value):
    """A class for a block that shows `value`: "nd-settle-a" or "nd-settle-b", the other one
    each time the value is not what it was. The two fade in alike, so what a block says
    settles in softly when it changes, and stays still when it does not."""
    seen = st.session_state.setdefault("_nav_settle", {})
    last, side = seen.get(name, (None, "b"))
    if last is None:
        side = "a"
    elif value != last:
        side = "b" if side == "a" else "a"
    seen[name] = (value, side)
    return f"nd-settle-{side}"


def next_figure():
    """The number of the next figure on this page (app.py starts the count again each run)."""
    st.session_state[_FIGURES] = st.session_state.get(_FIGURES, 0) + 1
    return st.session_state[_FIGURES]


def reset_figures():
    st.session_state[_FIGURES] = 0


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
    st.caption(f"Your selection (**{selection_summary()}**) carries over to the other pages of the "
               f"{MODEL.lower()}. Continue in:")
    row = st.container(horizontal=True, gap="medium")
    for other in others:
        link(row, other)
