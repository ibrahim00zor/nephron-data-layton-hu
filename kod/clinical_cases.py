"""
clinical_cases.py — Structural description of the clinical cases.

This is NOT clinical content. It only records, for each case shown on the Clinical page,
which model scenario it looks at, which scenario it is compared against, and which
segment/solute its model-data charts focus on. The same table lets the model pages link
back to the case that uses the active scenario, so the two worlds stay connected.
"""

CASES = {
    "SGLT2": {
        "number": 1,
        "button": "SGLT2 Inhibition",
        "title": "Case 1: SGLT2 Inhibition and TGF Restoration",
        "scenario": "F_SGLT2",
        "reference": "F_normal",
        "label": "SGLT2 Inhibition",
        "color": "#7a2f5a",
        "focus": {"segment": "cTAL", "solute": "Na"},
    },
    "Hyperfiltration": {
        "number": 2,
        "button": "Diabetic Hyperfiltration",
        "title": "Case 2: Diabetic Hyperfiltration",
        "scenario": "F_diab_mod",
        "reference": "F_normal",
        "label": "Diabetes",
        "color": "#c0652a",
        "focus": {"segment": "PT", "solute": "Na"},
    },
    "Hypertension": {
        "number": 3,
        "button": "Hypertension",
        "title": "Case 3: Hypertension",
        "scenario": "F_HT",
        "reference": "F_normal",
        "label": "Hypertension",
        "color": "#a8861f",
        "focus": {"segment": "mTAL", "solute": "Na"},
    },
}

REFERENCE_COLOR = "#4a463e"   # the baseline is drawn in a neutral ink

# scenario code -> case key (which case, if any, is built on a given scenario)
CASE_BY_SCENARIO = {case["scenario"]: key for key, case in CASES.items()}
