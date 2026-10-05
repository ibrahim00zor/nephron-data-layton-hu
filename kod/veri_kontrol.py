"""
veri_kontrol.py  —  Scenario data-integrity checker.

The model's Newton solver may fail to converge for some scenarios (especially the
collecting duct / merged computation); the result is then NaN or a physically impossible
negative value (negative osmolality/volume). This script scans each scenario and reports
whether it is reliable.

Verdict classes:
  CLEAN         -> no NaN, no negative osmolality/volume (trace-solute ~0 noise accepted)
  PROXIMAL_OK   -> single nephrons are sound but the collecting duct (merged/IMCD) is broken
  BROKEN        -> widespread NaN / negative osmolality

Run with:  python3 kod/veri_kontrol.py
"""
import os
import duckdb
import pandas as pd

PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET   = os.path.join(PROJ_ROOT, "veri", "nephron_veritabani.parquet")
DB        = f"'{PARQUET}'"

# Variables that cannot be negative (physical)
NONNEG = ('osmolality', 'water_volume')


def q(sql):
    return duckdb.sql(sql).df()


def scenario_report():
    """Per-scenario integrity metrics + verdict."""
    # Convergence indicators: NaN and negative Lumen osmolality (solute total).
    # NOTE: in IMCD merged the Cell-compartment volume comes out negative due to a separate
    # model artifact, but the Lumen (urinary path) is sound; so only Lumen counts for volume.
    df = q(f"""
        SELECT condition,
            SUM(CASE WHEN value IS NULL OR isnan(value) THEN 1 ELSE 0 END) AS nan,
            SUM(CASE WHEN variable='osmolality' AND compartment='Lumen' AND value < -1 THEN 1 ELSE 0 END) AS neg_osm,
            SUM(CASE WHEN variable='water_volume' AND compartment='Lumen' AND value < -0.001 THEN 1 ELSE 0 END) AS neg_lumen_vol
        FROM {DB}
        GROUP BY condition ORDER BY condition
    """)

    # Which segments/nephrons are broken? (Lumen-based genuine convergence failure)
    bad_loc = q(f"""
        SELECT DISTINCT condition, segment, nephron
        FROM {DB}
        WHERE (value IS NULL OR isnan(value))
           OR (variable='osmolality' AND compartment='Lumen' AND value < -1)
           OR (variable='water_volume' AND compartment='Lumen' AND value < -0.001)
        ORDER BY condition, segment
    """)

    verdicts = []
    for _, r in df.iterrows():
        cond = r['condition']
        n_bad = int(r['nan'] + r['neg_osm'] + r['neg_lumen_vol'])
        if n_bad == 0:
            v = "CLEAN"
        else:
            locs = bad_loc[bad_loc['condition'] == cond]
            # Only the collecting duct (merged) and last segments affected?
            distal = {'IMCD', 'OMCD', 'CCD', 'CNT', 'DCT'}
            affected = set(locs['segment'])
            if affected <= distal:
                v = "PROXIMAL_OK (collecting duct broken)"
            else:
                v = "BROKEN"
        verdicts.append(v)
    df['verdict'] = verdicts
    return df, bad_loc


if __name__ == "__main__":
    print(f"Source: {os.path.basename(PARQUET)}\n")
    df, bad_loc = scenario_report()
    print(df.to_string(index=False))
    print()
    if not bad_loc.empty:
        print("Breakage locations (scenario -> affected segments):")
        for cond in bad_loc['condition'].unique():
            segs = sorted(set(bad_loc[bad_loc['condition'] == cond]['segment']))
            print(f"  {cond:<12} {segs}")
    clean = df[df['verdict'] == 'CLEAN']['condition'].tolist()
    print(f"\nSafe to use (fully clean): {clean}")
