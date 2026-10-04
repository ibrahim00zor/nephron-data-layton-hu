"""
transport.py — Membrane transport fluxes: units, membranes, integration, mass balance.

The dataset holds, for every segment, the fluxes the model computes across the epithelium:
two pathway totals (`apical`, `paracellular`; Na+ and K+ only) and the flux through each
transporter. This module turns those rows into something that can be shown honestly.

UNITS (verified, see `mass_balance`)
    The model writes solute FLOWS already scaled to pmol/min, but writes FLUXES unscaled, in
    its internal nondimensional units (output.py). The Parquet labels them "pmol/min"; that
    label is not correct. From the model's nondimensionalisation (values.py: href = 1e-5 cm/s,
    Cref = 1e-3 mmol/cm3) one model flux unit is

        href * Cref = 1e-8 mmol/(s*cm2) = 600 pmol/(min*cm2)

    a flux DENSITY per unit luminal surface. This is not taken on trust: integrating
    (apical + paracellular) flux over the luminal surface pi*D*dx reproduces the drop in
    luminal flow exactly (ratio 1.0000) for Na+ and K+ in PT, S3, SDL, LDL, LAL, mTAL and cTAL,
    in every scenario and nephron type tested, and within 1% in DCT.

SIGN
    A flux is positive from the first to the second compartment of its membrane: for an
    apical membrane lumen -> cell, for a basolateral one cell -> interstitial side.

MEMBRANES
    Which membrane each transporter sits on is read from the model's parameter files
    (datafiles/<SEG>params_{F,M}_hum.dat, `transport_<A>_<B>_<Type>` rows; identical for both
    sexes). Where a transporter sits on several basolateral membranes the model writes one
    file per membrane; the current Parquet does not keep that label, so such rows share one
    key. They are summed here, which gives the transporter's total basolateral flux.
"""
import numpy as np
import pandas as pd
import streamlit as st

from ui_kit import q, DB

HREF = 1e-5    # cm/s       (model: values.py)
CREF = 1e-3    # mmol/cm3   (model: values.py)
FLUX_UNIT = 600.0            # pmol/(min*cm2) per model flux unit  (= HREF * CREF * 60 s/min * 1e9 pmol/mmol)
FLUX_UNIT_LABEL = "pmol/(min·cm²)"

# Cells of the model tubule a segment's grid belongs to. PT (181 points) and S3 (20 points)
# are two parts of one 200-cell proximal tubule; every other segment is its own 200-cell tubule.
GRID_CELLS = {"PT": 200, "S3": 200}

# Segments where the per-nephron integral is verified by mass balance.
CLOSES_EXACTLY = ("PT", "S3", "SDL", "LDL", "LAL", "mTAL", "cTAL")
CLOSES_WITHIN_1PCT = ("DCT",)
INTEGRABLE = set(CLOSES_EXACTLY + CLOSES_WITHIN_1PCT)
# CNT and the collecting ducts are coalescing tubules with intercalated-cell pathways that
# are not exported, so a per-nephron total cannot be reconstructed from the exported fluxes.

PATHWAY_TOTALS = {
    "apical": "Apical entry, total (lumen → cell)",
    "paracellular": "Paracellular, total (lumen → LIS)",
}

