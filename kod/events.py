"""
events.py — What the page does when it is pointed at, clicked or typed at.

One small script, mounted once per run by app.py, listens on the whole page:

- A click on an internal link (class "nd-go") is answered in place. The address of the
  link is sent to Python, which applies it (nav.follow) and renders the result, without
  starting a new session. The href stays a real address, so opening the link in a new
  tab, copying it, or a browser without JavaScript still works.
- Pointing at a part of a figure that has a card (an element with data-seg inside a
  .nd-plate, and a .nd-card[data-for] with the same key) shows that card beside the pointer.
- Keys: "[" and "]" step along the nephron (the addresses are on the sidebar map), "?"
  shows the keys, Escape hides them.
- The pilcrow beside a page title copies the address of the view.

The script is trusted code written here; nothing a visitor types reaches it.
"""
import streamlit as st
from streamlit.errors import StreamlitAPIException

JS = """
export default function (component) {
  const nd = (window.__nd = window.__nd || {});
  nd.go = (address) => component.setTriggerValue('went', address);   // always the live session
  if (nd.ready) return;
  nd.ready = true;

  // ---- an internal link is answered in place
  const address = (href) => {
    const url = new URL(href, window.location.href);
    return url.pathname.split('/').pop() + url.search;
  };

  // ---- the card beside the pointer
  let card = null;
  const hide = () => { if (card) { card.classList.remove('on'); card = null; } };
  const place = (x, y) => {
    const box = card.getBoundingClientRect();
    let left = x + 18, top = y + 16;
    if (left + box.width > window.innerWidth - 8) left = x - box.width - 18;
    if (top + box.height > window.innerHeight - 8) top = y - box.height - 16;
    card.style.left = Math.max(8, left) + 'px';
    card.style.top = Math.max(8, top) + 'px';
  };
  document.addEventListener('mousemove', (e) => {
    const hot = e.target.closest ? e.target.closest('.nd-plate [data-seg]') : null;
    if (!hot) { hide(); return; }
    const next = hot.closest('.nd-plate').querySelector(
      '.nd-card[data-for="' + hot.getAttribute('data-seg') + '"]');
    if (next !== card) { hide(); card = next; if (card) card.classList.add('on'); }
    if (card) place(e.clientX, e.clientY);
  }, { passive: true });
  document.addEventListener('scroll', hide, { passive: true, capture: true });

  const flash = (message) => {
    let el = document.getElementById('nd-flash');
    if (!el) { el = document.createElement('div'); el.id = 'nd-flash'; document.body.appendChild(el); }
    el.textContent = message;
    el.classList.add('on');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('on'), 1800);
  };

  document.addEventListener('click', (e) => {
    if (!e.target.closest) return;
    const pilcrow = e.target.closest('[data-testid="stHeaderActionElements"] a');
    if (pilcrow && navigator.clipboard) {
      setTimeout(() => navigator.clipboard.writeText(window.location.href)
        .then(() => flash('link to this view copied')), 60);
      return;
    }
    // a plain left click only: with a modifier the browser opens the address as usual
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const link = e.target.closest('a.nd-go');
    if (!link) return;
    e.preventDefault();
    hide();
    nd.go(address(link.getAttribute('href')));
  });

  // ---- keys
  const typing = (e) => {
    const t = e.target;
    return t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
  };
  document.addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey || typing(e)) return;
    if (e.key === '?') { document.body.classList.toggle('nd-keys-on'); return; }
    if (e.key === 'Escape') { document.body.classList.remove('nd-keys-on'); return; }
    if (e.key === '[' || e.key === ']') {
      const where = document.querySelector('.nd-where');
      const to = where && (e.key === '[' ? where.dataset.prev : where.dataset.next);
      if (to) { e.preventDefault(); nd.go(address(to)); }
    }
  });
}
"""

def _register():
    return st.components.v2.component("nd_events", js=JS, isolate_styles=False)


_listen = _register()


def went():
    """Mount the listener; return the address of the internal link that was just followed, if any."""
    global _listen
    try:
        result = _listen(key="nd_events", on_went_change=lambda: None)
    except StreamlitAPIException:
        # the registry belongs to the running server; a new one (a restart, a test) starts empty
        _listen = _register()
        result = _listen(key="nd_events", on_went_change=lambda: None)
    return result.went
