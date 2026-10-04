"""
ui_kit.py — Shared UI components.

app.py (the router) and every file under views/ import this module. The page frame
(theme, CSS), the sidebar, query helpers, chart helper, and citation footer all come
from here. Page files hold only their own logic — boilerplate lives here.
Navigation and the shared selection context live in nav.py.
"""
import html
import os
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px

import nav
import nephron_figure
import style
from clinical_cases import CASES, CASE_BY_SCENARIO
from style import SCENARIO_COLOR  # noqa: F401  (re-exported: pages import it from here)

APP_NAME = "Nephron Data (Layton/Hu)"

# ============================================================
#  Paths (relative to the project root)
# ============================================================
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(PROJ, "veri", "nephron_veritabani.parquet")
DB = f"read_parquet('{PARQUET}')"

# ============================================================
#  Constants
# ============================================================
SEG_ORDER_SUP = ["PT", "S3", "SDL", "mTAL", "cTAL", "DCT", "CNT", "CCD", "OMCD", "IMCD"]
SEG_ORDER_JUX = ["PT", "S3", "SDL", "LDL", "LAL", "mTAL", "cTAL", "DCT", "CNT", "CCD", "OMCD", "IMCD"]
NEPHRONS = ["sup", "jux1", "jux2", "jux3", "jux4", "jux5", "merged"]
CD_SEGMENTS = {"CCD", "OMCD", "IMCD"}

SCENARIO_LABEL = {
    "F_normal":   "♀ Healthy female (baseline)",
    "M_normal":   "♂ Healthy male (baseline)",
    "F_diab_mod": "♀ + Diabetes (moderate)",
    "F_HT":       "♀ + Hypertension",
    "F_SGLT2":    "♀ + SGLT2 inhibitor",
    "M_SGLT2":    "♂ + SGLT2 inhibitor",
}
SCENARIO_DETAIL = {
    "F_normal":   "Healthy adult female, normal hydration. The reference for every comparison.",
    "M_normal":   "Healthy adult male. Reference for sex-difference analyses.",
    "F_diab_mod": "Moderate diabetes. Glucose load rises in the PT.",
    "F_HT":       "Hypertension. Tubular pressure and renal blood flow deviate from baseline.",
    "F_SGLT2":    "Gliflozin. PT glucose reabsorption blocked; natriuresis expected.",
    "M_SGLT2":    "Gliflozin, male. Sex × drug comparison against F_SGLT2.",
}

# ============================================================
#  Page frame (called once per run by app.py, before the page body)
# ============================================================
def apply_frame():
    """Chart template and stylesheets shared by every page (see style.py, nephron_figure.py)."""
    style.apply()
    st.markdown(nephron_figure.STYLES, unsafe_allow_html=True)

# ============================================================
#  Query helpers (cached)
# ============================================================
@st.cache_data
def q(sql, params=None):
    return duckdb.connect().execute(sql, params or []).df()

def scalar(sql, scenario, params=None):
    """Adds the condition filter automatically and returns a single value."""
    if "condition=" not in sql:
        sql = sql.replace("WHERE ", f"WHERE condition='{scenario}' AND ", 1)
    r = q(sql, params or [])
    return None if r.empty else float(r["value"].iloc[0])

# ============================================================
#  Helpers
# ============================================================
def neph_for(segment, requested):
    return "merged" if segment in CD_SEGMENTS else requested

@st.cache_data
def options():
    """(segments, solutes) present in the data. Segments come in physiological (flow) order."""
    seg = q(f"SELECT DISTINCT segment FROM {DB}")["segment"].tolist()
    sol = q(f"SELECT DISTINCT solute FROM {DB} WHERE solute IS NOT NULL")["solute"].tolist()
    ordered = [s for s in SEG_ORDER_JUX if s in seg] + sorted(s for s in seg if s not in SEG_ORDER_JUX)
    return ordered, sorted(sol)

@st.cache_data
def health_metrics():
    return q(f"""
        SELECT COUNT(*) AS rows, COUNT(DISTINCT segment) AS segments,
               (SELECT COUNT(DISTINCT solute) FROM {DB} WHERE solute IS NOT NULL) AS solutes,
               COUNT(DISTINCT variable) AS variables,
               COUNT(DISTINCT nephron) AS nephrons,
               COUNT(DISTINCT condition) AS scenario_count
        FROM {DB}
    """).iloc[0]