# (segment, transporter) -> membranes, from the model's human parameter files.
MEMBRANES = {
    ("PT", "SGLT2"): ["Lumen-Cell"], ("PT", "NHE3"): ["Lumen-Cell"], ("PT", "HATPase"): ["Lumen-Cell"],
    ("PT", "GLUT2"): ["Cell-Bath", "Cell-LIS"], ("PT", "NaKATPase"): ["Cell-Bath", "Cell-LIS"],
    ("S3", "SGLT1"): ["Lumen-Cell"], ("S3", "NHE3"): ["Lumen-Cell"], ("S3", "HATPase"): ["Lumen-Cell"],
    ("S3", "GLUT1"): ["Cell-Bath", "Cell-LIS"], ("S3", "NaKATPase"): ["Cell-Bath", "Cell-LIS"],
    ("mTAL", "NKCC2A"): ["Lumen-Cell"], ("mTAL", "NKCC2F"): ["Lumen-Cell"], ("mTAL", "NHE3"): ["Lumen-Cell"],
    ("mTAL", "KCC4"): ["Cell-LIS", "Cell-Bath"], ("mTAL", "NaKATPase"): ["Cell-LIS", "Cell-Bath"],
    ("cTAL", "NKCC2A"): ["Lumen-Cell"], ("cTAL", "NKCC2B"): ["Lumen-Cell"], ("cTAL", "NHE3"): ["Lumen-Cell"],
    ("cTAL", "KCC4"): ["Cell-LIS", "Cell-Bath"], ("cTAL", "NaKATPase"): ["Cell-LIS", "Cell-Bath"],
    ("DCT", "NHE3"): ["Lumen-Cell"], ("DCT", "NCC"): ["Lumen-Cell"], ("DCT", "ENaC"): ["Lumen-Cell"],
    ("DCT", "NaKATPase"): ["Cell-LIS", "Cell-Bath"],
    ("CNT", "ENaC"): ["Lumen-Cell"], ("CNT", "Pendrin"): ["Lumen-ICB"],
    ("CNT", "HATPase"): ["Lumen-ICA", "ICB-LIS", "ICB-Bath"],
    ("CNT", "HKATPase"): ["Lumen-Cell", "Lumen-ICA", "Lumen-ICB"],
    ("CNT", "AE1"): ["ICA-LIS", "ICA-Bath"],
    ("CNT", "NaKATPase"): ["Cell-LIS", "Cell-Bath", "ICA-LIS", "ICA-Bath", "ICB-LIS", "ICB-Bath"],
    ("CCD", "ENaC"): ["Lumen-Cell"], ("CCD", "Pendrin"): ["Lumen-ICB"],
    ("CCD", "HATPase"): ["Lumen-ICA", "ICB-LIS", "ICB-Bath"],
    ("CCD", "HKATPase"): ["Lumen-Cell", "Lumen-ICA", "Lumen-ICB"],
    ("CCD", "AE1"): ["ICA-LIS", "ICA-Bath"],
    ("CCD", "NaKATPase"): ["Cell-LIS", "Cell-Bath", "ICA-LIS", "ICA-Bath", "ICB-LIS", "ICB-Bath"],
    ("OMCD", "ENaC"): ["Lumen-Cell"], ("OMCD", "HATPase"): ["Lumen-ICA"],
    ("OMCD", "HKATPase"): ["Lumen-Cell", "Lumen-ICA"], ("OMCD", "AE1"): ["ICA-LIS", "ICA-Bath"],
    ("OMCD", "NHE1"): ["Cell-LIS", "Cell-Bath"],
    ("OMCD", "NaKATPase"): ["Cell-LIS", "Cell-Bath", "ICA-LIS", "ICA-Bath"],
    ("IMCD", "HKATPase"): ["Lumen-Cell"], ("IMCD", "NaKATPase"): ["Cell-LIS", "Cell-Bath"],
}


def side(membrane):
    """'apical' for a membrane facing the lumen, otherwise 'basolateral'."""
    return "apical" if membrane.startswith("Lumen-") else "basolateral"


def pathway_label(segment, transporter, membrane, profiles_summed):
    """Readable name for one row group of the flux data."""
    if transporter in PATHWAY_TOTALS:
        return PATHWAY_TOTALS[transporter]
    if membrane:
        return f"{transporter} · {membrane}"
    membranes = MEMBRANES.get((segment, transporter), [])
    if len(membranes) == 1:
        return f"{transporter} · {membranes[0]}"
    if profiles_summed > 1:
        return f"{transporter} · basolateral ({profiles_summed} membranes summed)"
    return transporter


@st.cache_data
def flux_segments():
    return q(f"SELECT DISTINCT segment FROM {DB} WHERE variable='flux'")["segment"].tolist()


@st.cache_data
def flux_solutes(segment):
    return sorted(q(f"SELECT DISTINCT solute FROM {DB} WHERE variable='flux' AND segment=?",
                    [segment])["solute"].tolist())


