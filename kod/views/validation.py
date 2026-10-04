"""validation.py — Automatic physiology checks.

Two kinds of checks are kept apart:
- OUTPUT checks test what the model computes (lumen composition, fluxes). Only these count
  towards the score.
- INPUT checks look at quantities the model is GIVEN — the interstitial composition
  (Layton & Layton 2019: specified, not computed) and the proximal-tubule inlet condition.
  They confirm the data is as specified; they are not evidence that the model reproduces
  physiology, so they are shown separately and never scored.
"""
import streamlit as st

import nav
import transport
from ui_kit import DB, scalar, SCENARIO_LABEL, segment_broken

scenario = nav.get("scenario")

st.markdown("## Automatic Physiology Validation")
st.caption(f"Active scenario: **{SCENARIO_LABEL.get(scenario, scenario)}**. "
           f"Some checks may give a different result in a disease/drug scenario — "
           f"that is **information**, not an error.")

outputs = []   # (name, value, target, ok)  — what the model computes; ok=None -> not available
inputs = []    # (name, value, expected, ok) — what the model is given


def value(sql):
    return scalar(sql, scenario)


# ------------------------------------------------------------
#  Model outputs
# ------------------------------------------------------------
# PT isosmotic
a = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='PT' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='PT' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=1")
if a and b:
    outputs.append(("PT isosmotic", f"{a:.1f} → {b:.1f}", "|diff| < 10", abs(b-a) < 10))

# mTAL dilution
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=1")
if a and b:
    outputs.append(("mTAL dilution (lumen Na)", f"{a:.0f} → {b:.0f} mM", "outlet < inlet", b < a))

# NKCC2 stoichiometry
a = value(f"SELECT value FROM {DB} WHERE variable='flux' AND transporter='NKCC2A' AND solute='Na' "
          f"AND segment='mTAL' AND nephron='sup' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='flux' AND transporter='NKCC2A' AND solute='Cl' "
          f"AND segment='mTAL' AND nephron='sup' AND position=0")
if a and b and a != 0:
    r = b / a
    outputs.append(("NKCC2A stoichiometry", f"Cl/Na = {r:.2f}", "Target: 1.8–2.2", 1.8 < r < 2.2))

# Urine hyperosmolar — only meaningful where the collecting duct converged. A non-converged
# IMCD holds NaN or physically impossible values; reporting those as a failed physiology check
# would be misleading, so the check is marked not available instead.
if segment_broken(scenario, "IMCD"):
    outputs.append(("Urine hyperosmolar", "not available",
                    "IMCD did not converge in this scenario (see Data Integrity)", None))
else:
    v = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='IMCD' "
              f"AND compartment='Lumen' AND nephron='merged' AND position=1")
    if v:
        outputs.append(("Urine hyperosmolar", f"{v:.0f} mOsm", "> plasma (300)", v > 300))

# Urea recycling
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='urea' AND segment='LDL' "
          f"AND compartment='Lumen' AND nephron='jux5' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='urea' AND segment='LDL' "
          f"AND compartment='Lumen' AND nephron='jux5' AND position=1")
if a and b:
    outputs.append(("Urea recycling (LDL jux5)", f"{a:.1f} → {b:.1f} (×{b/a:.1f})",
                    "Target: at least ×2", b > 2*a))

# NH3 lumen = Bath equilibrium
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='NH3' AND segment='LDL' "
          f"AND compartment='Lumen' AND nephron='jux5' AND position=1")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='NH3' AND segment='LDL' "
          f"AND compartment='Bath' AND nephron='jux5' AND position=1")
if a and b:
    outputs.append(("NH3 lumen ≈ Bath (LDL outlet)", f"L={a:.3f} · B={b:.3f}",
                    "diff < 15%", abs(a-b)/max(a, b) < 0.15))

# Segment chaining
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=1")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='cTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=0")
if a and b and a != 0:
    outputs.append(("Segment chaining (mTAL → cTAL)", f"{a:.1f} = {b:.1f}",
                    "diff < 2%", abs(a-b)/a < 0.02))

