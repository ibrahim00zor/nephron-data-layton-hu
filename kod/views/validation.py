"""validation.py — Automatic physiology checks.

Two kinds of checks are kept apart:
- OUTPUT checks test what the model computes (lumen composition, fluxes). Only these count
  towards the score.
- INPUT checks look at quantities the model is GIVEN — the interstitial composition
  (Layton & Layton 2019: specified, not computed) and the proximal-tubule inlet condition.
  They confirm the data is as specified; they are not evidence that the model reproduces
  physiology, so they are shown separately and never scored.
"""
import html

import streamlit as st

import nav
import style
import transport
from ui_kit import DB, scalar, selection, SCENARIO_LABEL, segment_broken

scenario = selection(whole=False)["scenario"]      # this page reads one scenario and nothing else

st.markdown("## Validation")
st.caption(f"Does the model's output behave as physiology expects? Checked for "
           f"{SCENARIO_LABEL.get(scenario, scenario)}. In a disease or drug scenario a check may "
           f"come out differently; that is information about the scenario, not an error.")

outputs = []   # (name, value, target, ok, how) — what the model computes; ok=None -> not available
inputs = []    # (name, value, expected, ok, how) — what the model is given
# `how` says, in words, exactly what the check reads from the dataset. It is shown when the
# row is opened, so that a verdict can be traced without reading this file.


def see(page, label, **selection):
    """A link that opens the page where the checked quantity can be seen."""
    return (f" <a class='nd-go' href='{html.escape(nav.href(page, **selection), quote=True)}' "
            f"target='_self'>{label} →</a>")


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
    outputs.append(("PT isosmotic", f"{a:.1f} → {b:.1f}", "|diff| < 10", abs(b-a) < 10,
                    "Lumen osmolality of the superficial nephron where the proximal tubule begins "
                    "(position 0) and where it ends (position 1). Passes when the two differ by "
                    "less than 10 mOsm."))

# mTAL dilution
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=1")
if a and b:
    outputs.append(("mTAL dilution (lumen Na)", f"{a:.0f} → {b:.0f} mM", "outlet < inlet", b < a,
                    "Lumen Na⁺ concentration of the superficial nephron at the inlet and at the "
                    "outlet of the mTAL. Passes when the outlet is lower."
                    + see("segment", "See the profile", solute="Na", segment="mTAL", nephron="sup",
                          compartment="Lumen")))

# NKCC2 stoichiometry
a = value(f"SELECT value FROM {DB} WHERE variable='flux' AND transporter='NKCC2A' AND solute='Na' "
          f"AND segment='mTAL' AND nephron='sup' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='flux' AND transporter='NKCC2A' AND solute='Cl' "
          f"AND segment='mTAL' AND nephron='sup' AND position=0")
if a and b and a != 0:
    r = b / a
    outputs.append(("NKCC2A stoichiometry", f"Cl/Na = {r:.2f}", "Target: 1.8–2.2", 1.8 < r < 2.2,
                    "Cl⁻ flux divided by Na⁺ flux through NKCC2A at the inlet of the mTAL "
                    "(superficial nephron). Passes when the ratio lies between 1.8 and 2.2."
                    + see("transporters", "See the fluxes", solute="Na", segment="mTAL", nephron="sup")))

# Urine hyperosmolar — only meaningful where the collecting duct converged. A non-converged
# IMCD holds NaN or physically impossible values; reporting those as a failed physiology check
# would be misleading, so the check is marked not available instead.
if segment_broken(scenario, "IMCD"):
    outputs.append(("Urine hyperosmolar", "not available",
                    "IMCD did not converge in this scenario (see Data Integrity)", None,
                    "Would read the lumen osmolality where the IMCD ends. In this scenario the "
                    "collecting duct did not converge, so there is no trustworthy value to judge."))
else:
    v = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='IMCD' "
              f"AND compartment='Lumen' AND nephron='merged' AND position=1")
    if v:
        outputs.append(("Urine hyperosmolar", f"{v:.0f} mOsm", "> plasma (300)", v > 300,
                        "Lumen osmolality where the IMCD ends (the collecting duct shared by all "
                        "nephrons). Passes when it is above 300 mOsm, the value taken here for plasma."))

# Urea recycling
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='urea' AND segment='LDL' "
          f"AND compartment='Lumen' AND nephron='jux5' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='urea' AND segment='LDL' "
          f"AND compartment='Lumen' AND nephron='jux5' AND position=1")
if a and b:
    outputs.append(("Urea recycling (LDL jux5)", f"{a:.1f} → {b:.1f} (×{b/a:.1f})",
                    "Target: at least ×2", b > 2*a,
                    "Lumen urea concentration at the inlet and at the outlet of the long descending "
                    "limb of the nephron with the longest loop (jux5). Passes when it at least doubles."
                    + see("segment", "See the profile", solute="urea", segment="LDL", nephron="jux5",
                          compartment="Lumen")))

# NH3 lumen = Bath equilibrium
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='NH3' AND segment='LDL' "
          f"AND compartment='Lumen' AND nephron='jux5' AND position=1")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='NH3' AND segment='LDL' "
          f"AND compartment='Bath' AND nephron='jux5' AND position=1")
