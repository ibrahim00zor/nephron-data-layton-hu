"""
education.py — Content source for the educational layer.

HOW TO EDIT:
1. In the SEGMENT, TRANSPORTER, and SOLUTE dictionaries, fill the "summary" field for
   each entry in your own words (paraphrase + cite model — not a verbatim copy).
2. In "source_page", write the relevant page number in Türkmen 2024.
3. Empty "summary" fields show up in Streamlit as "not written yet".

CITATION DISCIPLINE:
- Do NOT quote verbatim (the book's copyright is restricted).
- Learn the material and summarize it in your own words, then append a "Türkmen 2024, p. X" note.
- Can be enriched with PubMed papers later.
"""

# =============================================================
#  CITATIONS — central reference list
# =============================================================
CITATIONS = {
    "turkmen2024": {
        "short": "Türkmen 2024",
        "full":  "Türkmen, K. (2024). İnsan Fizyolojisinin Temel Kuramları – "
                 "Boşaltım, Dişi-Erkek Üreme ve Gebelik Fizyolojisi. 1st ed. "
                 "Konya: Dizgi Ofset. ISBN: 978-625-99451-0-1.",
        "type":  "book",
    },
    "hu2021": {
        "short": "Hu et al. 2021",
        "full":  "Hu, R., et al. (2021). Sex differences in solute and water handling "
                 "in the human kidney. iScience 24(6):102694.",
        "url":   "https://www.sciencedirect.com/science/article/pii/S2589004221006350",
        "type":  "article",
    },
    "layton2019": {
        "short": "Layton & Layton 2019",
        "full":  "Layton, A.T., Layton, H.E. (2019). A computational model of epithelial "
                 "solute and water transport along a human nephron. PLOS Comp Biol.",
        "type":  "article",
    },
}


# =============================================================
#  SEGMENT CONTENT
#  For each segment: summary (author-written), apical/basolateral
#  transporter list (structural), citation source page.
# =============================================================
SEGMENT = {
    "PT": {
        "full_name": "Proximal Convoluted Tubule",
        "summary": "",  # AUTHOR: learn from Türkmen 2024 and summarize in your own words
        "apical":       ["NHE3", "SGLT1", "SGLT2", "AQP1"],
        "basolateral":  ["NaKATPase", "GLUT2"],
        "source_page": "",  # AUTHOR: relevant page in Türkmen 2024
        "source_key": "turkmen2024",
    },
    "S3": {
        "full_name": "Proximal Straight Tubule (pars recta)",
        "summary": "",
        "apical":       ["NHE3", "SGLT1", "AQP1"],
        "basolateral":  ["NaKATPase", "GLUT1"],
        "source_page": "",
        "source_key": "turkmen2024",
    },
    "SDL": {
        "full_name": "Short Descending Thin Limb",
        "summary": "",
        "apical":       ["AQP1"],  # water-permeable, solute-tight
        "basolateral":  [],
        "source_page": "",
        "source_key": "turkmen2024",
    },
    "LDL": {
        "full_name": "Long Descending Thin Limb (juxtamedullary only)",
        "summary": "",
        "apical":       ["AQP1 (limited)", "urea-permeable", "NH3-permeable"],
        "basolateral":  [],
        "source_page": "",
        "source_key": "turkmen2024",
        "note": "In the modern understanding the classic 'water-permeable only' description "
                "does not hold — it is urea-permeable with a paracellular convective Na leak.",
    },
    "LAL": {
        "full_name": "Long Ascending Thin Limb (juxtamedullary only)",
        "summary": "",
        "apical":       ["passive NaCl reabsorption"],
        "basolateral":  [],
        "source_page": "",
        "source_key": "turkmen2024",
    },
    "mTAL": {
        "full_name": "Medullary Thick Ascending Limb",
        "summary": "",
        "apical":       ["NKCC2", "ROMK", "NHE3"],
        "basolateral":  ["NaKATPase", "ClC-Kb", "KCC4"],
        "source_page": "",
        "source_key": "turkmen2024",
        "note": "Diluting segment — water-impermeable, reabsorbs NaCl via NKCC2.",
    },
    "cTAL": {
        "full_name": "Cortical Thick Ascending Limb",
        "summary": "",
        "apical":       ["NKCC2", "ROMK"],
        "basolateral":  ["NaKATPase", "ClC-Kb"],
        "source_page": "",
        "source_key": "turkmen2024",
        "note": "Ends at the macula densa (TGF feedback).",
    },
    "DCT": {
        "full_name": "Distal Convoluted Tubule",
        "summary": "",
        "apical":       ["NCC"],
        "basolateral":  ["NaKATPase", "ClC-Kb"],
        "source_page": "",
        "source_key": "turkmen2024",
        "note": "NCC = thiazide diuretic target.",
    },
    "CNT": {
        "full_name": "Connecting Tubule",
        "summary": "",
        "apical":       ["ENaC", "ROMK"],
        "basolateral":  ["NaKATPase", "AQP3/4"],
        "source_page": "",
        "source_key": "turkmen2024",
    },
    "CCD": {
        "full_name": "Cortical Collecting Duct",
        "summary": "",
        "apical":       ["ENaC (PC)", "AQP2 (PC, ADH)",
                         "H-ATPase (IC-A)", "Pendrin (IC-B)"],
        "basolateral":  ["NaKATPase (PC)", "AE1 (IC-A)", "AQP3/4"],
        "source_page": "",
        "source_key": "turkmen2024",
        "note": "PC = principal cell; IC-A/B = type A/B intercalated cell (acid–base).",
    },
    "OMCD": {
        "full_name": "Outer Medullary Collecting Duct",
        "summary": "",
        "apical":       ["ENaC", "AQP2", "H/K-ATPase", "H-ATPase"],
        "basolateral":  ["NaKATPase", "AE1"],
        "source_page": "",
        "source_key": "turkmen2024",
    },
    "IMCD": {
        "full_name": "Inner Medullary Collecting Duct",
        "summary": "",
        "apical":       ["AQP2", "UT-A1 (urea)", "ENaC"],
        "basolateral":  ["NaKATPase", "AQP3/4", "UT-A3"],
        "source_page": "",
        "source_key": "turkmen2024",
        "note": "Urea recycling starts here — contributes to the inner-medullary osmotic gradient.",
    },
}


