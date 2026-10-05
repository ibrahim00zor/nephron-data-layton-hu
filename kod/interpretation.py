"""
interpretation.py — Automatic physiological interpretation of a concentration profile.

Usage:
    from interpretation import interpret
    interpret(con_in, con_out, vol_in, vol_out, solute="Na")

Logic:
    concentration = mass / volume
    Splits the concentration change into two components:
      - Mass change (did solute actually enter/leave)
      - Volume change (was water reabsorbed/added)
    This automatically prevents intuition errors such as the LDL Na fallacy.
"""

def interpret(con_in, con_out, vol_in, vol_out, solute="solute"):
    """
    From a segment's inlet/outlet concentration + volume data, returns a sentence
    explaining the physiological reasons for the concentration change.
    """
    if con_in == 0 or vol_in == 0:
        return "No interpretation (inlet values are zero)."

    mass_in = con_in * vol_in
    mass_out = con_out * vol_out

    dk_pct = (mass_out - mass_in) / mass_in * 100   # mass %
    dv_pct = (vol_out - vol_in) / vol_in * 100      # volume %
    dc_pct = (con_out - con_in) / con_in * 100      # concentration %

    thr = 3.0   # below 3% we treat as "unchanged"

    # Nearly constant concentration
    if abs(dc_pct) < 2:
        return (f"**{solute} concentration is nearly constant** ({dc_pct:+.1f}%). "
                f"Mass {dk_pct:+.1f}%, volume {dv_pct:+.1f}% — the changes balance each "
                f"other (e.g. isosmotic reabsorption).")

    # Concentration INCREASED
    if dc_pct > 0:
        if abs(dk_pct) < thr and dv_pct < -thr:
            return (f"**{solute} concentration rose {dc_pct:+.1f}%.** "
                    f"Water was reabsorbed (volume {dv_pct:+.1f}%), {solute} mass constant "
                    f"({dk_pct:+.1f}%). _Concentration by water loss._")
        if dk_pct > thr and abs(dv_pct) < thr:
            return (f"**{solute} concentration rose {dc_pct:+.1f}%.** "
                    f"{solute} was secreted into the lumen (mass {dk_pct:+.1f}%), volume "
                    f"constant ({dv_pct:+.1f}%). _Active secretion._")
        if dk_pct > thr and dv_pct > thr:
            return (f"**{solute} concentration rose {dc_pct:+.1f}%.** "
                    f"Both {solute} entered ({dk_pct:+.1f}%) and volume rose ({dv_pct:+.1f}%) — "
                    f"net concentration. _Like the urea–water trap in the LDL._")
        if dk_pct < -thr and dv_pct < -thr:
            return (f"**{solute} concentration rose {dc_pct:+.1f}%** (but rarely). "
                    f"Both {solute} ({dk_pct:+.1f}%) and water ({dv_pct:+.1f}%) left; "
                    f"water left faster, so the remainder is concentrated.")

    # Concentration DECREASED
    else:
        if abs(dk_pct) < thr and dv_pct > thr:
            return (f"**{solute} concentration fell {dc_pct:+.1f}%.** "
                    f"Water entered the lumen (volume {dv_pct:+.1f}%), {solute} mass constant "
                    f"({dk_pct:+.1f}%). _Net dilution._")
        if dk_pct < -thr and abs(dv_pct) < thr:
            return (f"**{solute} concentration fell {dc_pct:+.1f}%.** "
                    f"{solute} was reabsorbed (mass {dk_pct:+.1f}%), volume constant "
                    f"({dv_pct:+.1f}%). _Classic reabsorption (e.g. mTAL Na)._")
        if dk_pct < -thr and dv_pct > thr:
            return (f"**{solute} concentration fell {dc_pct:+.1f}%.** "
                    f"{solute} left ({dk_pct:+.1f}%) **AND** water entered the lumen "
                    f"({dv_pct:+.1f}%). _Dual effect — modern inner-medulla behavior of the "
                    f"LDL urea–water trap type._")
        if dk_pct < -thr and dv_pct < -thr:
            return (f"**{solute} concentration fell {dc_pct:+.1f}%.** "
                    f"Both {solute} ({dk_pct:+.1f}%) and water ({dv_pct:+.1f}%) were reabsorbed; "
                    f"{solute} loss exceeds water loss.")

    # General fallback
    return (f"**{solute} concentration changed {dc_pct:+.1f}%.** "
            f"Mass {dk_pct:+.1f}%, volume {dv_pct:+.1f}%. "
            f"(Complex case — needs detailed inspection.)")
