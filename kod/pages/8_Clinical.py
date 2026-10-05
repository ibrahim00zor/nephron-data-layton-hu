"""
8_Clinical.py — Clinical World — Educational Interface

The second leg of the project's "two-world" architecture. The model world (pages 1-7)
inspects data; this page combines clinical context, an example case, and model data.

SAFETY / FRAMING:
- EDUCATIONAL; NOT clinical decision support.
- Drug/dose/mechanism content will be taken ONLY from a verified article.
- Awaiting clinician/professor verification.
- Science audit: "load/reabsorption" -> FLUX (flow); macula densa = cTAL.
"""
import streamlit as st
import plotly.express as px
from ui_kit import (
    setup_page, render_sidebar, q, DB, cite_footer, references_box
)

setup_page("Clinical")
render_sidebar()

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


# ================================================================
# CASE SELECTION (BUTTONS)
# ================================================================
st.markdown("### Clinical Cases")
st.caption("Pick a case — the model data opens up. Clinical content will be filled in once "
           "the source article is loaded.")

if "clinical_case" not in st.session_state:
    st.session_state.clinical_case = "SGLT2"

k1, k2, k3 = st.columns(3)

with k1:
    if st.button("SGLT2 Inhibition", width='stretch',
                 type="primary" if st.session_state.clinical_case == "SGLT2" else "secondary"):
        st.session_state.clinical_case = "SGLT2"
        st.rerun()

with k2:
    if st.button("Diabetic Hyperfiltration", width='stretch',
                 type="primary" if st.session_state.clinical_case == "Hyperfiltration" else "secondary"):
        st.session_state.clinical_case = "Hyperfiltration"
        st.rerun()

with k3:
    if st.button("Hypertension", width='stretch',
                 type="primary" if st.session_state.clinical_case == "Hypertension" else "secondary"):
        st.session_state.clinical_case = "Hypertension"
        st.rerun()

case = st.session_state.clinical_case
st.markdown("---")


