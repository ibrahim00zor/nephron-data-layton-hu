# Nephron Data (Layton/Hu)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20489610.svg)](https://doi.org/10.5281/zenodo.20489610)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![License: CC BY 4.0](https://img.shields.io/badge/Content-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Streamlit App](https://img.shields.io/badge/Live-Streamlit%20App-FF4B4B?logo=streamlit&logoColor=white)](https://nefron-veri-gezgini.streamlit.app)

An interactive, citable science tool that turns the output of the Layton/Hu human-nephron
epithelial transport model into an explorable data application for clinicians, students, and
researchers.

**Live app:** https://nefron-veri-gezgini.streamlit.app

**Citation:** Zor, İ. (2026). *Nephron Data (Layton/Hu).* Zenodo. https://doi.org/10.5281/zenodo.20489610

---

## What it does

The app visualizes the model output for **6 scenarios** — healthy female and male, moderate
diabetes, hypertension, and SGLT2 inhibitor (female and male). It traces the concentration
profile along each nephron segment, separates mass and volume changes, checks physiology
automatically, and provides an educational clinical layer.

**Pages** — the menu is organised in two worlds, plus data & quality

| World | Page | Purpose |
|---|---|---|
| Model | Segment Profile | One solute in one segment; Lumen+Bath overlay; automatic mass/volume interpretation |
| Model | Whole Nephron | Chained profile from PT → IMCD |
| Model | Nephron Types | Superficial vs juxtamedullary (jux1–5): the effect of depth |
| Model | Comparison | Several scenarios overlaid, with a difference table |
| Model | Interactive Anatomy (BETA) | D3.js anatomic diagram: color by concentration/load, thickness by flow |
| Clinical | Clinical Cases | Educational case interface built on the same scenarios — *not medical advice* |
| Data & quality | Validation | Automatic physiology checks |
| Data & quality | Data Integrity | Database inventory, convergence status, known limits |

**Linked exploration.** The selection (scenario, solute, segment, nephron type, compartment)
travels with you from page to page, so one question can be followed across views. A clinical
case opens the model pages with its scenarios and focus preselected and offers a way back;
a scenario links to the clinical case built on it.

---|---|
| Segment Profile | One solute in one segment; Lumen+Bath overlay; automatic mass/volume interpretation |
| Whole Nephron | Chained flow chart from PT → IMCD |
| Nephron Types | Superficial vs juxtamedullary (jux1–5): the effect of depth |
| Comparison | Several scenarios overlaid, with a difference table |
| Validation | Automatic physiology checks against textbook expectations |
| Data Integrity | Database inventory, convergence status, known limits |
| Interactive Anatomy (BETA) | D3.js anatomic diagram: color by concentration/load, thickness by flow |
| Clinical | Educational case interface (mechanism, drug/dose, model data) — *not medical advice* |

---

## Quick start

```bash
pip install -r requirements.txt
streamlit run kod/app.py
```

The app reads a single tidy Parquet file (`veri/nephron_veritabani.parquet`, 6 scenarios).

Run the tests (page rendering, shared selection, contextual navigation):

```bash
python tests/test_app.py
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
- **Model code:** [`mstadt/nephron`](https://github.com/mstadt/nephron)

**Units:** concentration mM · flux pmol/min · volume nl/min · osmolality mOsm · potential mV

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
│   ├── app.py             # entry point / router: menu, frame, sidebar, then the page
│   ├── nav.py             # page registry, shared selection context, contextual jumps
│   ├── ui_kit.py          # shared: frame, sidebar, queries, chart helper, citation footer
│   ├── clinical_cases.py  # which scenario/focus each clinical case is built on
│   ├── education.py       # educational content (segment/transporter/solute)
│   ├── interpretation.py  # automatic mass/volume interpretation
│   ├── views/             # one file per page (home, segment_profile, whole_nephron, ...)
│   ├── d3_components/     # nephron_diagram.html (D3.js anatomic template)
│   ├── build_database.py  # raw txt -> tidy Parquet (multi-scenario)
│   ├── run_scenarios.py   # scenario generator (resumable)
│   └── veri_kontrol.py    # data-integrity checker (convergence)
└── tests/
    └── test_app.py        # smoke + navigation tests (Streamlit AppTest)
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

## License

Dual-licensed (academic standard):

- **Code** (`kod/`) → [MIT License](LICENSE) — use, modify, distribute, including commercially, with attribution.
- **Content / data / figures** → [Creative Commons Attribution 4.0 (CC-BY 4.0)](LICENSE-CONTENT) — share, adapt, including commercially, with attribution.

## Citation

If you use this project in academic work, please use the format in [`CITATION.cff`](CITATION.cff). Short form:

> Zor, İ. (2026). *Nephron Data (Layton/Hu)* (Computer software).
> https://github.com/ibrahim00zor/nefron-veri-gezgini

The data is derived from the Hu et al. 2021 model. When citing this tool, also cite the original paper:

> Hu, R., McDonough, A.A., Layton, A.T. (2021). *Sex differences in solute and water handling
> in the human kidney: Modeling and functional implications.* iScience 24(6):102667.
> https://doi.org/10.1016/j.isci.2021.102667
