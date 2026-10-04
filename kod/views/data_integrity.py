"""data_integrity.py — Database inventory + known limits."""
import os
import streamlit as st

from ui_kit import q, DB, PARQUET

st.markdown("## Data Integrity Panel")
st.caption(f"Source: `{os.path.basename(PARQUET)}` · "
           f"All scenarios are kept combined in a single tidy Parquet.")

# Scenario distribution
st.markdown("**Scenario distribution**")
by_cond = q(f"SELECT condition AS scenario, COUNT(*) AS rows FROM {DB} GROUP BY condition ORDER BY condition")
st.dataframe(by_cond, width='stretch', hide_index=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Variable categories**")
    by_var = q(f"""
        SELECT variable, COUNT(*) AS rows,
               COUNT(DISTINCT solute) AS solutes, COUNT(DISTINCT compartment) AS compartments
        FROM {DB} GROUP BY variable ORDER BY rows DESC
    """)
    st.dataframe(by_var, width='stretch', hide_index=True)
with c2:
    st.markdown("**Segment distribution**")
    by_seg = q(f"""
        SELECT segment, COUNT(DISTINCT nephron) AS nephron_types, COUNT(*) AS rows
        FROM {DB} GROUP BY segment ORDER BY rows DESC
    """)
    st.dataframe(by_seg, width='stretch', hide_index=True)

st.markdown("**Nephron-type distribution**")
by_neph = q(f"SELECT nephron, COUNT(*) AS rows FROM {DB} GROUP BY nephron ORDER BY rows DESC")
st.dataframe(by_neph, width='stretch', hide_index=True)

st.markdown("---")
st.markdown("### Scenario data integrity")
st.caption("The model's Newton solver may fail to converge for the collecting duct "
           "(IMCD merged) in some scenarios. NaN and a negative Lumen osmolality (a solute "
           "total cannot be physically negative) indicate a genuine convergence failure. "
           "Distal/urine claims should be taken only from CLEAN scenarios.")
integ = q(f"""
    SELECT condition AS scenario,
        SUM(CASE WHEN value IS NULL OR isnan(value) THEN 1 ELSE 0 END) AS nan,
        SUM(CASE WHEN variable='osmolality' AND compartment='Lumen' AND value < -1 THEN 1 ELSE 0 END) AS negative_osm
    FROM {DB} GROUP BY condition ORDER BY condition
""")
integ["status"] = integ.apply(
    lambda r: "CLEAN" if (r["nan"] == 0 and r["negative_osm"] == 0)
    else "Collecting duct broken (proximal OK)", axis=1)
st.dataframe(integ, width='stretch', hide_index=True)

st.markdown("---")
st.markdown("### Known open issues")

st.markdown("""
<div style="border:1px solid #bbf7d0;background:#f0fdf4;padding:12px 14px;border-radius:6px;margin-bottom:10px;">
  <b style="color:#166534;">Resolved ✓ — Multi-membrane flux files split per membrane</b><br>
  <span style="color:#374151;">In CNT / CCD / OMCD some transporters (AE1 = 2 membranes,
  HATPase / HKATPase = 3 membranes, NHE1 = 2 membranes) are written into a single file,
  interleaved. The loader now separates them by stride, places each profile on the correct
  position axis, and labels it in the <code>membrane</code> column with the anatomic
  compartment pair (e.g. Lumen-ICA = type-A intercalated cell apical). 246 files parsed
  across 6 scenarios.</span>
</div>
<div style="border:1px solid #bfdbfe;background:#eff6ff;padding:12px 14px;border-radius:6px;margin-bottom:10px;">
  <b style="color:#1e40af;">Scenario library 6/10 successful</b><br>
  <span style="color:#374151;">4 scenarios (F_diab_severe, F_ACE, F_obese, F_UNX) gave a numerical
  convergence failure in the Newton solver (np.exp overflow). This is a <b>known limit</b> of
  the model, not a project error. The model's solver could be softened in the future.</span>
</div>
<div style="border:1px solid #bfdbfe;background:#eff6ff;padding:12px 14px;border-radius:6px;margin-bottom:10px;">
  <b style="color:#1e40af;">Units: what is confirmed and what is not</b><br>
  <span style="color:#374151;"><b>Transporter fluxes</b> (<code>variable='flux'</code>) are labelled
  "pmol/min" in the dataset, but the model writes them in its internal units. They are flux densities:
  1 model unit = 600 pmol/(min·cm²) of luminal surface. <b>Diameter and length</b> are in cm. Both
  are confirmed by mass balance — integrating apical + paracellular flux over the luminal surface
  reproduces the drop in luminal flow (see the Transporters page). The unit of <b>pressure</b> has
  not been confirmed from the source.</span>
</div>
<div style="border:1px solid #bfdbfe;background:#eff6ff;padding:12px 14px;border-radius:6px;">
  <b style="color:#1e40af;">The interstitial gradient is prescribed (~734 mOsm at the papilla)</b><br>
  <span style="color:#374151;">Interstitial fluid composition is a model <b>input</b>: specified at
  the cortex, the outer–inner medullary boundary and the papillary tip, linear in between
  (Layton &amp; Layton 2019, Table 2), and identical in all six scenarios here. The ~734 mOsm is
  therefore not a result and not a failed prediction; ~1200 mOsm is reported for maximal
  antidiuresis. The model has no vasculature and does not simulate how the gradient forms.</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Data structure + citations: see the README.")
