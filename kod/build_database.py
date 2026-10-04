"""
build_database.py  —  data loader for this project (multi-scenario).
veri/ham_scenarios/<scenario>/*.txt -> a single tidy Parquet (with a condition column).
Design: 'classify-then-route' -> determine the file type, then parse with the right rule.

Run with:  python3 kod/build_database.py
"""
import glob
import os
import pandas as pd
import numpy as np

# --- Paths ---
KOD_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT  = os.path.dirname(KOD_DIR)
SCENARIOS_ROOT = os.path.join(PROJ_ROOT, "veri", "ham_scenarios")
OUTPUT     = os.path.join(PROJ_ROOT, "veri", "nephron_veritabani.parquet")

# Known constants (identical to the model's output.py / driver.py)
SOLUTES = ['Na','K','Cl','HCO3','H2CO3','CO2','HPO4','H2PO4','urea','NH3','NH4','H','HCO2','H2CO2','glu']
SOLUTES_BY_LEN = sorted(SOLUTES, key=len, reverse=True)
NEPHS = {'sup','jux1','jux2','jux3','jux4','jux5'}
TRANSPORTERS = {'NaKATPase','NHE3','KCC4','NKCC2A','NKCC2B','NKCC2F','HKATPase','AE1',
                'HATPase','Pendrin','ENaC','SGLT2','SGLT1','NHE1','NCC','GLUT2','GLUT1','NKCC1'}

# 'flux' rows are written by the model in its internal units (output.py does not scale them,
# unlike flows). One model unit = href*Cref = 600 pmol/(min*cm2) of luminal surface; diameter
# and length are in cm. Both are verified by mass balance in kod/transport.py.
UNITS = {'con':'mM', 'flow':'pmol/min', 'water_volume':'nl/min',
         'flux':'model flux unit (x600 = pmol/min/cm2)',
         'osmolality':'mOsm', 'pH':'', 'potential':'mV',
         'pressure':'unknown', 'diameter':'cm', 'length':'cm'}

# Compartment order used by the model (output.py); a two-digit membrane id in a file name,
# e.g. Na14, means "from compartment 1 to compartment 4" = Cell-LIS.
COMPARTMENTS = ['Lumen', 'Cell', 'ICA', 'ICB', 'LIS', 'Bath']

# Segment grid (number of points) sizes — fixed by the model. Everything else is 200.
SEGMENT_GRID = {'PT': 181, 'S3': 20}
DEFAULT_GRID = 200

# --- Multi-membrane flux files ---
# The model has TWO ways of writing a transporter that sits on several membranes:
#  (a) one file per membrane, with the membrane id in the file name (NaKATPase_Na14, _Na15, ...)
#      -> handled by `membrane_label()`;
#  (b) one file for all membranes, interleaved, with no id in the name -> handled below.
# Some transporters (AE1, HATPase, HKATPase, NHE1) belong to more than one cell membrane
# in a segment; the model writes their fluxes into a SINGLE file, WITHOUT a membrane id in
# the file name, in append mode. Result: an N*grid-row file where the data is NOT
# position-based but membrane-based INTERLEAVED:
#     [pos0_m0, pos0_m1, pos0_m2, pos1_m0, pos1_m1, pos1_m2, ...]
# So membrane m's profile = values[m::num_membranes] (separated by stride).
# The membrane order is the transport_ line order in the model's parameter files
# (datafiles/<SEG>params_*_hum.dat); the table below was extracted from that order,
# sex-filtered, and validated against file lengths. Label = the compartment pair.
#   Compartments: Cell=principal, ICA=type-A intercalated cell, ICB=type-B intercalated cell,
#   LIS=lateral intercellular space, Bath=interstitium, Lumen=tubule lumen.
MEMBRANE_ORDER = {
    ('CNT',  'HATPase'):  ['Lumen-ICA', 'ICB-LIS', 'ICB-Bath'],
    ('CNT',  'HKATPase'): ['Lumen-Cell', 'Lumen-ICA', 'Lumen-ICB'],
    ('CNT',  'AE1'):      ['ICA-LIS', 'ICA-Bath'],
    ('CCD',  'HATPase'):  ['Lumen-ICA', 'ICB-LIS', 'ICB-Bath'],
    ('CCD',  'HKATPase'): ['Lumen-Cell', 'Lumen-ICA', 'Lumen-ICB'],
    ('CCD',  'AE1'):      ['ICA-LIS', 'ICA-Bath'],
    ('OMCD', 'HKATPase'): ['Lumen-Cell', 'Lumen-ICA'],
    ('OMCD', 'AE1'):      ['ICA-LIS', 'ICA-Bath'],
    ('OMCD', 'NHE1'):     ['Cell-LIS', 'Cell-Bath'],
}


def split_solute_membid(token):
    """ 'Na11'->('Na','11') ; 'HCO311'->('HCO3','11') ; 'Cl'->('Cl','') """
    for s in SOLUTES_BY_LEN:
        if token.startswith(s):
            return s, token[len(s):]
    return token, ''


def membrane_label(membid):
    """ '14' -> 'Cell-LIS' ; '' or anything unexpected -> None """
    if len(membid) == 2 and membid.isdigit():
        a, b = int(membid[0]), int(membid[1])
        if a < len(COMPARTMENTS) and b < len(COMPARTMENTS):
            return f"{COMPARTMENTS[a]}-{COMPARTMENTS[b]}"
    return None


