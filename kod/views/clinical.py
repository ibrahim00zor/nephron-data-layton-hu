"""
clinical.py — Clinical World — Educational Interface

The second leg of the project's "two-world" architecture. The model world inspects data;
this page combines clinical context, an example case, and model data, and links each case
back into the model pages with its scenarios and focus preselected.

SAFETY / FRAMING:
- EDUCATIONAL; NOT clinical decision support.
- Drug/dose/mechanism content will be taken ONLY from a verified article.
- Awaiting clinician/professor verification.
- Science audit: "load/reabsorption" -> FLUX (flow); macula densa = cTAL.
"""
import streamlit as st
import plotly.express as px

import nav
from clinical_cases import CASES, REFERENCE_COLOR
from ui_kit import q, DB, cite_footer, references_box

# ================================================================
# BANNER — Clinical World identity
# ================================================================
st.markdown(
    """<div style="
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 10px;
        margin-bottom: 16px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <div style="font-size: 1.5rem; font-weight: 700; letter-spacing: 0.02em;">
                    Clinical Education Interface
                </div>
                <div style="font-size: 0.88rem; opacity: 0.85; margin-top: 4px;">
                    Example cases and model data — under one roof
                </div>
            </div>
            <div style="font-size: 0.78rem; opacity: 0.7; text-align: right;">
                Educational — not medical advice
            </div>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

st.warning(
    "**Educational — not medical advice.** The charts here are the output of a mathematical "
    "model (Hu et al. 2021); they are not real patient data. They cannot be used for diagnosis, "
    "treatment, or patient-care decisions."
)

# ================================================================
# HELPER FUNCTIONS
# ================================================================

def plot_case_metric(df, x_col, y_col, color_col, title, y_title, colors):
    fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title,
                  color_discrete_map=colors)
    fig.update_layout(hovermode="x unified", height=350,
                      margin=dict(l=10, r=10, t=40, b=10))
    fig.update_traces(line=dict(width=3))
    return fig


def _inlet(df, label):
    s = df.loc[df["condition"] == label, "value"]
    return float(s.iloc[0]) if len(s) else float("nan")

def _outlet(df, label):
    s = df.loc[df["condition"] == label, "value"]
    return float(s.iloc[-1]) if len(s) else float("nan")

def _absorbed(df, label):
    s = df.loc[df["condition"] == label, "value"]
    return float(s.iloc[0] - s.iloc[-1]) if len(s) else float("nan")

def _percent(new, base):
    return 100.0 * (new - base) / base if base else float("nan")


def case_profile(case, variable, segment, solute=None):
    """Profile of one variable for the case's scenario and its reference, labelled for charts."""
    solute_clause = "AND solute=?" if solute else ""
    params = [case["reference"], case["scenario"], variable, segment] + ([solute] if solute else [])
    df = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN (?, ?)
          AND variable=? AND segment=? AND compartment='Lumen' AND nephron='sup' {solute_clause}
        ORDER BY condition, position
    """, params)
    df["condition"] = df["condition"].map({case["reference"]: "Normal", case["scenario"]: case["label"]})
    return df


def model_world_links(case_key):
    """Clinical world -> model world: open the model pages with this case's context applied."""
    case = CASES[case_key]
    pair = [case["reference"], case["scenario"]]
    focus = case["focus"]
    st.markdown("---")
    st.markdown("**Go deeper in the model world**")
    st.caption(f"Each button opens the page with this case's scenarios (`{pair[0]}` vs `{pair[1]}`) and "
               f"its focus ({focus['segment']} · {focus['solute']}) already selected. "
               f"A link on that page brings you back here.")
    b1, b2, b3 = st.columns(3)
    if b1.button("Compare the two scenarios", key=f"case_{case_key}_cmp", width="stretch"):
        nav.go("comparison", back_label=case["title"], compare=pair,
               nephron="sup", compartment="Lumen", **focus)
    if b2.button(f"Segment profile ({focus['segment']})", key=f"case_{case_key}_seg", width="stretch"):
        nav.go("segment", back_label=case["title"], scenario=case["scenario"], nephron="sup", **focus)
    if b3.button("Interactive anatomy", key=f"case_{case_key}_ana", width="stretch"):
        nav.go("anatomy", back_label=case["title"], scenario=case["scenario"],
               nephron="sup", compartment="Lumen", **focus)


# ================================================================
# CASE SELECTION (BUTTONS)
# ================================================================
st.markdown("### Clinical Cases")
st.caption("Pick a case — the model data opens up. Clinical content will be filled in once "
           "the source article is loaded.")

case_key = nav.get("case")
if case_key not in CASES:
    case_key = next(iter(CASES))
    nav.put(case=case_key)

for column, (key, spec) in zip(st.columns(len(CASES)), CASES.items()):
    if column.button(spec["button"], key=f"case_pick_{key}", width="stretch",
                     type="primary" if key == case_key else "secondary"):
        nav.put(case=key)
        st.rerun()

case = CASES[case_key]
colors = {"Normal": REFERENCE_COLOR, case["label"]: case["color"]}
st.markdown("---")


# ================================================================
# CASE 1: SGLT2 Inhibition
# ================================================================
if case_key == "SGLT2":
    st.markdown(f"### {case['title']}")

    # --- Data queries ---
    df_glu = case_profile(case, "con", "PT", "glu")
    df_na_con = case_profile(case, "con", "cTAL", "Na")
    df_na_flow = case_profile(case, "flow", "cTAL", "Na")
    con_n, con_s = _outlet(df_na_con, "Normal"), _outlet(df_na_con, case["label"])
    flw_n, flw_s = _outlet(df_na_flow, "Normal"), _outlet(df_na_flow, case["label"])
    glu_n, glu_s = _outlet(df_glu, "Normal"), _outlet(df_glu, case["label"])

    # --- Patient summary card ---
    with st.container(border=True):
        st.markdown("##### Patient Summary")
        st.info("The patient profile and clinical context will be filled in once the source article is loaded.")
        k1, k2, k3 = st.columns(3)
        k1.metric("Na load to macula densa", f"{flw_s:,.0f} pmol/min",
                   f"{_percent(flw_s, flw_n):+.0f}%", delta_color="off")
        k2.metric("Macula densa Na conc.", f"{con_s:.0f} mM",
                   f"{_percent(con_s, con_n):+.0f}%", delta_color="off")
        k3.metric("PT glucose outlet", f"{glu_s:.1f} mM",
                   f"{glu_s - glu_n:+.1f} mM", delta_color="off")
        st.caption("Metrics give the difference of `F_SGLT2` relative to `F_normal`.")

    # --- 4 Tabs ---
    t_mech, t_drug, t_model, t_ref = st.tabs(
        ["Mechanism and Physiology", "Drug and Dose Approach", "Model Data", "References"]
    )

    with t_mech:
        st.info("The mechanism description will be filled in once the source article is loaded.")

    with t_drug:
        st.info("Drug and dose information will be filled in once the source article is loaded.")

    with t_model:
        st.markdown("#### 1. Glucose excretion in the proximal tubule")
        st.plotly_chart(
            plot_case_metric(df_glu, "position", "value", "condition",
                             "PT Lumen Glucose Concentration (mM)",
                             "Glucose (mM)", colors),
            width='stretch',
        )
        st.markdown("#### 2. Sodium reaching the macula densa (cTAL outlet)")
        st.caption("Macula densa = the cortical end of the thick ascending limb (cTAL outlet).")
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(
                plot_case_metric(df_na_con, "position", "value", "condition",
                                 "cTAL Lumen Na+ Concentration", "Na+ (mM)", colors),
                width='stretch',
            )
        with g2:
            st.plotly_chart(
                plot_case_metric(df_na_flow, "position", "value", "condition",
                                 "cTAL Lumen Na+ Flux", "Na+ flux (pmol/min)", colors),
                width='stretch',
            )
        st.success(
            f"**Model data:** load reaching the macula densa = {_percent(flw_s, flw_n):+.0f}% "
            f"(flux: {flw_n:,.0f} -> {flw_s:,.0f} pmol/min); concentration = {_percent(con_s, con_n):+.0f}% "
            f"({con_n:.0f} -> {con_s:.0f} mM)."
        )
        model_world_links(case_key)

    with t_ref:
        references_box(["hu2021"], title="References — Case 1", open=True)
        st.info("Additional references will be added once the source article is loaded.")


# ================================================================
# CASE 2: Diabetic Hyperfiltration
# ================================================================
elif case_key == "Hyperfiltration":
    st.markdown(f"### {case['title']}")

    df_flow_pt = case_profile(case, "water_volume", "PT")
    df_na_flow_pt = case_profile(case, "flow", "PT", "Na")
    qg_n, qg_d = _inlet(df_flow_pt, "Normal"), _inlet(df_flow_pt, case["label"])
    reab_n, reab_d = _absorbed(df_na_flow_pt, "Normal"), _absorbed(df_na_flow_pt, case["label"])

    # --- Patient summary card ---
    with st.container(border=True):
        st.markdown("##### Patient Summary")
        st.info("The patient profile and clinical context will be filled in once the source article is loaded.")
        k1, k2 = st.columns(2)
        k1.metric("PT inlet water flow (filtration)", f"{qg_d:.0f} nl/min",
                   f"{_percent(qg_d, qg_n):+.0f}%", delta_color="off")
        k2.metric("Na reabsorbed in PT (mass)", f"{reab_d:,.0f} pmol/min",
                   f"{_percent(reab_d, reab_n):+.0f}%", delta_color="off")
        st.caption("Metrics give the difference of `F_diab_mod` relative to `F_normal`.")

    # --- 4 Tabs ---
    t_mech, t_drug, t_model, t_ref = st.tabs(
        ["Mechanism and Physiology", "Drug and Dose Approach", "Model Data", "References"]
    )

    with t_mech:
        st.info("The mechanism description will be filled in once the source article is loaded.")

    with t_drug:
        st.info("Drug and dose information will be filled in once the source article is loaded.")

    with t_model:
        st.markdown("#### 1. Increased volume load entering the proximal tubule")
        st.plotly_chart(
            plot_case_metric(df_flow_pt, "position", "value", "condition",
                             "PT Water Volume Flow (nl/min)",
                             "Volume (nl/min)", colors),
            width='stretch',
        )
        st.caption(f"PT inlet water flow in diabetes: {qg_n:.0f} -> {qg_d:.0f} nl/min "
                   f"({_percent(qg_d, qg_n):+.0f}%).")
        st.markdown("#### 2. Sodium reabsorption (mass)")
        st.caption("In the PT the Na+ concentration is nearly constant at ~140 mM (iso-osmotic); "
                   "reabsorption shows in the **flux (mass)**.")
        st.plotly_chart(
            plot_case_metric(df_na_flow_pt, "position", "value", "condition",
                             "PT Lumen Na+ Flux (load)",
                             "Na+ flux (pmol/min)", colors),
            width='stretch',
        )
        st.warning(
            f"**Mass:** Na+ reabsorbed in the PT Normal **{reab_n:,.0f}** -> Diabetes **{reab_d:,.0f} pmol/min** "
            f"({_percent(reab_d, reab_n):+.0f}%)."
        )
        model_world_links(case_key)

    with t_ref:
        references_box(["hu2021"], title="References — Case 2", open=True)
        st.info("Additional references will be added once the source article is loaded.")


# ================================================================
# CASE 3: Hypertension
# ================================================================
elif case_key == "Hypertension":
    st.markdown(f"### {case['title']}")

    df_na_con_tal = case_profile(case, "con", "mTAL", "Na")
    df_na_flow_tal = case_profile(case, "flow", "mTAL", "Na")
    cout_n, cout_h = _outlet(df_na_con_tal, "Normal"), _outlet(df_na_con_tal, case["label"])
    fout_n, fout_h = _outlet(df_na_flow_tal, "Normal"), _outlet(df_na_flow_tal, case["label"])

    # --- Patient summary card ---
    with st.container(border=True):
        st.markdown("##### Patient Summary")
        st.info("The patient profile and clinical context will be filled in once the source article is loaded.")
        k1, k2 = st.columns(2)
        k1.metric("mTAL outlet Na load", f"{fout_h:,.0f} pmol/min",
                   f"{_percent(fout_h, fout_n):+.0f}%", delta_color="off")
        k2.metric("mTAL outlet Na conc.", f"{cout_h:.0f} mM",
                   f"{cout_h - cout_n:+.0f} mM", delta_color="off")
        st.caption("Metrics give the difference of `F_HT` relative to `F_normal`.")

    # --- 4 Tabs ---
    t_mech, t_drug, t_model, t_ref = st.tabs(
        ["Mechanism and Physiology", "Drug and Dose Approach", "Model Data", "References"]
    )

    with t_mech:
        st.info("The mechanism description will be filled in once the source article is loaded.")

    with t_drug:
        st.info("Drug and dose information will be filled in once the source article is loaded.")

    with t_model:
        st.markdown("#### Sodium handling in the thick ascending limb (TAL)")
        st.caption("Left: lumen concentration. Right: lumen flux (load delivered distally).")
        h1, h2 = st.columns(2)
        with h1:
            st.plotly_chart(
                plot_case_metric(df_na_con_tal, "position", "value", "condition",
                                 "mTAL Lumen Na+ Concentration (mM)", "Na+ (mM)", colors),
                width='stretch',
            )
        with h2:
            st.plotly_chart(
                plot_case_metric(df_na_flow_tal, "position", "value", "condition",
                                 "mTAL Lumen Na+ Flux (load)", "Na+ flux (pmol/min)", colors),
                width='stretch',
            )
        st.caption(
            f"Load at the mTAL outlet in hypertension: {fout_n:,.0f} -> {fout_h:,.0f} pmol/min "
            f"({_percent(fout_h, fout_n):+.0f}%)."
        )
        model_world_links(case_key)

    with t_ref:
        references_box(["hu2021"], title="References — Case 3", open=True)
        st.info("Additional references will be added once the source article is loaded.")

cite_footer()
