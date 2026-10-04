"""data_integrity.py — What is in the dataset, what converged, and what to know about it."""
import os
import streamlit as st

import nephron_figure
import style
from ui_kit import q, DB, PARQUET, integrity_map, segment_names

st.markdown("## Data Integrity")
st.caption(f"Everything in the app is read from one tidy table, `{os.path.basename(PARQUET)}`. "
           f"This page counts what is in it.")

# ------------------------------------------------------------
#  Inventory
# ------------------------------------------------------------
st.markdown("### What is in the table")

st.markdown("<div class='nd-label'>Rows per scenario</div>", unsafe_allow_html=True)
by_cond = q(f"SELECT condition AS scenario, COUNT(*) AS rows FROM {DB} GROUP BY condition ORDER BY condition")
style.table(by_cond)

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("<div class='nd-label'>By variable</div>", unsafe_allow_html=True)
    by_var = q(f"""
        SELECT variable, COUNT(*) AS rows,
               COUNT(DISTINCT solute) AS solutes, COUNT(DISTINCT compartment) AS compartments
        FROM {DB} GROUP BY variable ORDER BY rows DESC
    """)
    style.table(by_var)
with c2:
    st.markdown("<div class='nd-label'>By segment</div>", unsafe_allow_html=True)
    by_seg = q(f"""
        SELECT segment, COUNT(DISTINCT nephron) AS nephron_types, COUNT(*) AS rows
        FROM {DB} GROUP BY segment ORDER BY rows DESC
    """)
    style.table(by_seg)

st.markdown("<div class='nd-label'>By nephron type</div>", unsafe_allow_html=True)
by_neph = q(f"SELECT nephron, COUNT(*) AS rows FROM {DB} GROUP BY nephron ORDER BY rows DESC")
style.table(by_neph)

# ------------------------------------------------------------
#  Convergence
# ------------------------------------------------------------
st.markdown("### Which scenarios converged")
st.caption("The model's Newton solver can fail in the collecting duct (IMCD, merged nephron). A NaN, or "
           "a negative osmolality in the lumen — a sum of solutes cannot be negative — marks a real "
           "convergence failure. Statements about the distal nephron or the urine should be taken "
           "only from the scenarios marked clean.")
integ = q(f"""
    SELECT condition AS scenario,
        SUM(CASE WHEN value IS NULL OR isnan(value) THEN 1 ELSE 0 END) AS nan,
        SUM(CASE WHEN variable='osmolality' AND compartment='Lumen' AND value < -1 THEN 1 ELSE 0 END) AS negative_osm
    FROM {DB} GROUP BY condition ORDER BY condition
""")
# One small nephron per scenario: the stretch that did not converge is struck out.
broken = integrity_map()
st.markdown(
    "<div class='nd-six'>" + "".join(
        "<figure>" + nephron_figure.locator(None, width=44, names=segment_names(),
                                            struck=broken.get(code, ()))
        + f"<figcaption>{code}"
        + (f"<i>{', '.join(sorted(broken[code]))} not converged</i>" if broken.get(code) else "<br>complete")
        + "</figcaption></figure>"
        for code in integ["scenario"]) + "</div>",
    unsafe_allow_html=True,
)
integ["status"] = integ.apply(
    lambda r: "clean" if (r["nan"] == 0 and r["negative_osm"] == 0)
    else "collecting duct did not converge (proximal segments fine)", axis=1)
style.table(integ)

# ------------------------------------------------------------
#  Things to know
# ------------------------------------------------------------
st.markdown("### Things to know about this dataset")

st.markdown("""
<dl class="nd-issues">
  <dt><span class="nd-label done">Resolved</span>Interleaved multi-membrane flux files</dt>
  <dd>In CNT, CCD and OMCD some transporters (AE1 on 2 membranes, HATPase and HKATPase on 3, NHE1 on 2)
  are written by the model into a single file, interleaved. The loader separates them by stride, puts
  each profile on the right position axis, and names the membrane in the <code>membrane</code> column
  (for example Lumen-ICA, the apical membrane of the type-A intercalated cell). 246 files across the
  6 scenarios.</dd>

  <dt><span class="nd-label">Note</span>Some transporter profiles share a key</dt>
  <dd>Na/K-ATPase, GLUT1/2 and KCC4 sit on several basolateral membranes (2 to 6, depending on the
  segment). The model writes one file per membrane; the current table stores those profiles under one
  key, without the membrane. The app sums them, which gives the transporter's total basolateral flux,
  instead of plotting them as one line. The loader now keeps the membrane, so a rebuilt table will
  carry it. The values themselves are not affected.</dd>

  <dt><span class="nd-label">Limit</span>Six scenarios out of ten</dt>
  <dd>Four scenarios (F_diab_severe, F_ACE, F_obese, F_UNX) failed to converge in the Newton solver
  (an overflow in <code>np.exp</code>). This is a limit of the model, not an error of this project.</dd>

  <dt><span class="nd-label">Units</span>What is confirmed and what is not</dt>
  <dd>Transporter fluxes (<code>variable='flux'</code>) are labelled "pmol/min" in the table, but the
  model writes them in its internal units. They are flux densities: 1 model unit = 600 pmol/(min·cm²) of
  luminal surface. Diameter and length are in cm. Both are confirmed by mass balance: integrating apical
  plus paracellular flux over the luminal surface reproduces the drop in luminal flow (see the
  Transporters page). The unit of pressure has not been confirmed from the source.</dd>

  <dt><span class="nd-label">Input</span>The interstitial gradient is prescribed</dt>
  <dd>The composition of the interstitial fluid is given to the model: specified at the cortex, the
  outer–inner medullary boundary and the papillary tip, linear in between (Layton &amp; Layton 2019,
  Table 2), and identical in all six scenarios here. The ~734 mOsm at the papilla is therefore not a
  result and not a failed prediction; ~1200 mOsm is reported for maximal antidiuresis. The model has no
  vasculature and does not simulate how the gradient forms.</dd>
</dl>
""", unsafe_allow_html=True)