# =============================================================
#  TRANSPORTER CONTENT
# =============================================================
TRANSPORTER = {
    "NHE3":    {"full_name": "Sodium–Hydrogen Exchanger 3",     "stoichiometry": "1 Na⁺ ↔ 1 H⁺",
                "location": "PT/S3/mTAL apical", "drug": "", "summary": "", "source_page": ""},
    "NKCC2":   {"full_name": "Na-K-2Cl Cotransporter Type 2",   "stoichiometry": "1 Na⁺ + 1 K⁺ + 2 Cl⁻",
                "location": "TAL apical", "drug": "Loop diuretic (furosemide, bumetanide)",
                "summary": "", "source_page": ""},
    "NCC":     {"full_name": "Na-Cl Cotransporter",             "stoichiometry": "1 Na⁺ + 1 Cl⁻",
                "location": "DCT apical", "drug": "Thiazide diuretic",
                "summary": "", "source_page": ""},
    "ENaC":    {"full_name": "Epithelial Sodium Channel",       "stoichiometry": "Na⁺ channel",
                "location": "CNT/CD apical", "drug": "Amiloride, triamterene; regulated by aldosterone",
                "summary": "", "source_page": ""},
    "SGLT2":   {"full_name": "Sodium–Glucose Cotransporter 2",  "stoichiometry": "1 Na⁺ + 1 glucose",
                "location": "PT (S1/S2) apical", "drug": "Gliflozins (dapagliflozin, empagliflozin)",
                "summary": "", "source_page": ""},
    "SGLT1":   {"full_name": "Sodium–Glucose Cotransporter 1",  "stoichiometry": "2 Na⁺ + 1 glucose",
                "location": "S3 apical", "drug": "",
                "summary": "", "source_page": ""},
    "NaKATPase": {"full_name": "Sodium–Potassium ATPase",       "stoichiometry": "3 Na⁺ out / 2 K⁺ in (ATP)",
                "location": "All cells basolateral", "drug": "Digoxin",
                "summary": "", "source_page": ""},
    "AE1":     {"full_name": "Anion Exchanger 1 (Band 3)",      "stoichiometry": "1 Cl⁻ ↔ 1 HCO₃⁻",
                "location": "CD IC-A basolateral", "drug": "",
                "summary": "", "source_page": ""},
    "Pendrin": {"full_name": "Pendrin (SLC26A4)",               "stoichiometry": "1 Cl⁻ ↔ 1 HCO₃⁻",
                "location": "CD IC-B apical", "drug": "",
                "summary": "", "source_page": ""},
    "HATPase": {"full_name": "V-type H⁺-ATPase",                "stoichiometry": "H⁺ pump (ATP)",
                "location": "CD IC-A apical", "drug": "",
                "summary": "", "source_page": ""},
    "HKATPase": {"full_name": "H⁺-K⁺ ATPase",                   "stoichiometry": "H⁺ out / K⁺ in (ATP)",
                "location": "CD IC-A apical", "drug": "",
                "summary": "", "source_page": ""},
    "ROMK":    {"full_name": "Renal Outer Medullary K Channel", "stoichiometry": "K⁺ channel",
                "location": "TAL/CD apical", "drug": "",
                "summary": "", "source_page": ""},
    "AQP1":    {"full_name": "Aquaporin 1",                     "stoichiometry": "water channel",
                "location": "PT/SDL/LDL apical+basolateral", "drug": "",
                "summary": "", "source_page": ""},
    "AQP2":    {"full_name": "Aquaporin 2 (ADH-dependent)",     "stoichiometry": "water channel",
                "location": "CD PC apical", "drug": "Vaptans (ADH antagonist)",
                "summary": "", "source_page": ""},
}


