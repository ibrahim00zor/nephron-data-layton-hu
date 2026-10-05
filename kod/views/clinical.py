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
import style
from clinical_cases import CASES, REFERENCE_COLOR
from ui_kit import q, DB, figure, references_box, scenario_word

# ================================================================
# HEADING
# ================================================================
st.markdown("## Clinical Cases")
st.markdown(
    "<p class='nd-lede' style='font-size:1.08rem;'>Three teaching cases, each built on one of the model's "
    "scenarios. The clinical text is still to be written and will come only from a verified source; "
    "what is here now is the structure and the model data behind each case.</p>",
    unsafe_allow_html=True,
)
st.warning(
    "**For teaching only — not medical advice.** The charts are the output of a mathematical model "
    "(Hu et al. 2021), not patient data. They cannot be used for diagnosis, treatment, or any "
    "decision about a patient."
)

# ================================================================
# HELPER FUNCTIONS
# ================================================================

def plot_case_metric(df, x_col, y_col, color_col, title, y_title, colors):
    fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title,
                  color_discrete_map=colors,
                  labels={x_col: "Position along the segment (0 = inlet, 1 = outlet)", y_col: y_title,
                          color_col: ""})
    fig.update_layout(hovermode="x unified", height=350, legend=dict(title_text=""))
    fig.update_traces(line=dict(width=2), hovertemplate="%{y:.4g}")
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
    st.markdown("<div class='nd-label'>Continue in the model world</div>", unsafe_allow_html=True)
    st.caption(f"Each opens with this case's scenarios (`{pair[0]}` and `{pair[1]}`) and its focus "
               f"({focus['segment']}, {focus['solute']}) already selected, and offers a way back here.")
    with_transporters = "transporters" in nav.PAGES
    b1, b2, b3, *rest = st.columns(4 if with_transporters else 3)
    if with_transporters and rest[0].button(f"Transporters ({focus['segment']})",
                                            key=f"case_{case_key}_trn", width="stretch"):
        nav.go("transporters", back_label=case["title"], scenario=case["scenario"], compare=pair,
               nephron="sup", **focus)
    if b1.button("Comparison", key=f"case_{case_key}_cmp", width="stretch"):
        nav.go("comparison", back_label=case["title"], compare=pair,
               nephron="sup", compartment="Lumen", **focus)
    if b2.button(f"Segment profile ({focus['segment']})", key=f"case_{case_key}_seg", width="stretch"):
        nav.go("segment", back_label=case["title"], scenario=case["scenario"], nephron="sup", **focus)
    if b3.button("Anatomy", key=f"case_{case_key}_ana", width="stretch"):
        nav.go("anatomy", back_label=case["title"], scenario=case["scenario"],
               nephron="sup", compartment="Lumen", **focus)