if a and b:
    outputs.append(("NH3 lumen ≈ Bath (LDL outlet)", f"L={a:.3f} · B={b:.3f}",
                    "diff < 15%", abs(a-b)/max(a, b) < 0.15,
                    "NH₃ concentration in the lumen (L) and in the interstitium (B) where the long "
                    "descending limb of jux5 ends. Passes when they differ by less than 15% of the larger."))

# Segment chaining
a = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='mTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=1")
b = value(f"SELECT value FROM {DB} WHERE variable='con' AND solute='Na' AND segment='cTAL' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=0")
if a and b and a != 0:
    outputs.append(("Segment chaining (mTAL → cTAL)", f"{a:.1f} = {b:.1f}",
                    "diff < 2%", abs(a-b)/a < 0.02,
                    "Lumen Na⁺ where the mTAL ends and where the cTAL begins (superficial nephron): "
                    "the fluid that leaves one segment is the fluid that enters the next. Passes when "
                    "the two differ by less than 2%."
                    + see("nephron", "See the whole nephron", solute="Na", nephron="sup",
                          compartment="Lumen")))

# Fluxes consistent with flows: the Na+ leaving the lumen across the epithelium (apical +
# paracellular flux, integrated over the luminal surface) must equal the drop in luminal flow.
balance = transport.mass_balance(scenario, "PT", "sup", "Na")
if balance:
    from_fluxes, flow_drop = balance
    if flow_drop:
        outputs.append(("Na⁺ mass balance (PT): fluxes vs flow",
                        f"{from_fluxes:,.0f} vs {flow_drop:,.0f} pmol/min",
                        "diff < 1%", abs(from_fluxes - flow_drop) / abs(flow_drop) < 0.01,
                        "Apical plus paracellular Na⁺ flux, integrated over the luminal surface of "
                        "the proximal tubule, against the drop in luminal Na⁺ flow between its inlet "
                        "and its outlet (superficial nephron). Passes when they differ by less than 1%."
                        + see("transporters", "See the fluxes", solute="Na", segment="PT", nephron="sup")))

# ------------------------------------------------------------
#  Prescribed inputs (boundary conditions)
# ------------------------------------------------------------
# PT inlet: the composition of the fluid entering the tubule is an inlet condition
v = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='PT' "
          f"AND compartment='Lumen' AND nephron='sup' AND position=0")
if v:
    inputs.append(("Glomerular filtrate ≈ plasma (PT inlet)", f"{v:.1f} mOsm",
                   "Expected: 290–310", 290 <= v <= 310,
                   "Lumen osmolality where the proximal tubule begins (superficial nephron). "
                   "An inlet condition of the model."))

# Corticomedullary gradient of the interstitium
a = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='CCD' "
          f"AND compartment='Bath' AND nephron='merged' AND position=0")
b = value(f"SELECT value FROM {DB} WHERE variable='osmolality' AND segment='IMCD' "
          f"AND compartment='Bath' AND nephron='merged' AND position=1")
if a and b:
    inputs.append(("Corticomedullary gradient (interstitium)", f"{a:.0f} → {b:.0f} mOsm (×{b/a:.2f})",
                   "Expected: at least ×2", b > 2*a,
                   "Interstitial osmolality where the CCD begins and where the IMCD ends. Prescribed."))

# ------------------------------------------------------------
#  Score (outputs only)
# ------------------------------------------------------------
passed = sum(1 for check in outputs if check[3] is True)
total = sum(1 for check in outputs if check[3] is not None)
unavailable = len(outputs) - total
m1, m2, m3 = st.columns(3)
m1.metric("Output checks passed", f"{passed} / {total}")
m2.metric("Success", f"{passed/total*100:.0f} %" if total else "—")
if unavailable:
    st.caption(f"{unavailable} check(s) not available for this scenario and left out of the score.")


def row(name, shown, target, ok, how=None, scored=True):
    """One line of the ledger: what was checked, what was found, what was expected, the verdict
    (and, when the row is opened, how it was computed)."""
    if ok is None:          # depends on a segment that did not converge
        return (name, shown, target, "n/a", "quiet", how)
    if not scored:          # inputs are reported, not judged as model performance
        return (name, shown, target, "as specified" if ok else "check", "quiet", how)
    return (name, shown, target, "pass" if ok else "differs", "pass" if ok else "fail", how)


st.markdown("### Model outputs")
st.caption("Quantities the model computes. These are the checks that count. "
           "Open a row to read how it is computed.")
style.ledger([row(*check) for check in outputs])

st.markdown("### Prescribed inputs")
st.caption(
    "Quantities the model is given, not ones it computes. The interstitial fluid composition "
    "is specified at the cortex, the outer–inner medullary boundary and the papillary tip and "
    "interpolated linearly in between (Layton & Layton 2019, Methods and Table 2); in this "
    "dataset it is identical in all six scenarios. The composition of the fluid entering the "
    "proximal tubule is likewise an inlet condition. They are shown to confirm the data is as "
    "specified and are not counted, because they say nothing about how well the model reproduces "
    "physiology."
)
style.ledger([row(*check, scored=False) for check in inputs])
