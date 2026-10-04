"""
Tests for the Model & Provenance page.

Run:   python tests/test_provenance.py     (or all tests: python tests/run_all.py)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_app import new_app  # noqa: E402,F401

def test_provenance_page_reads_commands_from_the_generator():
    import run_scenarios
    at = new_app("provenance")
    table = at.main.dataframe[0].value
    assert list(table["scenario"]) == [code for code, _, _ in run_scenarios.all_scenarios()]
    by_code = table.set_index("scenario")
    assert by_code.loc["F_SGLT2", "model command"].endswith("--inhibition SGLT2")
    assert by_code.loc["F_normal", "status"] == "in the dataset; all segments converged"
    assert "IMCD did not converge" in by_code.loc["M_normal", "status"]
    assert by_code.loc["F_ACE", "status"].startswith("not in the dataset")
    anchors = at.main.dataframe[1].value.set_index("location")
    assert anchors.loc["Papillary tip", "osmolality (mOsm)"] == 734.4
    assert anchors.loc["Cortex", "Na (mM)"] == 140.0

TESTS = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]

if __name__ == "__main__":
    failed = 0
    for test in TESTS:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:   # report every test, do not stop at the first failure
            failed += 1
            print(f"FAIL  {test.__name__}: {type(exc).__name__}: {str(exc)[:400]}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
