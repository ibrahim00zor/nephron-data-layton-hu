"""validation.py — Automatic physiology checks."""
import streamlit as st

import nav
from ui_kit import DB, scalar, SCENARIO_LABEL

scenario = nav.get("scenario")

st.markdown("## Automatic Physiology Validation")
st.caption(f"Active scenario: **{SCENARIO_LABEL.get(scenario, scenario)}**. "
           f"Some checks may give a different result in a disease/drug scenario — "
           f"that is **information**, not an error.")

checks = []
add = checks.append

# 1. Filtrate ~ plasma
v = scalar(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='PT' "
           f"AND compartment='Lumen' AND nephron='sup' AND position=0", scenario)
if v: add(("Glomerular filtrate ≈ plasma", f"{v:.1f} mOsm", "Target: 290–310", 290 <= v <= 310))

# 2. PT isosmotic
a = scalar(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='PT' "
           f"AND compartment='Lumen' AND nephron='sup' AND position=0", scenario)
b = scalar(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='PT' "
           f"AND compartment='Lumen' AND nephron='sup' AND position=1", scenario)
if a and b: add(("PT isosmotic", f"{a:.1f} → {b:.1f}", "|diff| < 10", abs(b-a) < 10))

# 3. mTAL dilution
a = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
           f"AND compartment='Lumen' AND nephron='sup' AND position=0", scenario)
b = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
           f"AND compartment='Lumen' AND nephron='sup' AND position=1", scenario)
if a and b: add(("mTAL dilution (lumen Na)", f"{a:.0f} → {b:.0f} mM", "outlet < inlet", b < a))

# 4. NKCC2 stoichiometry
a = scalar(f"SELECT value FROM {DB} WHERE variable='flux' AND transporter='NKCC2A' AND solute='Na' "
           f"AND segment='mTAL' AND nephron='sup' AND position=0", scenario)
b = scalar(f"SELECT value FROM {DB} WHERE variable='flux' AND transporter='NKCC2A' AND solute='Cl' "
           f"AND segment='mTAL' AND nephron='sup' AND position=0", scenario)
if a and b and a != 0:
    r = b / a
    add(("NKCC2A stoichiometry", f"Cl/Na = {r:.2f}", "Target: 1.8–2.2", 1.8 < r < 2.2))

# 5. Corticomedullary gradient
a = scalar(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='CCD' "
           f"AND compartment='Bath' AND nephron='merged' AND position=0", scenario)
b = scalar(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='IMCD' "
           f"AND compartment='Bath' AND nephron='merged' AND position=1", scenario)
if a and b:
    add(("Corticomedullary gradient (Bath)", f"{a:.0f} → {b:.0f} (×{b/a:.2f})",
         "Target: at least ×2", b > 2*a))

# 6. Urine hyperosmolar
v = scalar(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='IMCD' "
           f"AND compartment='Lumen' AND nephron='merged' AND position=1", scenario)
if v: add(("Urine hyperosmolar", f"{v:.0f} mOsm", "> plasma (300)", v > 300))

# 7. Urea recycling
a = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='urea' AND segment='LDL' "
           f"AND compartment='Lumen' AND nephron='jux5' AND position=0", scenario)
b = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='urea' AND segment='LDL' "
           f"AND compartment='Lumen' AND nephron='jux5' AND position=1", scenario)
if a and b: add(("Urea recycling (LDL jux5)", f"{a:.1f} → {b:.1f} (×{b/a:.1f})",
                 "Target: at least ×2", b > 2*a))

# 8. NH3 lumen=Bath equilibrium
a = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='NH3' AND segment='LDL' "
           f"AND compartment='Lumen' AND nephron='jux5' AND position=1", scenario)
b = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='NH3' AND segment='LDL' "
           f"AND compartment='Bath' AND nephron='jux5' AND position=1", scenario)
if a and b: add(("NH3 lumen ≈ Bath (LDL outlet)", f"L={a:.3f} · B={b:.3f}",
                 "diff < 15%", abs(a-b)/max(a,b) < 0.15))

# 9. Segment chaining
a = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
           f"AND compartment='Lumen' AND nephron='sup' AND position=1", scenario)
b = scalar(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='cTAL' "
           f"AND compartment='Lumen' AND nephron='sup' AND position=0", scenario)
if a and b and a != 0:
    add(("Segment chaining (mTAL → cTAL)", f"{a:.1f} = {b:.1f}",
         "diff < 2%", abs(a-b)/a < 0.02))

# Top metrics
passed = sum(1 for *_, ok in checks if ok)
total = len(checks)
m1, m2, m3 = st.columns(3)
m1.metric("Passed", f"{passed} / {total}")
m2.metric("Success", f"{passed/total*100:.0f} %" if total else "—")
m3.metric("Scenario", scenario)

st.markdown("---")

# 2-column card grid
cols = st.columns(2)
for i, (name, value, target, ok) in enumerate(checks):
    with cols[i % 2]:
        icon = "✓" if ok else "✗"
        color = "#059669" if ok else "#dc2626"
        st.markdown(f"""
        <div style="border:1px solid #e5e7eb;border-left:4px solid {color};
                    padding:10px 14px;border-radius:6px;margin-bottom:10px;background:white;">
          <div style="display:flex;justify-content:space-between;align-items:start;">
            <div style="font-weight:600;color:#111827;">{name}</div>
            <div style="color:{color};font-weight:700;font-size:1.1rem;">{icon}</div>
          </div>
          <div style="margin-top:4px;color:#374151;font-family:ui-monospace,monospace;">{value}</div>
          <div style="margin-top:2px;color:#6b7280;font-size:0.8rem;">{target}</div>
        </div>
        """, unsafe_allow_html=True)
