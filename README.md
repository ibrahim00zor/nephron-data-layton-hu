# Nephron Data (Layton/Hu)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20489610.svg)](https://doi.org/10.5281/zenodo.20489610)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![License: CC BY 4.0](https://img.shields.io/badge/Content-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Streamlit App](https://img.shields.io/badge/Live-Streamlit%20App-FF4B4B?logo=streamlit&logoColor=white)](https://nephron-data-layton-hu.streamlit.app)

A reader for the output of a published mathematical model of the human nephron (the
epithelial transport model of the Layton group; Hu, McDonough & Layton 2021). It lays the
model's output out so that it can be read, compared and checked: what happens to water and to
each solute, segment by segment, in six scenarios. It does not run the model and adds nothing
to it.

Formerly *Nefron Veri Gezgini* (Turkish). Links to the repository under its old name are
redirected by GitHub, and the DOI is unchanged.

**Live app:** https://nephron-data-layton-hu.streamlit.app

**Citation:** Zor, İ. (2026). *Nephron Data (Layton/Hu).* Zenodo. https://doi.org/10.5281/zenodo.20489610

---

## Status

An early-stage project. What is here:

- the model's output for six scenarios, read from one table, with pages that follow a solute
  along a segment, along the nephron, across nephron types and across scenarios, and that show
  what each transporter carries;
- checks of that output against physiology, an inventory of the dataset, and the exact model
  command behind every scenario;
- a look and a structure for the site (two "worlds", one selection that travels across pages,
  figures drawn by hand).

What is not here yet:

- **the clinical text.** The *Clinical world* shows the structure and the model data behind
  three teaching cases; their text will be written from verified sources and is not there;
- the summaries of the educational layer (segments, transporters, solutes);
- four of the ten scenarios that were attempted, and the end of the collecting duct in two of
  the six that are in (they did not converge in the model; see *Known limits*);
- a layout for phones. The site is made for a desktop browser and is checked in Safari's
  engine and in Chromium.

It is for teaching and for reading a model. It is not medical advice and not a tool for
clinical decisions.

---

## What it shows

Six scenarios: a healthy woman and a healthy man, moderate diabetes, hypertension, and SGLT2
inhibition in each sex.

**Pages.** The menu has two worlds and a back room.

| World | Page | Purpose |
|---|---|---|
| Model | Segment Profile | One solute along one segment, in the tubular fluid and the interstitium beside it; the change split into mass and water |
| Model | Whole Nephron | One solute from the proximal tubule to the papilla, the segments set end to end |
| Model | Nephron Types | The superficial nephron against the five juxtamedullary ones |
| Model | Comparison | Several scenarios on one chart, with a table of how they differ |
| Model | Transporters | Membrane fluxes per pathway and per transporter (NHE3, SGLT2, NKCC2, NCC, ENaC, Na/K-ATPase, …), with a mass-balance check |
| Model | Interactive Anatomy (beta) | The nephron drawn and coloured with the data: colour by concentration or load, thickness by water flow; a click on a segment selects it |
| Clinical | Clinical Cases | Three teaching cases built on the same scenarios: structure and model data only, for now |
| Data & quality | Validation | Checks of the model's output against physiology |
| Data & quality | Data Integrity | What is in the dataset, what converged, known limits |
| Data & quality | Model & Provenance | The exact model command behind each scenario, the model's prescribed inputs, how to reproduce the dataset |

**One selection.** The scenario, solute, segment, nephron type and compartment are chosen in
one row under the masthead and travel from page to page, so one question can be followed
across views. The address of a page carries the selection, so a copied address opens the same
view.

---

## Quick start

```bash
pip install -r requirements.txt
streamlit run kod/app.py
```

The app reads a single tidy Parquet file (`veri/nephron_veritabani.parquet`, 6 scenarios).

Run the tests (every page, the selection, the drawings, flux mass balance, provenance):

```bash
python tests/run_all.py
```

---

## Data & model provenance

All data is derived from the Layton/Hu human-nephron transport model. This project processes
that model's output; it does not re-implement the model.

- **Model (sex-specific human nephron):** Hu, R., McDonough, A.A., Layton, A.T. (2021). *Sex
  differences in solute and water handling in the human kidney: Modeling and functional
  implications.* iScience 24(6):102667. https://doi.org/10.1016/j.isci.2021.102667