@st.cache_data
def scenario_list():
    return q(f"SELECT DISTINCT condition FROM {DB} ORDER BY condition")["condition"].tolist()

# Variables that cannot be physically negative (used to detect convergence failures)
NONNEG_VARS = {"con", "osmolality", "water_volume"}

@st.cache_data
def integrity_map():
    """Which (scenario -> set of segments) failed to converge numerically?
    Signal: a NaN value or a negative Lumen osmolality (a solute total cannot be negative).
    The model's Newton solver breaks down in the collecting duct for some scenarios."""
    df = q(f"""
        SELECT condition, segment,
            SUM(CASE WHEN value IS NULL OR isnan(value) THEN 1 ELSE 0 END) AS nan,
            SUM(CASE WHEN variable='osmolality' AND compartment='Lumen' AND value < -1
                     THEN 1 ELSE 0 END) AS neg_osm
        FROM {DB} GROUP BY condition, segment
    """)
    broken = {}
    for _, r in df.iterrows():
        if r["nan"] > 0 or r["neg_osm"] > 0:
            broken.setdefault(r["condition"], set()).add(r["segment"])
    return broken

def valid_data(df, variable, value_col="value"):
    """Filters out physically impossible rows (NaN; negatives in non-negative variables).
    Prevents garbage curves from being drawn for non-converged scenarios (universal safety net).
    Returns: (clean_df, number_of_dropped_rows)."""
    n0 = len(df)
    mask = df[value_col].notna()
    if variable in NONNEG_VARS:
        mask = mask & (df[value_col] >= -1e-9)
    clean = df[mask]
    return clean, n0 - len(clean)

def segment_broken(scenario, segment):
    """Did this (scenario, segment) fail to converge? If True the whole segment is hidden
    (so no truncated/misleading curve is left). We distrust it even if it breaks only late."""
    return segment in integrity_map().get(scenario, set())

# ============================================================
#  Names behind the abbreviations
# ============================================================
NEPHRON_NAME = {
    "sup": "superficial nephron",
    "jux1": "juxtamedullary nephron 1 of 5 (shortest long loop)",
    "jux2": "juxtamedullary nephron 2 of 5",
    "jux3": "juxtamedullary nephron 3 of 5",
    "jux4": "juxtamedullary nephron 4 of 5",
    "jux5": "juxtamedullary nephron 5 of 5 (longest loop)",
    "merged": "the collecting duct, shared by all nephrons",
}
COMPARTMENT_NAME = {
    "Lumen": "the tubular fluid",
    "Cell": "inside the epithelial cell",
    "Bath": "the interstitium around the tubule",
    "LIS": "the lateral intercellular space",
}


def segment_names():
    """Segment code -> full name (from the educational layer)."""
    from education import SEGMENT
    return {code: info["full_name"] for code, info in SEGMENT.items() if info.get("full_name")}


def abbr(text, meaning=None):
    """A term that explains itself under the pointer."""
    text = html.escape(str(text))
    return f"<abbr title='{html.escape(meaning, quote=True)}'>{text}</abbr>" if meaning else text


def selection_with_names():
    from education import SOLUTE
    solute, segment, nephron, compartment = (nav.get(name) for name in nav.SELECTION)
    return " · ".join((
        abbr(solute, SOLUTE.get(solute, {}).get("full_name")),
        abbr(segment, segment_names().get(segment)),
        abbr(nephron, NEPHRON_NAME.get(nephron)),
        abbr(compartment, COMPARTMENT_NAME.get(compartment)),
    ))


def loop_depths():
    """How deep the long loop of each juxtamedullary nephron reaches, relative to the deepest
    (from the length the model gives its long descending limb in the baseline scenario)."""
    df = q(f"SELECT nephron, max(value) AS length FROM {DB} "
           f"WHERE variable='length' AND segment='LDL' AND condition=? GROUP BY nephron",
           [nav.DEFAULTS["scenario"]])
    longest = df["length"].max() if not df.empty else None
    if not longest:
        return {}
    return {row.nephron: row.length / longest for row in df.itertuples()}


