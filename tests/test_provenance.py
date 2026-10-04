"""
Tests for the Model & Provenance page.

Run:   python tests/test_provenance.py     (or all tests: python tests/run_all.py)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import html  # noqa: E402
import re  # noqa: E402

from test_app import new_app  # noqa: E402,F401


def tables(at):
    """The hand-ruled tables of a page (style.table), each as a list of {column: text}."""
    out = []
    for block in at.main.markdown:
        for found in re.findall(r"<table class='nd-table'>(.*?)</table>", block.value, flags=re.S):
            head = [html.unescape(c) for c in re.findall(r"<th(?:\s[^>]*)?>(.*?)</th>", found, flags=re.S)]
            rows = [[html.unescape(c) for c in re.findall(r"<td(?:\s[^>]*)?>(.*?)</td>", row, flags=re.S)]
                    for row in re.findall(r"<tr>(.*?)</tr>", found.split("<tbody>")[1], flags=re.S)]
            out.append([dict(zip(head, row)) for row in rows])
    return out


def test_provenance_page_reads_commands_from_the_generator():
    import run_scenarios
    at = new_app("provenance")
    scenarios, anchors = tables(at)[:2]
    assert [row["scenario"] for row in scenarios] == [code for code, _, _ in run_scenarios.all_scenarios()]
    by_code = {row["scenario"]: row for row in scenarios}
    assert by_code["F_SGLT2"]["model command"].endswith("--inhibition SGLT2")
    assert by_code["F_normal"]["status"] == "in the dataset; all segments converged"
    assert "IMCD did not converge" in by_code["M_normal"]["status"]
    assert by_code["F_ACE"]["status"].startswith("not in the dataset")
    by_place = {row["location"]: row for row in anchors}
    assert by_place["Papillary tip"]["osmolality (mOsm)"] == "734.4"
    assert by_place["Cortex"]["Na (mM)"] == "140"

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