- **Base human model:** Layton, A.T., Layton, H.E. (2019). *A computational model of epithelial
  solute and water transport along a human nephron.* PLoS Comput Biol 15(2):e1006108.
  https://doi.org/10.1371/journal.pcbi.1006108
- **Diabetic human model:** Hu, R., Layton, A. (2021). *A Computational Model of Kidney Function
  in a Patient with Diabetes.* Int J Mol Sci 22(11):5819. https://doi.org/10.3390/ijms22115819
- **Model code:** [`mstadt/nephron`](https://github.com/mstadt/nephron), commit `761ab729092e` (2022-07-05).
  The command line behind each scenario is in `kod/run_scenarios.py` and on the app's
  *Model & Provenance* page.

**Units:** concentration mM · solute flow pmol/min · volume nl/min · osmolality mOsm · potential mV ·
transporter flux density pmol/(min·cm²) (1 model unit = 600; verified by mass balance, see
`kod/transport.py`)

---

## Repository structure

```
.
├── README.md
├── LICENSE / LICENSE-CONTENT / CITATION.cff   # academic infrastructure
├── requirements.txt
├── veri/
│   └── nephron_veritabani.parquet   # 6 scenarios, one tidy table
├── kod/
│   ├── app.py             # entry point / router: frame and masthead, then the page
│   ├── nav.py             # page registry, masthead, shared selection, links that carry it
│   ├── ui_kit.py          # shared: frame, the selection row, the reader's words, queries, chart helper
│   ├── style.py           # the look: palette, chart template, stylesheet
│   ├── hand.py            # the hand that draws: the wander of a line and the tooth of the paper, as geometry
│   ├── nephron_figure.py  # the nephron drawing: Home figure, the small map of the selection row, logo
│   ├── anatomy_figure.py  # the drawing of the Interactive Anatomy page, coloured and sized by the data
│   ├── events.py          # clicks, pointer cards, keys and page turns, answered in place (v2 component)
│   ├── clinical_cases.py  # which scenario/focus each clinical case is built on
│   ├── transport.py       # transporter fluxes: verified units, membranes, mass balance
│   ├── education.py       # educational content (segment/transporter/solute)
│   ├── interpretation.py  # automatic mass/volume interpretation
│   ├── views/             # one file per page (home, segment_profile, ..., about)
│   ├── build_database.py  # raw txt -> tidy Parquet (multi-scenario)
│   ├── run_scenarios.py   # scenario generator (resumable)
│   └── veri_kontrol.py    # data-integrity checker (convergence)
├── tests/                 # Streamlit AppTest and unit tests; all of them: python tests/run_all.py
└── tools/
    ├── webkit_shot.swift  # a picture of a page as Safari's engine draws it
    └── webkit_drive.swift # point, click and time frames in Safari's engine
```

---

## Known limits

- **The interstitium is an input, not a result.** Interstitial fluid composition is specified
  at the cortex, the outer–inner medullary boundary and the papillary tip and interpolated
  linearly in between (Layton & Layton 2019, Table 2); it is identical in all six scenarios.
  The ~734 mOsm at the papillary tip is therefore a setting, not a prediction, and is below the
  ~1200 mOsm reported for maximal antidiuresis. The model has no vasculature and does not
  simulate how the medullary gradient is generated.
- **Scenario library 6/10:** four target scenarios (F_diab_severe, F_ACE, F_obese, F_UNX)
  failed to converge in the model's Newton solver (numerical overflow).
- **Non-converged distal segments** are hidden in the charts; distal/urine claims are only
  reliable for clean scenarios (see the Data Integrity page).

---

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).

## License

Dual-licensed (academic standard):

- **Code** (`kod/`) → [MIT License](LICENSE) — use, modify, distribute, including commercially, with attribution.
- **Content / data / figures** → [Creative Commons Attribution 4.0 (CC-BY 4.0)](LICENSE-CONTENT) — share, adapt, including commercially, with attribution.

## Citation

If you use this project in academic work, please use the format in [`CITATION.cff`](CITATION.cff). Short form:

> Zor, İ. (2026). *Nephron Data (Layton/Hu)* (Computer software).
> https://github.com/ibrahim00zor/nephron-data-layton-hu

The data is derived from the Hu et al. 2021 model. When citing this tool, also cite the original paper:

> Hu, R., McDonough, A.A., Layton, A.T. (2021). *Sex differences in solute and water handling
> in the human kidney: Modeling and functional implications.* iScience 24(6):102667.
> https://doi.org/10.1016/j.isci.2021.102667