@st.cache_data
def build_id():
    """Commit the running code was set from, read from .git without calling git ("" if unknown)."""
    git = os.path.join(PROJ, ".git")
    try:
        with open(os.path.join(git, "HEAD")) as f:
            head = f.read().strip()
        if not head.startswith("ref:"):
            return head
        ref = head.split(" ", 1)[1]
        path = os.path.join(git, ref)
        if os.path.exists(path):
            with open(path) as f:
                return f.read().strip()
        with open(os.path.join(git, "packed-refs")) as f:
            for line in f:
                if line.strip().endswith(ref):
                    return line.split(" ", 1)[0]
    except OSError:
        pass
    return ""


@st.cache_data
def dataset_fingerprint():
    """SHA-256 of the dataset file: two copies with the same fingerprint hold the same numbers."""
    import hashlib
    digest = hashlib.sha256()
    try:
        with open(PARQUET, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                digest.update(block)
    except OSError:
        return ""
    return digest.hexdigest()


# ============================================================
#  Sidebar (rendered once per run by app.py, below the page menu)
# ============================================================
def render_sidebar():
    scenarios = scenario_list()
    with st.sidebar:
        scenario = nav.select(
            st, "Active scenario", scenarios, "scenario", fallback="F_normal",
            format_func=lambda s: SCENARIO_LABEL.get(s, s),
            help="Charts and queries are filtered by this scenario. It stays selected as you change pages.",
        )
        detail = SCENARIO_DETAIL.get(scenario, "")
        if detail:
            st.markdown(f"<div class='nd-side-about'>{detail}</div>", unsafe_allow_html=True)

        # Model world -> clinical world: the case (if any) that is built on this scenario
        case_key = CASE_BY_SCENARIO.get(scenario)
        if case_key and st.button(f"Clinical case: {CASES[case_key]['button']} →",
                                  key="_sidebar_case", width="stretch",
                                  help="Open the clinical case that uses this scenario."):
            nav.go("clinical", case=case_key)

        broken = integrity_map()
        if scenario in broken:
            segs = ", ".join(sorted(broken[scenario]))
            st.warning(
                f"**{segs}** did not converge in this scenario (collecting duct). Its data is "
                f"invalid and is hidden in the charts; proximal tubule to DCT is reliable. "
                f"See Data Integrity."
            )

        # The selection that travels with the user across pages
        st.markdown("---")
        segment, nephron = nav.get("segment"), nav.get("nephron")
        long_loop = str(nephron).startswith("jux")
        order = SEG_ORDER_JUX if long_loop else SEG_ORDER_SUP
        # a click on the map selects that segment (the two thin limbs exist only in a long loop)
        links = {code: nav.href(segment=code, **({} if long_loop or code not in ("LDL", "LAL")
                                                  else {"nephron": "jux5"}))
                 for code in SEG_ORDER_JUX}
        before, after = nav.neighbours(order)
        steps = "".join(f" data-{key}='{html.escape(link, quote=True)}'"
                        for key, link in (("prev", before), ("next", after)) if link)
        st.markdown(
            f"<div class='nd-where'{steps}>"
            + nephron_figure.locator(segment, links=links, names=segment_names(), long_loop=long_loop,
                                     depth=loop_depths().get(nephron, 1.0))
            + f"<div><div class='nd-label'>Selection, kept across pages</div>"
            f"<div class='nd-side-meta' style='font-size:0.8rem;color:{style.INK_SOFT};'>"
            f"{selection_with_names()}</div>"
            f"<div class='nd-side-meta'>marked: where {html.escape(str(segment))} lies</div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
        if not nav.is_default_selection():
            if st.button("Reset selection", key="_sidebar_reset", width="stretch"):
                nav.reset_selection()
                st.rerun()

        st.markdown("---")
        sb = health_metrics()
        st.markdown(
            f"<div class='nd-label'>The dataset</div>"
            f"<div class='nd-side-meta'>{sb['scenario_count']} scenarios · "
            f"{sb['rows'] // max(sb['scenario_count'], 1):,} rows each<br>"
            f"{sb['segments']} segments · {sb['solutes']} solutes · {sb['nephrons']} nephron types<br>"
            f"scenario code <span style='color:{style.INK_SOFT};'>{scenario}</span></div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        with st.expander("Source and citation"):
            st.markdown(
                "**Model.** Hu R., McDonough A.A., Layton A.T. (2021). *Sex differences in solute "
                "and water handling in the human kidney: Modeling and functional implications.* "
                "iScience 24(6):102667. "
                "[doi:10.1016/j.isci.2021.102667](https://doi.org/10.1016/j.isci.2021.102667)  \n"
                "Code: `mstadt/nephron`\n\n"
                "**This tool.** Zor, İ. (2026). *Nephron Data (Layton/Hu).* Zenodo. "
                "[doi:10.5281/zenodo.20489610](https://doi.org/10.5281/zenodo.20489610)"
            )
            if "provenance" in nav.PAGES:
                nav.link(st, "provenance", "Scenarios, inputs, how to reproduce")
        with st.expander("Units"):
            st.markdown(
                "Concentration mM · solute flow pmol/min · volume nl/min · osmolality mOsm · "
                "potential mV · transporter flux pmol/(min·cm²)"
            )
    return scenario

# ============================================================
#  Chart helper
# ============================================================
def make_chart(df, x, y, color, title, xlab, ylab, color_label="Series",
               category_orders=None, height=460, color_map=None, legend_below=False):
    if color_map:
        fig = px.line(df, x=x, y=y, color=color, title=title,
                      labels={x: xlab, y: ylab, color: color_label},
                      category_orders=category_orders or {},
                      color_discrete_map=color_map)
    else:
        fig = px.line(df, x=x, y=y, color=color, title=title,
                      labels={x: xlab, y: ylab, color: color_label},
                      category_orders=category_orders or {})
    fig.update_layout(hovermode="x unified", height=height,
                      legend=dict(title_text=color_label.upper()))
    if legend_below:   # long series names: give the plot the full width
        fig.update_layout(legend=dict(orientation="h", title_text="", x=0, xanchor="left",
                                      y=-0.2, yanchor="top"))
    fig.update_traces(line=dict(width=2))
    return fig

# ============================================================
#  Colophon (the last thing on every page)
# ============================================================
def colophon():
    st.markdown(
        "<div class='nd-colophon'>"
        "<b>Nephron Data (Layton/Hu)</b> · İbrahim Zor, 2026 · "
        "<a href='https://doi.org/10.5281/zenodo.20489610' target='_blank'>doi:10.5281/zenodo.20489610</a> · "
        "<a href='https://github.com/ibrahim00zor/nefron-veri-gezgini' target='_blank'>source</a><br>"
        "Model: Hu R., McDonough A.A., Layton A.T. (2021). <i>Sex differences in solute and water "
        "handling in the human kidney.</i> iScience 24(6):102667.<br>"
        "Code under the MIT licence, content under CC BY 4.0. "
        "Set in Source Serif and IBM Plex Mono; built with Streamlit, DuckDB and Plotly."
        f"{_imprint()}</div>{KEYS_CARD}",
        unsafe_allow_html=True,
    )


def _imprint():
    """Which code and which data this page was made from, for anyone who needs to say exactly."""
    parts = []
    commit, data = build_id(), dataset_fingerprint()
    if commit:
        parts.append(f"build <span class='nd-print' title='commit {commit}'>{commit[:7]}</span>")
    if data:
        parts.append(f"dataset <span class='nd-print' title='sha256 {data}'>{data[:12]}</span>")
    parts.append("<span class='nd-print' title='show the keyboard keys'>press ? for keys</span>")
    return "<br>" + " · ".join(parts)


# The keys (shown by "?"; the listening is in events.py).
KEYS_CARD = (
    "<div class='nd-keys' role='note'><div class='nd-label'>Keys</div><dl>"
    "<dt>]</dt><dd>next segment along the nephron</dd>"
    "<dt>[</dt><dd>previous segment</dd>"
    "<dt>¶</dt><dd>beside a page title: copy a link to this exact view</dd>"
    "<dt>?</dt><dd>show or hide this card</dd>"
    "</dl><div class='nd-side-meta'>The address of the page always carries your selection.</div></div>"
)

# ============================================================
#  Citation footer (under every chart)
# ============================================================
def cite_footer():
    st.markdown(
        "<div class='nd-cite'>"
        "Data: Hu, McDonough &amp; Layton 2021, <i>iScience</i> 24:102667. "
        "This tool: Zor 2026, "
        "<a href='https://doi.org/10.5281/zenodo.20489610' target='_blank'>doi:10.5281/zenodo.20489610</a>. "
        "Concentration in mM, volume in nl/min, osmolality in mOsm."
        "</div>",
        unsafe_allow_html=True,
    )

# ============================================================
#  Reference / citation system (bibliography entries)
# ============================================================
# RULE: only real references with a verified citation/DOI go here
# (consistent with CITATION.cff). No fabricated citation/DOI/title, ever.
# Primary clinical literature (RCTs, KDIGO, etc.) is added only after double-verification.
# NOTE: Türkmen 2024 (textbook) is intentionally NOT here — that reference is made by the
# author in their own notes, in their own words (only they have access to the book).
REFERENCES = {
    "hu2021": {
        "type": "Article",
        "authors": "Hu R., McDonough A.A., Layton A.T.",
        "year": 2021,
        "title": "Sex differences in solute and water handling in the human kidney: "
                 "Modeling and functional implications",
        "source": "iScience 24(6):102667",
        "doi": "10.1016/j.isci.2021.102667",
        "note": "The sex-specific human nephron model from which the data in this app is derived "
                "(primary source).",
    },
    "layton2019": {
        "type": "Article",
        "authors": "Layton A.T., Layton H.E.",
        "year": 2019,
        "title": "A computational model of epithelial solute and water transport along a human nephron",
        "source": "PLoS Computational Biology 15(2):e1006108",
        "doi": "10.1371/journal.pcbi.1006108",
        "note": "The first computational model of the human nephron, on which the sex-specific "
                "model is built. Listed by the model's authors as the paper for the human model.",
    },
    "hu_layton2021": {
        "type": "Article",
        "authors": "Hu R., Layton A.",
        "year": 2021,
        "title": "A Computational Model of Kidney Function in a Patient with Diabetes",
        "source": "International Journal of Molecular Sciences 22(11):5819",
        "doi": "10.3390/ijms22115819",
        "note": "Human diabetic-kidney model and SGLT2 inhibition. Listed by the model's authors "
                "as the paper for the diabetic human model.",
    },
    "model_stadt": {
        "type": "Software",
        "authors": "Stadt M., Layton A.T.",
        "year": None,
        "title": "nephron — mathematical model implementation",
        "source": "github.com/mstadt/nephron",
        "url": "https://github.com/mstadt/nephron",
        "note": "The open-source model code the scenarios were generated with.",
    },
    # --- Clinical literature (PubMed; verified by the author in 2026-06) ---
    "vallon2022": {
        "type": "Article",
        "authors": "Vallon V.",
        "year": 2022,
        "title": "Renoprotective Effects of SGLT2 Inhibitors",
        "source": "Heart Failure Clinics 18(4):539-549",
        "doi": "10.1016/j.hfc.2022.03.005",
        "note": "Mechanistic review of TGF restoration and the renoprotective mechanism of SGLT2i.",
    },
    "upadhyay2024": {
        "type": "Article",
        "authors": "Upadhyay A.",
        "year": 2024,
        "title": "SGLT2 Inhibitors and Kidney Protection: Mechanisms Beyond Tubuloglomerular Feedback",
        "source": "Kidney360 5(5):771-782",
        "doi": "10.34067/KID.0000000000000425",
        "note": "Renoprotective mechanisms of TGF and beyond (recent review).",
    },
    "empakidney2023": {
        "type": "RCT",
        "authors": "EMPA-KIDNEY Collaborative Group (Herrington WG, Staplin N, et al.)",
        "year": 2023,
        "title": "Empagliflozin in Patients with Chronic Kidney Disease",
        "source": "N Engl J Med 388(2):117-127 (online 2022)",
        "doi": "10.1056/NEJMoa2204233",
        "note": "Landmark randomized trial: clinical effect of empagliflozin on renal outcomes.",
    },
    "vallon_thomson2020": {
        "type": "Article",
        "authors": "Vallon V., Thomson S.C.",
        "year": 2020,
        "title": "The tubular hypothesis of nephron filtration and diabetic kidney disease",
        "source": "Nature Reviews Nephrology 16(6):317-336",
        "doi": "10.1038/s41581-020-0256-y",
        "note": "Reference review of the tubular hypothesis of diabetic hyperfiltration.",
    },
    "ivy_bailey2014": {
        "type": "Article",
        "authors": "Ivy J.R., Bailey M.A.",
        "year": 2014,
        "title": "Pressure natriuresis and the renal control of arterial blood pressure",
        "source": "The Journal of Physiology 592(18):3955-3967",
        "doi": "10.1113/jphysiol.2014.271676",
        "note": "Authoritative review of pressure natriuresis and renal blood-pressure control.",
    },
    "kdigo2022diabetes": {
        "type": "Guideline",
        "authors": "KDIGO Diabetes Work Group",
        "year": 2022,
        "title": "KDIGO 2022 Clinical Practice Guideline for Diabetes Management in Chronic Kidney Disease",
        "source": "Kidney International 102(5S):S1-S127",
        "doi": "10.1016/j.kint.2022.06.008",
        "note": "Clinical guideline for SGLT2i, RAS blockade, and glycemic management in diabetes + CKD.",
    },
    # --- Phase 27: dose sources for cases 2-3 ---
    "kdigo2021bp": {
        "type": "Guideline",
        "authors": "KDIGO Blood Pressure Work Group (Cheung AK, Chang TI, et al.)",
        "year": 2021,
        "title": "KDIGO 2021 Clinical Practice Guideline for the Management of Blood Pressure "
                 "in Chronic Kidney Disease",
        "source": "Kidney International 99(3S):S1-S87",
        "doi": "10.1016/j.kint.2020.11.003",
        "note": "Blood-pressure management in CKD: target <120 mmHg systolic, ACEi/ARB first-line "
                "in albuminuria, titrated to the highest tolerated approved dose.",
    },
    "agarwal2021click": {
        "type": "RCT",
        "authors": "Agarwal R., Sinha A.D., Cramer A.E., et al.",
        "year": 2021,
        "title": "Chlorthalidone for Hypertension in Advanced Chronic Kidney Disease",
        "source": "N Engl J Med 385(27):2507-2519",
        "doi": "10.1056/NEJMoa2110730",
        "note": "The CLICK trial: chlorthalidone achieved effective blood-pressure lowering in "
                "advanced CKD (eGFR <30).",
    },
}

def reference_card(ref):
    """Renders a single reference as a bibliography entry (hanging indent, type label, DOI)."""
    year = f" ({ref['year']})" if ref.get("year") else ""
    where = [x for x in (ref.get("source"), (f"ISBN {ref['isbn']}" if ref.get("isbn") else None)) if x]
    if ref.get("doi"):
        link = f" <a href='https://doi.org/{ref['doi']}' target='_blank'>doi:{ref['doi']}</a>"
    elif ref.get("url"):
        link = f" <a href='{ref['url']}' target='_blank'>{ref['url'].replace('https://', '')}</a>"
    else:
        link = ""
    gloss = f"<span class='gloss'>{ref['note']}</span>" if ref.get("note") else ""
    st.markdown(
        f"<div class='nd-ref'><span class='nd-label'>{ref.get('type', 'Reference')}</span>"
        f"{ref.get('authors', '')}{year}. {ref.get('title', '')}. <i>{'; '.join(where)}</i>.{link}{gloss}</div>",
        unsafe_allow_html=True,
    )

def references_box(keys, title="References", extra_note=None, open=False):
    """'References' section (expander) for the given reference keys.
    Silently skips an undefined key — never draws a fabricated entry."""
    with st.expander(title, expanded=open):
        for k in keys:
            ref = REFERENCES.get(k)
            if ref:
                reference_card(ref)
        if extra_note:
            st.caption(extra_note)
