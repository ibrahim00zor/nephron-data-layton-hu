"""
app.py — Nephron Data (Layton/Hu) · Home

Main file in the Streamlit multi-page layout. Sub-pages are reached from the left menu.
"""
import streamlit as st
import plotly.express as px

from ui_kit import setup_page, render_sidebar, q, DB

setup_page("Home")
scenario = render_sidebar()

# ============================================================
#  Title + citation card
# ============================================================
st.markdown(
    "<h1 style='margin-bottom:0.2rem;letter-spacing:-0.02em;'>Nephron Data (Layton/Hu)</h1>"
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
#  Example questions
# ============================================================
st.markdown("#### Example questions")
st.caption("Each of the three cards below represents a research question as a concrete chart. "
           "For detailed analysis, go to the relevant page from the left menu.")

q1, q2, q3 = st.columns(3)

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
    fig = px.line(df, x="position", y="value", color="series", height=170,
                  color_discrete_map={"♀": "#dc2626", "♂": "#1e40af"})
    fig.update_layout(margin=dict(l=10, r=10, t=5, b=5),
                      legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center",
                                  title_text=""),
                      xaxis_title=None, yaxis_title=None)
    fig.update_traces(line=dict(width=2.2))
    st.markdown(
        "<div style='border-left:3px solid #dc2626;padding-left:10px;margin-bottom:4px;'>"
        "<b>Sex difference</b><br>"
        "<span style='color:#6b7280;font-size:0.85rem;'>mTAL lumen Na &mdash; ♀ vs ♂</span>"
        "</div>", unsafe_allow_html=True,
    )
    st.plotly_chart(fig, width='stretch')
    st.caption("→ Detail: **Nephron Types** or **Comparison**")

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
    fig = px.line(df, x="position", y="value", color="series", height=170,
                  color_discrete_map={"Normal": "#059669", "Diabetes": "#d97706"})
    fig.update_layout(margin=dict(l=10, r=10, t=5, b=5),
                      legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center",
                                  title_text=""),
                      xaxis_title=None, yaxis_title=None)
    fig.update_traces(line=dict(width=2.2))
    st.markdown(
        "<div style='border-left:3px solid #d97706;padding-left:10px;margin-bottom:4px;'>"
        "<b>Diabetes effect</b><br>"
        "<span style='color:#6b7280;font-size:0.85rem;'>PT lumen glucose &mdash; normal vs diabetes</span>"
        "</div>", unsafe_allow_html=True,
    )
    st.plotly_chart(fig, width='stretch')
    st.caption("→ Detail: **Comparison**")

# Card 3: Medullary gradient
with q3:
    df = q(
        f"""SELECT position, value, segment FROM {DB}
            WHERE variable='osmolality' AND compartment='Bath' AND nephron='merged'
                  AND condition='F_normal' AND segment IN ('CCD','OMCD','IMCD')
            ORDER BY segment, position""",
        [],
    )
    fig = px.line(df, x="position", y="value", color="segment", height=170,
                  category_orders={"segment": ["CCD", "OMCD", "IMCD"]})
    fig.update_layout(margin=dict(l=10, r=10, t=5, b=5),
                      legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center",
                                  title_text=""),
                      xaxis_title=None, yaxis_title=None)
    fig.update_traces(line=dict(width=2.2))
    st.markdown(
        "<div style='border-left:3px solid #1e40af;padding-left:10px;margin-bottom:4px;'>"
        "<b>Medullary gradient</b><br>"
        "<span style='color:#6b7280;font-size:0.85rem;'>Interstitial osmolality, CCD → IMCD</span>"
        "</div>", unsafe_allow_html=True,
    )
    st.plotly_chart(fig, width='stretch')
    st.caption("→ Detail: **Whole Nephron**")

# ============================================================
#  How to use
# ============================================================
st.markdown("---")
st.markdown("#### How to use")
st.markdown("""
1. **In the left panel,** pick an *Active scenario* (default: healthy female). The selection is kept even when you change pages.
2. **Pick a page** from the left menu:
   - **Segment Profile** — one solute in one segment, Lumen+Bath overlay, automatic mass/volume interpretation
   - **Whole Nephron** — chained flow chart from PT → IMCD
   - **Nephron Types** — sup and jux1–5 (effect of depth)
   - **Comparison** — several scenarios overlaid (e.g. normal vs diabetes)
   - **Validation** — automatic test of the model's agreement with the textbook
   - **Data Integrity** — categories, known limits
3. Citation info (source + DOI) is available under every chart.
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
        "<b style='color:#374151;'>Model limit</b><br>"
        "<span style='color:#4b5563;font-size:0.92rem;'>"
        "Inner-medullary osmotic gradient ~734 mOsm; literature ~1200 mOsm (max ADH). "
        "The inner-medullary concentrating mechanism is <b>not fully reproduced</b> by "
        "mathematical models — an open problem.</span>"
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
    "Model: Hu R., et al. (2021). *Sex differences in solute and water handling in "
    "the human kidney.* iScience 24(6):102694. &nbsp;·&nbsp; "
    "This tool: Zor İ. (2026). *Nephron Data (Layton/Hu).* Zenodo. "
    "doi:10.5281/zenodo.20489610 &nbsp;·&nbsp; "
    "License: MIT (code) + CC-BY 4.0 (content)"
)