# =============================================================
#  SOLUTE CONTENT
# =============================================================
SOLUTE = {
    "Na":   {"full_name": "Sodium (Na⁺)",
             "role": "Main extracellular cation; osmotic pressure, extracellular fluid volume.",
             "reabsorption": {"PT": "~67%", "TAL": "~25%", "DCT": "~5%", "CD": "~3%"},
             "summary": "", "source_page": ""},
    "K":    {"full_name": "Potassium (K⁺)",
             "role": "Main intracellular cation; membrane potential; cardiac rhythm.",
             "summary": "", "source_page": ""},
    "Cl":   {"full_name": "Chloride (Cl⁻)",
             "role": "Main extracellular anion; moves together with Na.",
             "summary": "", "source_page": ""},
    "HCO3": {"full_name": "Bicarbonate (HCO₃⁻)",
             "role": "Main plasma buffer; acid–base balance.",
             "summary": "", "source_page": ""},
    "urea": {"full_name": "Urea",
             "role": "End product of protein metabolism; critical to forming the inner-medullary "
                     "osmotic gradient.",
             "summary": "", "source_page": ""},
    "glu":  {"full_name": "Glucose",
             "role": "Normally all filtrate is reabsorbed; glucosuria once the threshold is exceeded "
                     "in diabetes.",
             "summary": "", "source_page": ""},
    "NH3":  {"full_name": "Ammonia (NH₃)",
             "role": "Uncharged gas, crosses membranes freely; renal acid excretion.",
             "summary": "", "source_page": ""},
    "NH4":  {"full_name": "Ammonium (NH₄⁺)",
             "role": "Charged, membrane-impermeant; can be carried in place of K via NKCC2.",
             "summary": "", "source_page": ""},
}


# =============================================================
#  Helper functions
# =============================================================
def segment_info(code):
    return SEGMENT.get(code, {})

def transporter_info(code):
    return TRANSPORTER.get(code, {})

def solute_info(code):
    return SOLUTE.get(code, {})

def cite_short(key, page=None):
    a = CITATIONS.get(key, {})
    s = a.get("short", key)
    if page:
        s += f", p. {page}"
    return s

def cite_full(key):
    return CITATIONS.get(key, {}).get("full", key)
