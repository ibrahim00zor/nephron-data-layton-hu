#!/usr/bin/env python3
"""
run_scenarios.py — Autonomous generator for the scenario library.

Runs each scenario in turn and, if successful, copies it into the project folder.
Skips scenarios that were already completed (resumable).

Run (from a terminal):
    caffeinate -is nohup python3 ~/Desktop/Nefron-Projesi/kod/run_scenarios.py \\
        > ~/Desktop/Nefron-Projesi/yedekler/scenario_run.log 2>&1 &

Then watch progress with `tail -f ~/Desktop/Nefron-Projesi/yedekler/scenario_run.log`.

Estimated time: 9 scenarios x ~2h = ~18 hours. The MacBook must stay awake + plugged in + caffeinate.
"""

import os
import sys
import subprocess
import shutil
import time
from datetime import datetime

# Scenarios — (label, args, model_output_folder_name)
# The file_to_save logic in the model's parallel_simulate.py:
#   diabetes -> {sex}_hum_{Severity}_diab_N_unx
#   inhibition -> {inhib}_{sex}_hum
#   obese -> {sex}_hum_Y_obese
#   HT -> {sex}_hum_HT
#   normal -> {sex}_hum_normal
SCENARIOS = [
    # F_normal already exists — skipped
    ("M_normal",      ["--sex","male","--species","human","--type","multiple"],
                      "male_hum_normal"),
    ("F_diab_mod",    ["--sex","female","--species","human","--type","multiple","--diabetes","Moderate"],
                      "female_hum_Moderate_diab_N_unx"),
    ("F_diab_severe", ["--sex","female","--species","human","--type","multiple","--diabetes","Severe"],
                      "female_hum_Severe_diab_N_unx"),
    ("F_SGLT2",       ["--sex","female","--species","human","--type","multiple","--inhibition","SGLT2"],
                      "SGLT2_female_hum"),
    ("F_ACE",         ["--sex","female","--species","human","--type","multiple","--inhibition","ACE"],
                      "ACE_female_hum"),
    ("F_obese",       ["--sex","female","--species","human","--type","multiple","--obese","Y"],
                      "female_hum_Y_obese"),
    ("F_HT",          ["--sex","female","--species","human","--type","multiple","--HT","Y"],
                      "female_hum_HT"),
    ("M_SGLT2",       ["--sex","male","--species","human","--type","multiple","--inhibition","SGLT2"],
                      "SGLT2_male_hum"),
    # F_UNX: the model writes the folder as `female_hum_normal` (limited parameter system).
    # We temporarily back up the existing F_normal, then restore it afterward.
    ("F_UNX",         ["--sex","female","--species","human","--type","multiple","--unx","Y"],
                      "female_hum_normal"),
]

MODEL_DIR = os.path.expanduser("~/nephron")
PROJECT_DIR = os.path.expanduser("~/Desktop/Nefron-Projesi")
SCENARIOS_DIR = os.path.join(PROJECT_DIR, "veri", "ham_scenarios")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_scenario(label, args, model_folder):
    """Run a single scenario. Resumable: skip if the output already exists."""
    dest = os.path.join(SCENARIOS_DIR, label)
    if os.path.isdir(dest) and len(os.listdir(dest)) > 1000:
        log(f"⏭  {label}: already exists ({len(os.listdir(dest))} files), skipped")
        return True

    # UNX standalone: writes to female_hum_normal -> back up the existing F_normal
    is_unx = "--unx" in args and "Y" in args
    backup_path = None
    if is_unx:
        existing = os.path.join(MODEL_DIR, "female_hum_normal")
        if os.path.isdir(existing):
            backup_path = os.path.join(MODEL_DIR, "female_hum_normal__UNX_SAVE")
            log(f"   UNX prep: female_hum_normal -> female_hum_normal__UNX_SAVE")
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            shutil.move(existing, backup_path)

    # Delete any previous same-named output (append-bug prevention)
    src = os.path.join(MODEL_DIR, model_folder)
    if os.path.isdir(src):
        log(f"   Old {model_folder} found, deleting")
        shutil.rmtree(src)

    # Run the simulation
    log(f"▶  {label}: STARTED — {' '.join(args)}")
    t0 = time.time()
    try:
        subprocess.run(["python3", "parallel_simulate.py"] + args,
                       cwd=MODEL_DIR, check=True)
    except subprocess.CalledProcessError as e:
        log(f"❌ {label}: simulation error (exit {e.returncode})")
        if backup_path and os.path.isdir(backup_path):
            shutil.move(backup_path, os.path.join(MODEL_DIR, "female_hum_normal"))
        return False
    except KeyboardInterrupt:
        log(f"⏸  {label}: stopped by user")
        if backup_path and os.path.isdir(backup_path):
            shutil.move(backup_path, os.path.join(MODEL_DIR, "female_hum_normal"))
        sys.exit(130)
    dt = time.time() - t0
    log(f"   simulation finished ({dt/60:.1f} min = {dt/3600:.2f} h)")

    # Copy -> into the project
    if not os.path.isdir(src):
        log(f"❌ {label}: expected output missing: {src}")
        if backup_path and os.path.isdir(backup_path):
            shutil.move(backup_path, os.path.join(MODEL_DIR, "female_hum_normal"))
        return False
    os.makedirs(SCENARIOS_DIR, exist_ok=True)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    log(f"✅ {label}: {len(os.listdir(dest))} files copied -> {dest}")

    # UNX: clean the model folder + restore F_normal
    if is_unx and backup_path:
        if os.path.isdir(src):
            shutil.rmtree(src)
        if os.path.isdir(backup_path):
            shutil.move(backup_path, os.path.join(MODEL_DIR, "female_hum_normal"))
            log(f"   UNX cleanup: F_normal restored")

    return True


def main():
    log("=" * 60)
    log(f"Scenario library generation — {len(SCENARIOS)} scenarios (F_normal already exists)")
    log(f"Model directory: {MODEL_DIR}")
    log(f"Destination:     {SCENARIOS_DIR}")
    log(f"Estimated time:  ~{len(SCENARIOS)*2:.0f} hours")
    log("=" * 60)

    if not os.path.isdir(MODEL_DIR):
        log(f"ERROR: model directory not found: {MODEL_DIR}")
        sys.exit(1)

    os.makedirs(SCENARIOS_DIR, exist_ok=True)
    results = []
    for i, (label, args, folder) in enumerate(SCENARIOS, 1):
        log("")
        log(f"--- [{i}/{len(SCENARIOS)}] {label} ---")
        ok = run_scenario(label, args, folder)
        results.append((label, ok))

    log("")
    log("=" * 60)
    log("ALL DONE")
    for label, ok in results:
        log(f"  {'✅' if ok else '❌'} {label}")
    log("=" * 60)
    log("Next step: python3 kod/build_database.py (rebuild the parquet)")


if __name__ == "__main__":
    main()
