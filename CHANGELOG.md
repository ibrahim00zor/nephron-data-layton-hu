# Changelog

Notable changes to this project. Newest first.

## Unreleased — 2026-10-04

Tested with Python 3.12, Streamlit 1.65, DuckDB 1.5, pandas 3.0, Plotly 7.1.
Requires `streamlit>=1.52`. The dataset (`veri/nephron_veritabani.parquet`) is unchanged.

### Fluency (2026-10-05)

Measured in Safari's engine (WebKit) with `tools/webkit_drive.swift`, on the machine the site
is developed on; frame times are medians.

- **The name in the masthead leads home.** It did not: the address of the Home page was sent
  to the app as an empty string, which the app took for "nothing was followed".
- **Nothing is filtered by the browser any more.** The wander of the pencil line and the tooth
  of the paper were SVG filters laid over the drawings, and the grain of the page was two
  filtered drawings used as backgrounds. A browser works a filter out again for every frame in
  which something under it changes, and Safari also redrew the page's grain whenever it
  painted anything on it. Now the wander is in the geometry (`kod/hand.py`: a point is moved by
  a smooth field that depends only on where it is), the tooth is a small tile, and the grain of
  the page is two small pictures made once in the browser. The look is the same; a full
  repaint of the Home page went from 80 ms to 41 ms.
- **Fig. 1 answers at the rate of the display.** Pointing from segment to segment: 85 ms per
  frame before, 17 ms now. What is under the pointer is named on the figure by the script
  (`data-hot`) instead of through `:has(:hover)`; the card beside the pointer is moved, not
  laid out again. A clicked segment is marked at once, before the app has answered; the
  selection is marked by a rule beside the figure, so the figure itself is not sent again.
- **Interactive Anatomy is drawn by the page itself** (`kod/anatomy_figure.py`), by the same
  hand and answered by the same script as Fig. 1. It was a D3 drawing in a frame, with two
  fonts and a library fetched from elsewhere: about 30 ms per frame with the flow running (up
  to 90 ms under the pointer), a reload of the frame for every change, and — in Safari — a
  drawing cut off below the outer medulla. Now: 17 ms per frame, a change of solute or of what
  the colour shows is eased in place, the whole nephron is in view, and nothing is fetched
  from a third party. The profile along the nephron stands beside the drawing; a click on a
  segment selects it for every page. The page reads its data in two queries instead of
  about forty. The loop of the superficial nephron is closed (it was drawn as two limbs that
  did not meet).
- **Pages are turned, not swapped.** The page that is left steps back on the click; the page
  that is opened fades in as it arrives (it used to appear in three or four pieces). On a
  page, a block whose content changes settles in softly. `prefers-reduced-motion` is honoured.
- **A chart keeps its place.** A numbered figure is the same chart whatever it shows, so a
  new selection redraws its lines instead of removing the chart and putting another there.
- Tools: `tools/webkit_drive.swift` points at a page, clicks it and times its frames in
  WebKit; `tools/webkit_shot.swift` now photographs a page that is running.

### Published (2026-10-05)

- The README says plainly what this is, what is in it and what is not yet (the clinical text,
  the educational summaries, a layout for phones), and that it was *Nefron Veri Gezgini*.
- A source is named for what is written: the folds "About <segment>" no longer show a source
  line while the summary and its page are still to be written.

### One selection, in one place and in the reader's words (2026-10-05)

- **The selection is one row under the masthead**, the same on every page of the model world:
  *Scenario · Solute · Segment · Nephron · Compartment*, always in this order and under these
  names (`ui_kit.selection`). Before, the scenario was in a side panel and the other four were
  on the page, in an order that changed from page to page. A field a page does not use is
  still shown, with what is kept in it, but cannot be changed there. Under the row, one quiet
  line says what the scenario is, what did not converge in it, and links to its clinical case
  and back to the default selection. The side panel is gone; the small map of the nephron
  closes the row.
- **Figures speak in the reader's words.** Legends, tables and notes named scenarios, nephron
  types and compartments by their codes in the dataset (`F_diab_mod`, `jux3`, `Bath`); they
  now say "♀ + Diabetes (moderate)", "juxtamedullary 3", "interstitium". The codes stay where
  they belong: in the data, in the address of a page, in what is downloaded, and on the pages
  about the data. The Nephron field no longer offers "merged": the collecting duct is shared
  by all nephrons and is read from it without being asked.
- **Interactive Anatomy.** The long loop turns in a hairpin: the thin limbs met in a corner at
  its tip. The pencil is back in the drawing (a line two units thick with a coarser tooth);
  the ground is washed in over the pencil and under the colour, so the tooth shows the ground
  and the colour of a segment is not tinted by it.

### Corrected