def parse_filename(stem):
    """File name (without extension) -> record dict. None if unrecognized."""
    parts = stem.split('_')
    if len(parts) < 4:
        return None
    sex, species, segment = parts[0], parts[1], parts[2]
    rest = parts[3:]

    if rest and rest[-1] in NEPHS:
        nephron = rest[-1]; rest = rest[:-1]
    else:
        nephron = 'merged'

    rec = dict(sex=sex, species=species, segment=segment, nephron=nephron,
               solute=None, compartment=None, transporter=None, membrane=None)
    if not rest:
        return None
    head = rest[0]

    try:
        if head in ('con', 'flow'):
            rec['variable'] = head; rec['solute'] = rest[2]; rec['compartment'] = rest[4]
        elif head in ('osmolality', 'pressure', 'pH'):
            rec['variable'] = head; rec['compartment'] = rest[2]
        elif head == 'water':
            rec['variable'] = 'water_volume'; rec['compartment'] = rest[3]
        elif head in ('length', 'diameter'):
            rec['variable'] = head
        elif head == 'potential':
            rec['variable'] = 'potential'; rec['compartment'] = rest[2] + '-' + rest[3]
        elif head in ('apical', 'paracellular'):
            rec['variable'] = 'flux'; rec['transporter'] = head
            rec['solute'], _ = split_solute_membid(rest[1])
        elif head in TRANSPORTERS:
            rec['variable'] = 'flux'; rec['transporter'] = head
            rec['solute'], membid = split_solute_membid(rest[1])
            rec['membrane'] = membrane_label(membid)
        else:
            return None
    except IndexError:
        return None
    return rec


def make_frame(rec, condition, profile, membrane):
    """Turns a single (membrane) profile into a tidy DataFrame piece."""
    n = len(profile)
    return pd.DataFrame({
        "sex": rec['sex'], "species": rec['species'], "condition": condition,
        "nephron": rec['nephron'], "segment": rec['segment'],
        "position": np.linspace(0, 1, n),
        "variable": rec['variable'], "solute": rec['solute'],
        "compartment": rec['compartment'], "transporter": rec['transporter'],
        "membrane": membrane,
        "value": profile, "unit": UNITS.get(rec['variable'], 'unknown'),
        "source": condition,
    })


def load_scenario(scenario_dir, condition):
    """Loads a single scenario folder and adds the condition column.
    Splits multi-membrane flux files per membrane (see MEMBRANE_ORDER)."""
    files = sorted(glob.glob(os.path.join(scenario_dir, "*.txt")))
    if not files:
        return pd.DataFrame(), [], []
    frames, unknown, suspicious = [], [], []
    for path in files:
        stem = os.path.basename(path)[:-4]
        rec = parse_filename(stem)
        if rec is None:
            unknown.append(stem); continue
        values = pd.read_csv(path, header=None)[0].values
        n = len(values)
        grid = SEGMENT_GRID.get(rec['segment'], DEFAULT_GRID)

        # Is it a multi-membrane flux file? (length an exact multiple of grid and > grid)
        if rec['variable'] == 'flux' and n > grid and n % grid == 0:
            k = n // grid
            labels = MEMBRANE_ORDER.get((rec['segment'], rec['transporter']))
            if labels is None or len(labels) != k:
                # Not in the mapping table -> still split CORRECTLY (stride),
                # but we can't give an anatomic label; label by index and flag it.
                labels = [f"m{m}" for m in range(k)]
                suspicious.append((stem, n, k))
            for m in range(k):
                # interleaved: membrane m = every k-th value
                frames.append(make_frame(rec, condition, values[m::k], labels[m]))
        else:
            frames.append(make_frame(rec, condition, values, rec['membrane']))
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), unknown, suspicious


def load_all():
    """Loads every subfolder under ham_scenarios/."""
    if not os.path.isdir(SCENARIOS_ROOT):
        raise FileNotFoundError(f"Scenario root not found: {SCENARIOS_ROOT}")
    scenarios = sorted([d for d in os.listdir(SCENARIOS_ROOT)
                        if os.path.isdir(os.path.join(SCENARIOS_ROOT, d))])
    print(f"{len(scenarios)} scenarios found: {scenarios}")

    all_frames, all_unknown, all_suspicious = [], [], []
    for scn in scenarios:
        path = os.path.join(SCENARIOS_ROOT, scn)
        print(f"  loading: {scn}", end=" ... ", flush=True)
        df, unk, susp = load_scenario(path, scn)
        if df.empty:
            print("EMPTY (skipped)")
            continue
        print(f"{len(df):,} rows")
        all_frames.append(df)
        all_unknown.extend([(scn, u) for u in unk])
        all_suspicious.extend([(scn, s) for s in susp])
    if not all_frames:
        raise RuntimeError("No scenario could be loaded.")
    return pd.concat(all_frames, ignore_index=True), all_unknown, all_suspicious


if __name__ == "__main__":
    table, unknown, suspicious = load_all()
    print(f"\nTotal rows: {len(table):,}")
    print(f"Scenarios: {sorted(table['condition'].unique())}")
    print(f"Unparseable files: {len(unknown)}")
    n_multi = int((table['membrane'].notna()).sum())
    n_memb_files = table[table['membrane'].notna()][
        ['condition','segment','transporter','solute','nephron']].drop_duplicates().shape[0]
    print(f"Multi-membrane flux: {n_memb_files} files split per membrane "
          f"({n_multi:,} membrane-labeled rows)")
    if suspicious:
        print(f"WARNING - multi-membrane files NOT in the mapping table: {len(suspicious)} "
              f"(split correctly by stride but without an anatomic label; add to MEMBRANE_ORDER):")
        for item in suspicious[:10]:
            print(f"    {item}")
    table.to_parquet(OUTPUT, index=False)
    print(f"\nWritten -> {OUTPUT}")
