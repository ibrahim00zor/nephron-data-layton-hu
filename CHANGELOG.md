# Changelog

Notable changes to this project. Newest first.

## Unreleased — 2026-10-04

Tested with Python 3.12, Streamlit 1.65, DuckDB 1.5, pandas 3.0, Plotly 7.1.
Requires `streamlit>=1.52`. The dataset (`veri/nephron_veritabani.parquet`) is unchanged.

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
- The anatomy diagram uses `st.iframe` (the previous component API is scheduled for removal).

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

No data, query or scientific statement is changed by the design work.

### Fixed

- Opening a page by its URL bypassed the router when the page folder was named `pages/`
  (Streamlit's legacy multipage discovery). The folder is now `views/`.
- Segment Profile: division by zero when a solute's inlet concentration is 0.
- Comparison: the reference selector offered scenarios that had been dropped for
  non-convergence.

## 1.0.0 — 2026-06

First archived release (Zenodo, doi:10.5281/zenodo.20489610).
