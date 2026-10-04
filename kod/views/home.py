"""home.py — Home: what the tool is, example questions as launch points, how to use it."""
import streamlit as st
import plotly.express as px

import nav
from ui_kit import APP_NAME, q, DB

# ============================================================
#  Title + citation card
# ============================================================
st.markdown(
    f"<h1 style='margin-bottom:0.2rem;letter-spacing:-0.02em;'>{APP_NAME}</h1>"
    "<div style='color:#6b7280;font-size:1.02rem;margin-bottom:1.2rem;'>"
    "Interactive data explorer for a human-nephron epithelial transport model"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown("""
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-left:4px solid #1e40af;
            border-radius:6px;padding:14px 18px;margin:0.5rem 0 1.5rem 0;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
    <div>
      <div style="font-size:0.74rem;color:#6b7280;text-transform:uppercase;
                  letter-spacing:0.08em;font-weight:600;">
        Citable science tool
      </div>
      <div style="font-weight:500;color:#1f2937;font-size:1rem;margin-top:4px;
                  font-family:Georgia,serif;">
        Zor, İ. (2026). Nephron Data (Layton/Hu). <i>Zenodo</i>.
      </div>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">
      <a href="https://doi.org/10.5281/zenodo.20489610" target="_blank"
         style="background:#1e40af;color:white;padding:5px 11px;border-radius:4px;
                font-size:0.78rem;text-decoration:none;font-weight:500;
                font-family:ui-monospace,SFMono-Regular,monospace;">
        DOI 10.5281/zenodo.20489610
      </a>
      <a href="https://github.com/ibrahim00zor/nefron-veri-gezgini" target="_blank"
         style="background:#374151;color:white;padding:5px 11px;border-radius:4px;
                font-size:0.78rem;text-decoration:none;font-weight:500;">
        GitHub
      </a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
#  Introduction
# ============================================================
st.markdown("#### What this tool does")
st.markdown(
    "Visualizes the output of the Layton/Hu human-nephron model (Hu et al. 2021, *iScience*) "
    "interactively for **6 scenarios** &mdash; healthy female and male, moderate diabetes, "
    "hypertension, and SGLT2 inhibitor (♀ and ♂). "
    "It traces the concentration profile along each segment, separates mass and volume, "
    "and generates the physiological interpretation automatically."
)
st.markdown("")

# ============================================================
#  Example questions — each card opens the matching page with its selection applied
# ============================================================
st.markdown("#### Example questions")
st.caption("Each card is a research question as a concrete chart. "
           "The button opens the detailed page with the same selection already applied.")

q1, q2, q3 = st.columns(3)


def _card_chart(df, color, color_map=None, category_orders=None):
    fig = px.line(df, x="position", y="value", color=color, height=170,
                  color_discrete_map=color_map, category_orders=category_orders or {})
    fig.update_layout(margin=dict(l=10, r=10, t=5, b=5),
                      legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center", title_text=""),
                      xaxis_title=None, yaxis_title=None)
    fig.update_traces(line=dict(width=2.2))
    return fig


def _card_title(color, heading, subtitle):
    st.markdown(
        f"<div style='border-left:3px solid {color};padding-left:10px;margin-bottom:4px;'>"
        f"<b>{heading}</b><br>"
        f"<span style='color:#6b7280;font-size:0.85rem;'>{subtitle}</span>"
        "</div>", unsafe_allow_html=True,
    )


# Card 1: Sex difference
with q1:
    df = q(
        f"""SELECT position, value, condition AS series FROM {DB}
            WHERE variable='con' AND solute='Na' AND segment='mTAL'
                  AND compartment='Lumen' AND nephron='sup'
                  AND condition IN ('F_normal','M_normal')
            ORDER BY condition, position""",
        [],
    )
    df["series"] = df["series"].map({"F_normal": "♀", "M_normal": "♂"})
    _card_title("#dc2626", "Sex difference", "mTAL lumen Na &mdash; ♀ vs ♂")
    st.plotly_chart(_card_chart(df, "series", {"♀": "#dc2626", "♂": "#1e40af"}), width='stretch')
    if st.button("Open in Comparison", key="home_q1", width="stretch"):
        nav.go("comparison", back_label="example question: sex difference",
               compare=["F_normal", "M_normal"], solute="Na", segment="mTAL",
               nephron="sup", compartment="Lumen")

# Card 2: Diabetes
with q2:
    df = q(
        f"""SELECT position, value, condition AS series FROM {DB}
            WHERE variable='con' AND solute='glu' AND segment='PT'
                  AND compartment='Lumen' AND nephron='sup'
                  AND condition IN ('F_normal','F_diab_mod')
            ORDER BY condition, position""",
        [],
    )
    df["series"] = df["series"].map({"F_normal": "Normal", "F_diab_mod": "Diabetes"})
    _card_title("#d97706", "Diabetes effect", "PT lumen glucose &mdash; normal vs diabetes")
    st.plotly_chart(_card_chart(df, "series", {"Normal": "#059669", "Diabetes": "#d97706"}), width='stretch')
    if st.button("Open in Comparison", key="home_q2", width="stretch"):
        nav.go("comparison", back_label="example question: diabetes effect",
               compare=["F_normal", "F_diab_mod"], solute="glu", segment="PT",
               nephron="sup", compartment="Lumen")

# Card 3: Medullary gradient
with q3:
    df = q(
        f"""SELECT position, value, segment FROM {DB}
            WHERE variable='osmolality' AND compartment='Bath' AND nephron='merged'
                  AND condition='F_normal' AND segment IN ('CCD','OMCD','IMCD')
            ORDER BY segment, position""",
        [],
    )
    _card_title("#1e40af", "Medullary gradient", "Interstitial osmolality, CCD → IMCD (a model input)")
    st.plotly_chart(_card_chart(df, "segment", category_orders={"segment": ["CCD", "OMCD", "IMCD"]}),
                    width='stretch')
    if st.button("Open in Whole Nephron", key="home_q3", width="stretch"):
        nav.go("nephron", back_label="example question: medullary gradient",
               scenario="F_normal", solute="Na", compartment="Bath", nephron="sup")

# ============================================================
#  How to use
# ============================================================
st.markdown("---")
st.markdown("#### How to use")
st.markdown(f"""
1. **In the left panel,** pick an *Active scenario* (default: healthy female).
2. **Pick a page** from the menu. It is organised in two worlds:
   - **{nav.MODEL}** — explore the model output:
     **Segment Profile** (one solute in one segment, with an automatic mass/volume interpretation) ·
     **Whole Nephron** (chained profile from PT → IMCD) ·
     **Nephron Types** (superficial vs juxtamedullary) ·
     **Comparison** (several scenarios overlaid) ·
     **Transporters** (membrane fluxes per pathway and transporter) ·
     **Interactive Anatomy** (the nephron as a diagram).
   - **{nav.CLINICAL}** — **Clinical Cases**: educational cases built on the same scenarios.
   - **{nav.QUALITY}** — **Validation** (automatic physiology checks), **Data Integrity** (inventory, known limits)
     and **Model & Provenance** (the exact model commands, what the model is given, how to reproduce the data).
3. **Your selection travels with you.** The scenario, solute, segment and nephron type you choose
   on one page are what the next page opens with, so you can follow one question across views.
   A clinical case opens its scenarios in the model pages, and a scenario links back to its case.
4. Citation info (source + DOI) is available under every chart.
""")

# ============================================================
#  Limits
# ============================================================
st.markdown("---")
st.markdown("#### Known limits")
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        "<div style='border:1px solid #e5e7eb;border-left:3px solid #6b7280;"
        "padding:10px 14px;border-radius:4px;'>"
        "<b style='color:#374151;'>The interstitium is an input</b><br>"
        "<span style='color:#4b5563;font-size:0.92rem;'>"
        "The interstitial fluid composition is <b>prescribed, not computed</b>: it is specified at "
        "the cortex, the outer–inner medullary boundary and the papillary tip and interpolated "
        "linearly in between (Layton &amp; Layton 2019, Table 2). The ~734 mOsm at the papillary tip "
        "is therefore a setting, identical in all six scenarios — not a prediction — and is below "
        "the ~1200 mOsm reported for maximal antidiuresis. The model has no vasculature and does "
        "not simulate how the medullary gradient is generated.</span>"
        "</div>", unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        "<div style='border:1px solid #e5e7eb;border-left:3px solid #6b7280;"
        "padding:10px 14px;border-radius:4px;'>"
        "<b style='color:#374151;'>Scenario library</b><br>"
        "<span style='color:#4b5563;font-size:0.92rem;'>"
        "6 scenarios succeeded (10 were targeted). 4 scenarios failed to converge with "
        "Newton overflow: F_diab_severe, F_ACE, F_obese, F_UNX. "
        "A <b>numerical limit</b> of the model.</span>"
        "</div>", unsafe_allow_html=True,
    )

# ============================================================
#  Footer
# ============================================================
st.markdown("---")
st.caption(
    "Model: Hu R., McDonough A.A., Layton A.T. (2021). *Sex differences in solute and water "
    "handling in the human kidney.* iScience 24(6):102667. &nbsp;·&nbsp; "
    "This tool: Zor İ. (2026). *Nephron Data (Layton/Hu).* Zenodo. "
    "doi:10.5281/zenodo.20489610 &nbsp;·&nbsp; "
    "License: MIT (code) + CC-BY 4.0 (content)"
)