- **Primary citation.** The model paper was cited with iScience article number 102694 and
  DOI `10.1016/j.isci.2021.102694`, which belongs to an unrelated materials-science paper.
  The correct reference is Hu R, McDonough AA, Layton AT (2021), iScience 24(6):**102667**,
  doi:[10.1016/j.isci.2021.102667](https://doi.org/10.1016/j.isci.2021.102667). Fixed in the
  app, README and `CITATION.cff`; the missing co-author is added. The archived v1.0.0 record on
  Zenodo still carries the old DOI.
- **The interstitium is a model input, not a result.** The app described the ~734 mOsm
  papillary osmolality as something the model computes, and the Validation page scored the
  corticomedullary gradient as a passed check. In this model the interstitial composition is
  specified at three points and interpolated linearly (Layton & Layton 2019, Methods and
  Table 2); in the dataset it is identical in all six scenarios. Texts are reworded, and
  Validation now separates **model outputs** (scored) from **prescribed inputs** (shown, not
  scored).
- **Validation and non-converged segments.** A check that depends on a segment that did not
  converge is reported as "not available" instead of failed. Previously `M_normal` showed
  `nan mOsm` and `F_diab_mod` showed `-1129 mOsm` for urine osmolality.
- **Transporter flux units.** The dataset labels transporter fluxes "pmol/min"; the model
  actually writes them in its internal units. They are flux densities: 1 model unit =
  600 pmol/(min·cm²) of luminal surface. Verified by mass balance (see below).
- **Loader (`kod/build_database.py`).** The membrane id in some file names was discarded, so
  the profiles of a transporter on several basolateral membranes ended up under one key. The
  loader now keeps the membrane. Rebuilding from the raw output gives identical values in all
  6,198,390 rows. The shipped dataset has not been replaced; the app handles both.
- Nephron Types: removed the statement that the medullary gradient "arises from" deep
  nephrons — the gradient is prescribed in this model.

### Added

- **Two-world navigation.** The menu is grouped into *Model world*, *Clinical world* and
  *Data & quality*. `kod/app.py` is a router (`st.navigation`); pages live in `kod/views/`.
- **Linked exploration.** The selection (scenario, solute, segment, nephron type,
  compartment) travels with the user from page to page. A clinical case opens the model
  pages with its scenarios and focus preselected and offers a link back; a scenario links to
  the clinical case built on it; home example questions open the matching page.
- **Transporters page.** Membrane fluxes per pathway and per transporter (NHE3, SGLT1/2,
  NKCC2, NCC, ENaC, Na/K-ATPase, …), within one scenario or across scenarios, with
  whole-segment totals where verified. Model output only — no interpretation added.
- **Mass-balance verification.** Apical + paracellular flux integrated over the luminal
  surface reproduces the drop in luminal flow: exact to six decimals in PT, S3, SDL, LDL, LAL,
  mTAL and cTAL, within 0.7% in DCT, across all 552 combinations of scenario × nephron type ×
  segment × (Na, K). Shown on the Transporters page and added to Validation.
- **Model & Provenance page.** The exact model command behind each scenario (read from
  `kod/run_scenarios.py`), convergence status, the model's prescribed inputs, the model's
  literature, and the commands to reproduce the dataset.
- **Tests** (`python tests/run_all.py`): every page through the router, the shared selection,
  multi-step contextual jumps, validation scoring, flux mass balance, provenance.
- References added: Layton & Layton 2019 (PLoS Comput Biol 15(2):e1006108) and Hu & Layton
  2021 (Int J Mol Sci 22(11):5819), the papers the model's authors list for the human and
  diabetic-human models.

### Changed

- The Clinical page follows the content-free version on `main`: structure and model data
  only, until a verified source article is loaded. No clinical content is reintroduced.
- Segment lists are in physiological order (PT → IMCD) instead of alphabetical.

### Structure

- **A masthead instead of a sidebar menu.** Every page starts with the same line: the name
  (a link to the Home page) and the worlds, *Model world*, *Clinical world*, *Data & quality*,
  and *About*; under it, the pages of the world the reader is in. It stays in view while the
  page scrolls, its links carry the selection and are answered in place.
- **The side panel holds the selection and nothing else:** the scenario, and the solute,
  segment, nephron and compartment that travel across pages. Dataset facts, units and the
  citation moved to the new **About** page (how to cite, with BibTeX; what the site is not;
  the dataset and its fingerprint; units; licence; where to report an error).
- **Numbered figures.** A chart is named under it, not inside it: `ui_kit.figure()` gives
  every chart "Fig. N", a caption in words, and its source, and puts the legend under the
  plot where it cannot be cut off. The per-chart citation line is gone.
- **Home.** The headline says what the site is (the name is in the masthead); the segment
  selected on Fig. 1 is read out in a band across the page (profile, values, ways on).
- **Fonts are the ones Streamlit ships** (Source Serif, Source Code Pro). Before, they were
  requested from Google Fonts through a font string whose fallbacks were not honoured: when
  the request failed, the whole site fell back to a sans-serif.
- Smaller things: "Points" on Segment Profile is now the range along the segment; table
  headers are words, not column names; Anatomy's buttons no longer lie over its legend;
  a fold has one ruled line, not two; the section mark above page titles is gone.

### Design

- **A look of its own.** The default dashboard theme is replaced by the look of a printed
  monograph: paper and ink, a serif for reading (Source Serif 4), a monospace for numbers
  (IBM Plex Mono), one accent colour, rules instead of boxes, charts drawn like journal
  figures. Palette, chart template and stylesheet live in `kod/style.py`; widget colours and
  fonts in `.streamlit/config.toml`.
- **Fig. 1 on the Home page.** A schematic of the superficial nephron and the collecting
  duct, drawn as SVG from one geometry (`kod/nephron_figure.py`). Each segment is tinted and
  labelled with the osmolality of the tubular fluid at its outlet, read from the dataset for
  the active scenario; a segment that did not converge is hatched and labelled "n.c.".
- **A locator in the sidebar.** The same drawing, small, marks the segment in the current
  selection on every page.
- **Mark and wordmark.** A logo (glomerulus and loop) in the sidebar and as the favicon.
- The Home panels name each line where it ends instead of using a legend; Validation is a
  ruled ledger; Data Integrity lists its notes as definitions; every page ends in a colophon.
- The Streamlit "Deploy" button and developer menu are hidden (`toolbarMode = "minimal"`).

- **Details that reward a closer look.**
  - *The figure answers.* Pointing at a part of Fig. 1 keeps it and lets the rest step back,
    and shows a card beside the pointer: the full name, the osmolality profile along the
    segment as a small line, and its inlet and outlet values. A click selects the segment in
    place (no reload): it stays marked, and a reading under the figure shows its profile
    against the interstitium, with ways on to Segment Profile and Transporters. The long loops
    of the juxtamedullary nephrons (one target, five bend values), the glomerulus and the
    macula densa can be pointed at too. The areas to point at are wide (30 px around a line).
  - *One hand, everywhere.* The rest of the page is in the hand of the figure. Labels are
    written the way the figure is annotated (small, italic, in the reading face) instead of
    in capitals. A field is a line to write on, not a box; what has been chosen is boxed and
    lightly shaded. A button is a frame drawn by hand and is shaded in under the pointer; a
    box to tick is drawn, and ticked in red pencil. Page titles are underlined quickly in red
    pencil. Tabs, folds, notes and the edge of the side panel are ruled in pencil. Tables are
    ruled by hand (`style.table`), words in serif and numbers in mono, instead of spreadsheet
    grids. The interactive anatomy drawing uses the same pencil, outlines and labels.
  - *Paper and pencil.* The page has the tooth of paper (a grain so slight it is felt more than
    seen). What is drawn, the nephron, is drawn as a pencil study: the outline is found in two
    passes, the line wanders a little, and tone is hatched over a pale wash, darker with the
    value; a segment without data keeps a broken outline and stays empty. What is measured,
    the line of a chart, is left exactly as it is. Charts sit on the sheet, without a box of
    their own. On the first view the tubule is drawn in the order the fluid meets the segments.
  - *Pencil marks in the text.* Titles are underlined quickly (red pencil under a page, graphite
    under a section and under the name in the side panel); links are underlined by hand; the
    letters that name the Home panels are ringed; checks are ticked by hand; list items start
    with a drawn dash; the logo is drawn in two passes.
  - *No browser-side filters.* Every pencil mark is a small SVG with its unevenness in the path
    itself, used as a CSS image. An earlier version applied `filter: url(#...)` to the lines
    of the charts; Safari then drew the charts without their lines. `tools/webkit_shot.swift`
    renders a page in WebKit off screen, so this can be checked without Safari.
  - *The sidebar map is a control.* A click on a segment selects it; the long loop is drawn to
    the depth of the selected juxtamedullary nephron.
  - *The address carries the selection.* The URL of a page always holds what the page shows
    (scenario, solute, segment, nephron, compartment, compared scenarios, case), so a copied
    address is a link to exactly that view. Values that do not exist are ignored.
  - *Links inside the app are answered in place.* A click on the figure, on the sidebar map
    or on a "see it" link no longer starts a new session: one small listener
    (`kod/events.py`, a Streamlit v2 component) passes the address to Python, which applies it
    as opening the link would. The links stay real addresses (new tab, copy, no JavaScript).
  - *Keys.* `[` and `]` step along the nephron, `?` shows the keys. The mark beside a page
    title is a pilcrow; a click copies the link to the view.
  - *Validation explains itself.* A row opens to say exactly what the check reads from the
    dataset, with a link to the page where it can be seen.
  - *Data Integrity* shows one small nephron per scenario with the stretch that did not converge
    struck out.
  - Abbreviations in the sidebar give their full names under the pointer; the colophon names the
    build (commit) and the dataset (SHA-256), in full under the pointer.

No data, query or scientific statement is changed by the design work.

### Fixed

- Opening a page by its URL bypassed the router when the page folder was named `pages/`
  (Streamlit's legacy multipage discovery). The folder is now `views/`.
- Segment Profile: division by zero when a solute's inlet concentration is 0.
- Comparison: the reference selector offered scenarios that had been dropped for
  non-convergence.

## 1.0.0 — 2026-06

First archived release (Zenodo, doi:10.5281/zenodo.20489610).