@st.cache_data
def profiles(scenario, segment, nephron, solute):
    """Flux profiles of every pathway that moves `solute` in one segment.

    Returns columns: pathway, transporter, position, value (model units), density
    (pmol/(min*cm2)). Rows that share a key — the same transporter on several basolateral
    membranes — are summed per position.
    """
    df = q(
        f"""SELECT transporter, membrane, position, SUM(value) AS value, COUNT(*) AS profiles_summed
            FROM {DB}
            WHERE condition=? AND variable='flux' AND segment=? AND nephron=? AND solute=?
            GROUP BY transporter, membrane, position
            ORDER BY transporter, membrane, position""",
        [scenario, segment, nephron, solute],
    )
    if df.empty:
        return df.assign(pathway=[], density=[])
    df["membrane"] = df["membrane"].fillna("")
    df["pathway"] = [pathway_label(segment, t, m, n)
                     for t, m, n in zip(df["transporter"], df["membrane"], df["profiles_summed"])]
    df["density"] = df["value"] * FLUX_UNIT
    return df


@st.cache_data
def slice_area(scenario, segment, nephron):
    """Luminal surface of each grid cell, in cm2: pi * diameter * (length / cells)."""
    geo = q(
        f"""SELECT position,
                   MAX(CASE WHEN variable='diameter' THEN value END) AS diameter,
                   MAX(CASE WHEN variable='length' THEN value END) AS length
            FROM {DB}
            WHERE condition=? AND segment=? AND nephron=? AND variable IN ('diameter','length')
            GROUP BY position ORDER BY position""",
        [scenario, segment, nephron],
    )
    cells = GRID_CELLS.get(segment, len(geo))
    return (np.pi * geo["diameter"] * geo["length"] / cells).to_numpy()


def integrate(profile_values, area):
    """Flux through the whole segment, in pmol/min per tubule.

    The model's scheme is implicit: the flow change across an interval uses the flux at its
    downstream cell, so the first point is not part of the sum.
    """
    values = np.asarray(profile_values, dtype=float)
    if len(values) != len(area) or len(values) < 2:
        return float("nan")
    return float(np.sum(values[1:] * FLUX_UNIT * area[1:]))


def segment_totals(scenario, segment, nephron, solute):
    """Per-pathway integral over the segment (pmol/min). Empty if the segment is not integrable."""
    df = profiles(scenario, segment, nephron, solute)
    if df.empty or segment not in INTEGRABLE:
        return pd.DataFrame(columns=["pathway", "total"])
    area = slice_area(scenario, segment, nephron)
    rows = [(name, integrate(group.sort_values("position")["value"], area))
            for name, group in df.groupby("pathway", sort=False)]
    return pd.DataFrame(rows, columns=["pathway", "total"])


def mass_balance(scenario, segment, nephron, solute):
    """Integrated (apical + paracellular) flux vs the drop in luminal flow, both in pmol/min.

    Returns (from_fluxes, flow_drop) or None when it cannot be evaluated (the two pathway
    totals exist for Na+ and K+ only, and only integrable segments are compared).
    """
    if segment not in INTEGRABLE:
        return None
    df = profiles(scenario, segment, nephron, solute)
    parts = df[df["transporter"].isin(PATHWAY_TOTALS)]
    if parts["transporter"].nunique() < 2:
        return None
    transepithelial = parts.groupby("position")["value"].sum().sort_index()
    flow = q(
        f"""SELECT value FROM {DB}
            WHERE condition=? AND variable='flow' AND segment=? AND nephron=? AND solute=?
                  AND compartment='Lumen' ORDER BY position""",
        [scenario, segment, nephron, solute],
    )["value"]
    if len(flow) < 2 or flow.isna().any() or transepithelial.isna().any():
        return None
    from_fluxes = integrate(transepithelial.to_numpy(), slice_area(scenario, segment, nephron))
    return from_fluxes, float(flow.iloc[0] - flow.iloc[-1])