# ================================================================
# CASE SELECTION (BUTTONS)
# ================================================================
st.markdown("<div class='nd-label' style='margin-top:0.6rem;'>Choose a case</div>", unsafe_allow_html=True)

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
    with st.container(border=True, key="nd_frame_1"):
        st.markdown("##### Patient summary")
        style.pending("Not written yet. The patient profile and clinical context wait for the source article.")
        k1, k2, k3 = st.columns(3)
        k1.metric("Na load to macula densa", f"{flw_s:,.0f} pmol/min",
                   f"{_percent(flw_s, flw_n):+.0f}%", delta_color="off")
        k2.metric("Macula densa Na conc.", f"{con_s:.0f} mM",
                   f"{_percent(con_s, con_n):+.0f}%", delta_color="off")
        k3.metric("PT glucose outlet", f"{glu_s:.1f} mM",
                   f"{glu_s - glu_n:+.1f} mM", delta_color="off")
        st.caption(f"Metrics give the difference of {scenario_word('F_SGLT2')} relative to "
                   f"{scenario_word('F_normal')}.")

    # --- 4 Tabs ---
    t_model, t_mech, t_drug, t_ref = st.tabs(
        ["Model data", "Mechanism and physiology", "Drug and dose", "References"]
    )

    with t_mech:
        style.pending("Not written yet. The mechanism will be described from the source article.")

    with t_drug:
        style.pending("Not written yet. Drug and dose information will be taken only from a verified source.")

    with t_model:
        st.markdown("#### 1. Glucose excretion in the proximal tubule")
        figure(
            plot_case_metric(df_glu, "position", "value", "condition",
                             "PT Lumen Glucose Concentration (mM)",
                             "Glucose (mM)", colors),
        )
        st.markdown("#### 2. Sodium reaching the macula densa (cTAL outlet)")
        st.caption("Macula densa = the cortical end of the thick ascending limb (cTAL outlet).")
        g1, g2 = st.columns(2)
        with g1:
            figure(
                plot_case_metric(df_na_con, "position", "value", "condition",
                                 "cTAL Lumen Na+ Concentration", "Na+ (mM)", colors),
            )
        with g2:
            figure(
                plot_case_metric(df_na_flow, "position", "value", "condition",
                                 "cTAL Lumen Na+ Flux", "Na+ flux (pmol/min)", colors),
            )
        st.success(
            f"**Model data:** load reaching the macula densa = {_percent(flw_s, flw_n):+.0f}% "
            f"(flux: {flw_n:,.0f} -> {flw_s:,.0f} pmol/min); concentration = {_percent(con_s, con_n):+.0f}% "
            f"({con_n:.0f} -> {con_s:.0f} mM)."
        )
        model_world_links(case_key)

    with t_ref:
        references_box(["hu2021"], title="References — Case 1", open=True)
        style.pending("Clinical references will be added with the source article.")


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
    with st.container(border=True, key="nd_frame_2"):
        st.markdown("##### Patient summary")
        style.pending("Not written yet. The patient profile and clinical context wait for the source article.")
        k1, k2 = st.columns(2)
        k1.metric("PT inlet water flow (filtration)", f"{qg_d:.0f} nl/min",
                   f"{_percent(qg_d, qg_n):+.0f}%", delta_color="off")
        k2.metric("Na reabsorbed in PT (mass)", f"{reab_d:,.0f} pmol/min",
                   f"{_percent(reab_d, reab_n):+.0f}%", delta_color="off")
        st.caption(f"Metrics give the difference of {scenario_word('F_diab_mod')} relative to "
                   f"{scenario_word('F_normal')}.")

    # --- 4 Tabs ---
    t_model, t_mech, t_drug, t_ref = st.tabs(
        ["Model data", "Mechanism and physiology", "Drug and dose", "References"]
    )

    with t_mech:
        style.pending("Not written yet. The mechanism will be described from the source article.")

    with t_drug:
        style.pending("Not written yet. Drug and dose information will be taken only from a verified source.")

    with t_model:
        st.markdown("#### 1. Increased volume load entering the proximal tubule")
        figure(
            plot_case_metric(df_flow_pt, "position", "value", "condition",
                             "PT Water Volume Flow (nl/min)",
                             "Volume (nl/min)", colors),
        )
        st.caption(f"PT inlet water flow in diabetes: {qg_n:.0f} -> {qg_d:.0f} nl/min "
                   f"({_percent(qg_d, qg_n):+.0f}%).")
        st.markdown("#### 2. Sodium reabsorption (mass)")
        st.caption("In the PT the Na+ concentration is nearly constant at ~140 mM (iso-osmotic); "
                   "reabsorption shows in the **flux (mass)**.")
        figure(
            plot_case_metric(df_na_flow_pt, "position", "value", "condition",
                             "PT Lumen Na+ Flux (load)",
                             "Na+ flux (pmol/min)", colors),
        )
        st.warning(
            f"**Mass:** Na+ reabsorbed in the PT Normal **{reab_n:,.0f}** -> Diabetes **{reab_d:,.0f} pmol/min** "
            f"({_percent(reab_d, reab_n):+.0f}%)."
        )
        model_world_links(case_key)

    with t_ref:
        references_box(["hu2021"], title="References — Case 2", open=True)
        style.pending("Clinical references will be added with the source article.")


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
    with st.container(border=True, key="nd_frame_3"):
        st.markdown("##### Patient summary")
        style.pending("Not written yet. The patient profile and clinical context wait for the source article.")
        k1, k2 = st.columns(2)
        k1.metric("mTAL outlet Na load", f"{fout_h:,.0f} pmol/min",
                   f"{_percent(fout_h, fout_n):+.0f}%", delta_color="off")
        k2.metric("mTAL outlet Na conc.", f"{cout_h:.0f} mM",
                   f"{cout_h - cout_n:+.0f} mM", delta_color="off")
        st.caption(f"Metrics give the difference of {scenario_word('F_HT')} relative to "
                   f"{scenario_word('F_normal')}.")

    # --- 4 Tabs ---
    t_model, t_mech, t_drug, t_ref = st.tabs(
        ["Model data", "Mechanism and physiology", "Drug and dose", "References"]
    )

    with t_mech:
        style.pending("Not written yet. The mechanism will be described from the source article.")

    with t_drug:
        style.pending("Not written yet. Drug and dose information will be taken only from a verified source.")

    with t_model:
        st.markdown("#### Sodium handling in the thick ascending limb (TAL)")
        st.caption("Left: lumen concentration. Right: lumen flux (load delivered distally).")
        h1, h2 = st.columns(2)
        with h1:
            figure(
                plot_case_metric(df_na_con_tal, "position", "value", "condition",
                                 "mTAL Lumen Na+ Concentration (mM)", "Na+ (mM)", colors),
            )
        with h2:
            figure(
                plot_case_metric(df_na_flow_tal, "position", "value", "condition",
                                 "mTAL Lumen Na+ Flux (load)", "Na+ flux (pmol/min)", colors),
            )
        st.caption(
            f"Load at the mTAL outlet in hypertension: {fout_n:,.0f} -> {fout_h:,.0f} pmol/min "
            f"({_percent(fout_h, fout_n):+.0f}%)."
        )
        model_world_links(case_key)

    with t_ref:
        references_box(["hu2021"], title="References — Case 3", open=True)
        style.pending("Clinical references will be added with the source article.")

