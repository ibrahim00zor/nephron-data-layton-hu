"""provenance.py — Where the data comes from and how to reproduce it.

Everything shown here is read from the generator script (run_scenarios.py), the dataset
itself, or the reference registry — nothing is typed in twice.
"""
import os
import platform

import duckdb
import pandas as pd
import plotly
import streamlit as st

import run_scenarios
from ui_kit import (
    q, DB, PARQUET, SCENARIO_LABEL, integrity_map, references_box, scenario_list,
)

st.markdown("## Model & Provenance")
st.caption("Where every number in this app comes from, and what it takes to reproduce it.")

in_dataset = scenario_list()
rows_by_scenario = q(f"SELECT condition, COUNT(*) AS n FROM {DB} GROUP BY condition").set_index("condition")["n"]
not_converged = integrity_map()

# ============================================================
#  1. Pipeline
# ============================================================
st.markdown("### 1. From model to app")
st.markdown(f"""
1. **Model.** The sex-specific human nephron model of the Layton group, run unchanged from the
   public code: [`mstadt/nephron`]({run_scenarios.MODEL_REPO}) at commit
   `{run_scenarios.MODEL_COMMIT[:12]}` (2022-07-05). This project processes the model's output;
   it does not re-implement the model.
2. **One run per scenario.** Each scenario is one command (table below). The model writes one
   text file per variable, solute, compartment and nephron type.
3. **Loader.** `kod/build_database.py` reads those files into one tidy table,
   `veri/{os.path.basename(PARQUET)}` — **{int(rows_by_scenario.sum()):,} rows**, {len(in_dataset)} scenarios.
4. **App.** Every chart and number is a query on that table. Figures in the text are computed
   from the data at display time, not typed in.
""")

# ============================================================
#  2. Scenarios
# ============================================================
st.markdown("### 2. Scenarios and the exact model commands")
table = []
for code, flags, _folder in run_scenarios.all_scenarios():
    if code not in in_dataset:
        status = "not in the dataset — the model's solver did not converge"
    elif code in not_converged:
        status = f"in the dataset; {', '.join(sorted(not_converged[code]))} did not converge (hidden in charts)"
    else:
        status = "in the dataset; all segments converged"
    table.append({
        "scenario": code,
        "description": SCENARIO_LABEL.get(code, "—"),
        "status": status,
        "rows": f"{int(rows_by_scenario[code]):,}" if code in rows_by_scenario.index else "—",
        "model command": run_scenarios.command(flags),
    })
st.dataframe(pd.DataFrame(table), hide_index=True, width='stretch')
st.caption(f"{len(in_dataset)} of {len(table)} targeted scenarios are in the dataset. The commands are read from "
           f"`kod/run_scenarios.py`, the script that generated the library.")

# ============================================================
#  3. Prescribed inputs
# ============================================================
st.markdown("### 3. What the model is given")
st.markdown(
    "The model computes transport along the tubule; it does **not** compute the surroundings of "
    "the tubule. The interstitial fluid composition is specified at three points — cortex, "
    "outer–inner medullary boundary, papillary tip — and interpolated linearly in between "
    "(Layton & Layton 2019, Methods and Table 2). It is the same in every scenario of this dataset. "
    "The model has no vasculature and does not simulate how the medullary gradient is generated."
)
anchors = [("Cortex", "CCD", 0.0), ("Outer–inner medullary boundary", "IMCD", 0.0), ("Papillary tip", "IMCD", 1.0)]
shown = ["Na", "K", "Cl", "urea"]
rows = []
for name, segment, position in anchors:
    values = q(
        f"""SELECT variable, solute, value FROM {DB}
            WHERE condition='F_normal' AND compartment='Bath' AND nephron='merged'
                  AND segment=? AND position=? AND variable IN ('con','osmolality')""",
        [segment, position],
    )
    row = {"location": name}
    for solute in shown:
        match = values[(values["variable"] == "con") & (values["solute"] == solute)]["value"]
        row[f"{solute} (mM)"] = round(float(match.iloc[0]), 1) if len(match) else None
    osm = values[values["variable"] == "osmolality"]["value"]
    row["osmolality (mOsm)"] = round(float(osm.iloc[0]), 1) if len(osm) else None
    rows.append(row)
st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
st.caption("Interstitial composition around the collecting duct, read from the dataset "
           "(`compartment='Bath'`). These are inputs: they describe the setting the tubule is placed "
           "in, not a result of the simulation.")

# ============================================================
#  4. Literature
# ============================================================
st.markdown("### 4. The model's literature")
references_box(["hu2021", "layton2019", "hu_layton2021", "model_stadt"],
               title="Papers and code the dataset is derived from", open=True)

# ============================================================
#  5. Reproduce
# ============================================================
st.markdown("### 5. Reproduce the dataset")
commands = "\n".join(
    f"{run_scenarios.command(flags):<92s}# {code}" for code, flags, _ in run_scenarios.all_scenarios()
    if code in in_dataset
)
st.code(
    f"""git clone {run_scenarios.MODEL_REPO} && cd nephron
git checkout {run_scenarios.MODEL_COMMIT}

{commands}

# copy each output folder to veri/ham_scenarios/<scenario>/ in this repository, then:
python3 kod/build_database.py""",
    language="bash",
)
st.markdown("""
- Run each scenario into an **empty** output folder: the model appends to its transporter-flux
  files, so a second run into the same folder corrupts them.
- A scenario with all nephron types takes roughly two hours on a laptop.
- The model code needs `numpy < 2.0`. The app does not run the model, so it is not affected.
- `kod/veri_kontrol.py` reports which scenarios and segments converged.
""")

# ============================================================
#  6. This app
# ============================================================
st.markdown("### 6. This app")
st.caption(f"Running on Python {platform.python_version()} · streamlit {st.__version__} · "
           f"duckdb {duckdb.__version__} · pandas {pd.__version__} · plotly {plotly.__version__}. "
           f"Tests: `python tests/test_app.py`.")