# Fluxes consistent with flows: the Na+ leaving the lumen across the epithelium (apical +
# paracellular flux, integrated over the luminal surface) must equal the drop in luminal flow.
balance = transport.mass_balance(scenario, "PT", "sup", "Na")
if balance:
    from_fluxes, flow_drop = balance
    if flow_drop:
        outputs.append(("Na⁺ mass balance (PT): fluxes vs flow",
                        f"{from_fluxes:,.0f} vs {flow_drop:,.0f} pmol/min",
                        "diff < 1%", abs(from_fluxes - flow_drop) / abs(flow_drop) < 0.01))

# ------------------------------------------------------------
#  Prescribed inputs (boundary conditions)
# ------------------------------------------------------------
# PT inlet: the composition of the fluid entering the tubule is an inlet condition
v = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='PT' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=0")
if v:
    inputs.append(("Glomerular filtrate ≈ plasma (PT inlet)", f"{v:.1f} mOsm",
                   "Expected: 290–310", 290 <= v <= 310))

# Corticomedullary gradient of the interstitium
a = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='CCD' "
          f"AND compartment='Bath' AND nephron='merged' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='IMCD' "
          f"AND compartment='Bath' AND nephron='merged' AND position=1")
if a and b:
    inputs.append(("Corticomedullary gradient (interstitium)", f"{a:.0f} → {b:.0f} mOsm (×{b/a:.2f})",
                   "Expected: at least ×2", b > 2*a))

# ------------------------------------------------------------
#  Score (outputs only)
# ------------------------------------------------------------
passed = sum(1 for *_, ok in outputs if ok is True)
total = sum(1 for *_, ok in outputs if ok is not None)
unavailable = len(outputs) - total
m1, m2, m3 = st.columns(3)
m1.metric("Output checks passed", f"{passed} / {total}")
m2.metric("Success", f"{passed/total*100:.0f} %" if total else "—")
m3.metric("Scenario", scenario)
if unavailable:
    st.caption(f"{unavailable} check(s) not available for this scenario and left out of the score.")


def card(name, shown, target, ok, scored=True):
    if ok is None:   # depends on a segment that did not converge
        icon, color, scored = "n/a", "#9ca3af", False
    elif scored:
        icon, color = ("✓", "#059669") if ok else ("✗", "#dc2626")
    else:   # inputs are reported, not judged as model performance
        icon, color = ("as specified" if ok else "check", "#6b7280")
    st.markdown(f"""
    <div style="border:1px solid #e5e7eb;border-left:4px solid {color};
                padding:10px 14px;border-radius:6px;margin-bottom:10px;background:white;">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div style="font-weight:600;color:#111827;">{name}</div>
        <div style="color:{color};font-weight:700;font-size:{'1.1rem' if scored else '0.78rem'};">{icon}</div>
      </div>
      <div style="margin-top:4px;color:#374151;font-family:ui-monospace,monospace;">{shown}</div>
      <div style="margin-top:2px;color:#6b7280;font-size:0.8rem;">{target}</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("---")
st.markdown("#### Model outputs")
st.caption("Quantities the model computes. These are the checks that count.")
cols = st.columns(2)
for i, (name, shown, target, ok) in enumerate(outputs):
    with cols[i % 2]:
        card(name, shown, target, ok)

st.markdown("#### Prescribed inputs")
st.caption(
    "Quantities the model is **given**, not ones it computes. The interstitial fluid composition "
    "is specified at the cortex, the outer–inner medullary boundary and the papillary tip and "
    "interpolated linearly in between (Layton & Layton 2019, Methods and Table 2); in this "
    "dataset it is identical in all six scenarios. The composition of the fluid entering the "
    "proximal tubule is likewise an inlet condition. Shown to confirm the data is as specified — "
    "**not counted**, because they say nothing about how well the model reproduces physiology."
)
cols = st.columns(2)
for i, (name, shown, target, ok) in enumerate(inputs):
    with cols[i % 2]:
        card(name, shown, target, ok, scored=False)
