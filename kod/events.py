"""
events.py — What the page does when it is pointed at, clicked or typed at.

One small script, mounted once per run by app.py, listens on the whole page:

- A click on an internal link (class "nd-go") is answered in place. The address of the
  link is sent to Python, which applies it (nav.follow) and renders the result, without
  starting a new session. The href stays a real address, so opening the link in a new
  tab, copying it, or a browser without JavaScript still works.
- The page answers the click at once, before Python has: a segment clicked on a figure is
  marked there and then (data-pick), and a link that leads to another page lets the page
  that is being left fade (data-leaving on <body>; the new page fades in by itself, see
  style.py).
- Pointing at a part of a figure (an element with data-seg inside a .nd-plate) names that
  part on every figure of the page and on the sidebar map (data-hot), and shows its card
  beside the pointer (the .nd-card[data-for] with the same key).
- Keys: "[" and "]" step along the nephron (the addresses are on the sidebar map), "?"
  shows the keys, Escape hides them.
- The pilcrow beside a page title copies the address of the view.
- The tooth of the paper is made here, once, as two small pictures (see `paper` below).

The script is trusted code written here; nothing a visitor types reaches it.
"""
import streamlit as st
from streamlit.errors import StreamlitAPIException

JS = """
export default function (component) {
  const nd = (window.__nd = window.__nd || {});
  nd.go = (address) => component.setTriggerValue('went', address);   // always the live session
  if (nd.arrived) nd.arrived(component.data || {});
  if (nd.ready) return;
  nd.ready = true;

  // ---- the address of an internal link, as Python reads it: "page?field=value"
  // (the Home page is "./": an empty address would say nothing, and be ignored)
  const address = (href) => {
    const url = new URL(href, window.location.href);
    return (url.pathname.split('/').pop() || './') + url.search;
  };
  const page = (where) => where.split('?')[0].replace(/^\\.\\//, '');
  const here = () => page(address(window.location.href));

  // ---- leaving a page: what is on it steps back while the next one is fetched
  let leaving = null;
  const stay = () => { clearTimeout(leaving); document.body.removeAttribute('data-leaving'); };
  const leave = () => {
    document.body.setAttribute('data-leaving', here() || 'home');
    clearTimeout(leaving);
    leaving = setTimeout(stay, 1500);      // whatever happens, nothing stays hidden
  };
  nd.arrived = (data) => {
    if (data.page === nd.page) return;
    nd.page = data.page;
    stay();
    const main = document.querySelector('[data-testid="stMain"]');
    if (main && main.scrollTop > 0) main.scrollTo(0, 0);     // a new page is read from its top
  };
  nd.arrived(component.data || {});

  // ---- what is under the pointer on a figure, and the card beside it
  let hot = null, card = null, size = null, frame = 0, at = null;
  const mark = (name, key) => {
    document.querySelectorAll('.nd-plate > svg, .nd-where').forEach((el) => {
      if (key) el.setAttribute(name, key); else el.removeAttribute(name);
    });
  };
  const place = () => {
    frame = 0;
    if (!card || !at) return;
    if (!size) size = card.getBoundingClientRect();
    let left = at.x + 18, top = at.y + 16;
    if (left + size.width > window.innerWidth - 8) left = at.x - size.width - 18;
    if (top + size.height > window.innerHeight - 8) top = at.y - size.height - 16;
    card.style.transform = 'translate3d(' + Math.max(8, left) + 'px,' + Math.max(8, top) + 'px,0)';
  };
  const point = (target, e) => {
    if (target === hot) return;
    hot = target;
    const key = hot ? hot.getAttribute('data-seg') : null;
    mark('data-hot', key);
    const next = hot ? document.querySelector('.nd-card[data-for="' + key + '"]') : null;
    if (next === card) return;
    if (card) card.classList.remove('on');
    card = next; size = null;
    if (card) {
      at = { x: e.clientX, y: e.clientY };
      place();                               // where it belongs first, then shown
      card.classList.add('on');
    }
  };
  const over = (e) => point(e.target && e.target.closest ? e.target.closest('.nd-plate [data-seg]') : null, e);
  document.addEventListener('mouseover', over, { passive: true });
  document.addEventListener('mousemove', (e) => {
    if (!hot) over(e);                       // after a scroll, the pointer may not have left
    if (!card) return;
    at = { x: e.clientX, y: e.clientY };
    if (!frame) frame = requestAnimationFrame(place);
  }, { passive: true });
  document.documentElement.addEventListener('mouseleave', () => point(null));
  document.addEventListener('scroll', () => point(null), { passive: true, capture: true });

  // ---- a segment clicked on a figure is marked at once; Python's answer takes its place
  const pick = (link) => {
    const svg = link.closest('.nd-plate svg');
    const key = link.getAttribute('data-seg');
    if (!svg || !key || key === 'loops') return;
    svg.setAttribute('data-pick', key);
    // the page says which segment is selected in a small rule of its own (nephron_figure.pin);
    // when that rule changes, Python has answered
    let timer = 0;
    const settled = new MutationObserver(() => done());
    const done = () => { settled.disconnect(); clearTimeout(timer); svg.removeAttribute('data-pick'); };
    const pin = document.querySelector('style.nd-pin');
    if (pin) settled.observe(pin, { subtree: true, childList: true, characterData: true });
    timer = setTimeout(done, 4000);
  };

  const flash = (message) => {
    let el = document.getElementById('nd-flash');
    if (!el) { el = document.createElement('div'); el.id = 'nd-flash'; document.body.appendChild(el); }
    el.textContent = message;
    el.classList.add('on');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('on'), 1800);
  };

  const follow = (to, link) => {
    if (page(to) !== here()) leave(); else if (link) pick(link);
    nd.go(to);
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
    point(null);
    follow(address(link.getAttribute('href')), link);
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
      if (to) { e.preventDefault(); follow(address(to)); }
    }
  });

  // ---- the tooth of the paper
  // The page has a grain (fine) and an unevenness of tone (slow). Both were drawings that
  // the browser worked out from noise each time it painted the page behind anything, and in
  // Safari that was most of the cost of every frame. Here they are worked out once, into
  // two small pictures that the stylesheet tiles (style.PAPER_TEXTURE); until they are
  // ready, and without this script, the page has the same tone without the grain.
  const paper = () => {
    let state = 8;
    const random = () => (state = (Math.imul(state, 1664525) + 1013904223) >>> 0) / 4294967296;
    // noise that repeats at the edges of its tile: octaves of a grid of random values
    const noise = (size, cells, octaves) => {
      const out = new Float32Array(size * size);
      let weight = 1, total = 0;
      for (let o = 0; o < octaves; o++, cells *= 2, weight /= 2) {
        total += weight;
        const grid = new Float32Array(cells * cells);
        for (let i = 0; i < grid.length; i++) grid[i] = random();
        const step = cells / size;
        for (let y = 0; y < size; y++) {
          const gy = y * step, y0 = Math.floor(gy) % cells, y1 = (y0 + 1) % cells;
          let fy = gy - Math.floor(gy); fy = fy * fy * (3 - 2 * fy);
          for (let x = 0; x < size; x++) {
            const gx = x * step, x0 = Math.floor(gx) % cells, x1 = (x0 + 1) % cells;
            let fx = gx - Math.floor(gx); fx = fx * fx * (3 - 2 * fx);
            const top = grid[y0 * cells + x0] + (grid[y0 * cells + x1] - grid[y0 * cells + x0]) * fx;
            const low = grid[y1 * cells + x0] + (grid[y1 * cells + x1] - grid[y1 * cells + x0]) * fx;
            out[y * size + x] += (top + (low - top) * fy) * weight;
          }
        }
      }
      for (let i = 0; i < out.length; i++) out[i] /= total;
      return out;
    };
    // a tile of one colour whose opacity follows the noise: mean + spread * (noise - 0.5)
    const tile = (name, size, cells, octaves, rgb, mean, spread) => {
      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = size;
      const context = canvas.getContext('2d');
      const image = context.createImageData(size, size);
      const field = noise(size, cells, octaves);
      for (let i = 0; i < field.length; i++) {
        image.data[4 * i] = rgb[0]; image.data[4 * i + 1] = rgb[1]; image.data[4 * i + 2] = rgb[2];
        image.data[4 * i + 3] = Math.max(0, Math.min(255, 255 * (mean + spread * (field[i] - 0.5))));
      }
      context.putImageData(image, 0, 0);
      canvas.toBlob((blob) => {
        if (blob) document.documentElement.style.setProperty(name, 'url(' + URL.createObjectURL(blob) + ')');
      });
    };
    const sharp = Math.min(Math.max(Math.round(window.devicePixelRatio || 1), 1), 2);
    tile('--nd-grain', 260 * sharp, 200, sharp + 1, [149, 137, 115], 0.047, 0.10);
    tile('--nd-mottle', 180, 5, 2, [179, 162, 129], 0.02, 0.19);
  };
  try { paper(); } catch (error) { /* the page stays plain paper */ }
}
"""


def _register():
    return st.components.v2.component("nd_events", js=JS, isolate_styles=False)


_listen = _register()


def went(page=None):
    """Mount the listener; return the address of the internal link that was just followed,
    if any. `page` is the page being shown: the script uses it to tell an arrival."""
    global _listen
    try:
        result = _listen(key="nd_events", data={"page": page}, on_went_change=lambda: None)
    except StreamlitAPIException:
        # the registry belongs to the running server; a new one (a restart, a test) starts empty
        _listen = _register()
        result = _listen(key="nd_events", data={"page": page}, on_went_change=lambda: None)
    return result.went