# ================================================================
# CASE 1: SGLT2 Inhibition
# ================================================================
if case == "SGLT2":
    st.markdown("### Case 1: SGLT2 Inhibition and TGF Restoration")
    cmap1 = {"Normal": "#dc2626", "SGLT2 Inhibition": "#be185d"}

    # --- Data queries ---
    df_glu = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN ('F_normal', 'F_SGLT2')
          AND variable='con' AND solute='glu' AND segment='PT' AND compartment='Lumen' AND nephron='sup'
        ORDER BY condition, position
    """)
    df_glu["condition"] = df_glu["condition"].map({"F_normal": "Normal", "F_SGLT2": "SGLT2 Inhibition"})
    df_na_con = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN ('F_normal', 'F_SGLT2')
          AND variable='con' AND solute='Na' AND segment='cTAL' AND compartment='Lumen' AND nephron='sup'
        ORDER BY condition, position
    """)
    df_na_con["condition"] = df_na_con["condition"].map({"F_normal": "Normal", "F_SGLT2": "SGLT2 Inhibition"})
    df_na_flow = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN ('F_normal', 'F_SGLT2')
          AND variable='flow' AND solute='Na' AND segment='cTAL' AND compartment='Lumen' AND nephron='sup'
        ORDER BY condition, position
    """)
    df_na_flow["condition"] = df_na_flow["condition"].map({"F_normal": "Normal", "F_SGLT2": "SGLT2 Inhibition"})
    con_n, con_s = _outlet(df_na_con, "Normal"), _outlet(df_na_con, "SGLT2 Inhibition")
    flw_n, flw_s = _outlet(df_na_flow, "Normal"), _outlet(df_na_flow, "SGLT2 Inhibition")
    glu_n, glu_s = _outlet(df_glu, "Normal"), _outlet(df_glu, "SGLT2 Inhibition")

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
                             "Glucose (mM)", cmap1),
            width='stretch',
        )
        st.markdown("#### 2. Sodium reaching the macula densa (cTAL outlet)")
        st.caption("Macula densa = the cortical end of the thick ascending limb (cTAL outlet).")
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(
                plot_case_metric(df_na_con, "position", "value", "condition",
                                 "cTAL Lumen Na+ Concentration", "Na+ (mM)", cmap1),
                width='stretch',
            )
        with g2:
            st.plotly_chart(
                plot_case_metric(df_na_flow, "position", "value", "condition",
                                 "cTAL Lumen Na+ Flux", "Na+ flux (pmol/min)", cmap1),
                width='stretch',
            )
        st.success(
            f"**Model data:** load reaching the macula densa = {_percent(flw_s, flw_n):+.0f}% "
            f"(flux: {flw_n:,.0f} -> {flw_s:,.0f} pmol/min); concentration = {_percent(con_s, con_n):+.0f}% "
            f"({con_n:.0f} -> {con_s:.0f} mM)."
        )
        st.markdown("---")
        st.page_link("pages/4_Comparison.py",
                      label="Inspect F_normal vs F_SGLT2 side by side on the Comparison page",
                      icon=":material/search:")

    with t_ref:
        references_box(
            ["hu2021"],
            title="References — Case 1", open=True,
        )
        st.info("Additional references will be added once the source article is loaded.")


# ================================================================
# CASE 2: Diabetic Hyperfiltration
# ================================================================
elif case == "Hyperfiltration":
    st.markdown("### Case 2: Diabetic Hyperfiltration")
    cmap2 = {"Normal": "#dc2626", "Diabetes": "#ea580c"}

    df_flow_pt = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN ('F_normal', 'F_diab_mod')
          AND variable='water_volume' AND segment='PT' AND compartment='Lumen' AND nephron='sup'
        ORDER BY condition, position
    """)
    df_flow_pt["condition"] = df_flow_pt["condition"].map({"F_normal": "Normal", "F_diab_mod": "Diabetes"})
    df_na_flow_pt = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN ('F_normal', 'F_diab_mod')
          AND variable='flow' AND solute='Na' AND segment='PT' AND compartment='Lumen' AND nephron='sup'
        ORDER BY condition, position
    """)
    df_na_flow_pt["condition"] = df_na_flow_pt["condition"].map({"F_normal": "Normal", "F_diab_mod": "Diabetes"})
    qg_n, qg_d = _inlet(df_flow_pt, "Normal"), _inlet(df_flow_pt, "Diabetes")
    reab_n, reab_d = _absorbed(df_na_flow_pt, "Normal"), _absorbed(df_na_flow_pt, "Diabetes")

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
                             "Volume (nl/min)", cmap2),
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
                             "Na+ flux (pmol/min)", cmap2),
            width='stretch',
        )
        st.warning(
            f"**Mass:** Na+ reabsorbed in the PT Normal **{reab_n:,.0f}** -> Diabetes **{reab_d:,.0f} pmol/min** "
            f"({_percent(reab_d, reab_n):+.0f}%)."
        )
        st.markdown("---")
        st.page_link("pages/4_Comparison.py",
                      label="Inspect F_normal vs F_diab_mod side by side on the Comparison page",
                      icon=":material/search:")

    with t_ref:
        references_box(
            ["hu2021"],
            title="References — Case 2", open=True,
        )
        st.info("Additional references will be added once the source article is loaded.")


# ================================================================
# CASE 3: Hypertension
# ================================================================
elif case == "Hypertension":
    st.markdown("### Case 3: Hypertension")
    cmap3 = {"Normal": "#dc2626", "Hypertension": "#a16207"}

    df_na_con_tal = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN ('F_normal', 'F_HT')
          AND variable='con' AND solute='Na' AND segment='mTAL' AND compartment='Lumen' AND nephron='sup'
        ORDER BY condition, position
    """)
    df_na_con_tal["condition"] = df_na_con_tal["condition"].map({"F_normal": "Normal", "F_HT": "Hypertension"})
    df_na_flow_tal = q(f"""
        SELECT position, value, condition FROM {DB}
        WHERE condition IN ('F_normal', 'F_HT')
          AND variable='flow' AND solute='Na' AND segment='mTAL' AND compartment='Lumen' AND nephron='sup'
        ORDER BY condition, position
    """)
    df_na_flow_tal["condition"] = df_na_flow_tal["condition"].map({"F_normal": "Normal", "F_HT": "Hypertension"})
    cin_n, cin_h = _inlet(df_na_con_tal, "Normal"), _inlet(df_na_con_tal, "Hypertension")
    cout_n, cout_h = _outlet(df_na_con_tal, "Normal"), _outlet(df_na_con_tal, "Hypertension")
    fout_n, fout_h = _outlet(df_na_flow_tal, "Normal"), _outlet(df_na_flow_tal, "Hypertension")

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
                                 "mTAL Lumen Na+ Concentration (mM)", "Na+ (mM)", cmap3),
                width='stretch',
            )
        with h2:
            st.plotly_chart(
                plot_case_metric(df_na_flow_tal, "position", "value", "condition",
                                 "mTAL Lumen Na+ Flux (load)", "Na+ flux (pmol/min)", cmap3),
                width='stretch',
            )
        st.caption(
            f"Load at the mTAL outlet in hypertension: {fout_n:,.0f} -> {fout_h:,.0f} pmol/min "
            f"({_percent(fout_h, fout_n):+.0f}%)."
        )
        st.markdown("---")
        st.page_link("pages/4_Comparison.py",
                      label="Inspect F_normal vs F_HT side by side on the Comparison page",
                      icon=":material/search:")

    with t_ref:
        references_box(
            ["hu2021"],
            title="References — Case 3", open=True,
        )
        st.info("Additional references will be added once the source article is loaded.")

cite_footer()
