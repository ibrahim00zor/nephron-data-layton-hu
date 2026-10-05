"""The About page states facts that live elsewhere in the repository; they must agree."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_app import new_app  # noqa: E402


def _cff(field):
    """A top-level field of CITATION.cff (the file is simple enough to read by line)."""
    with open(os.path.join(ROOT, "CITATION.cff"), encoding="utf-8") as f:
        for line in f:
            if line.startswith(field + ":"):
                return line.split(":", 1)[1].strip().strip('"')
    raise AssertionError(f"{field} not in CITATION.cff")


def test_about_cites_what_the_citation_file_says():
    at = new_app("about")
    shown = " ".join(m.value for m in at.main.markdown) + " ".join(c.value for c in at.main.code)
    assert _cff("doi") in shown                          # this tool
    assert _cff("title") in shown
    assert _cff("repository-code") in shown
    assert "10.1016/j.isci.2021.102667" in shown         # the model paper (also in CITATION.cff)
    with open(os.path.join(ROOT, "CITATION.cff"), encoding="utf-8") as f:
        assert "10.1016/j.isci.2021.102667" in f.read()
    assert f"year      = {{{_cff('year')}}}" in shown      # the BibTeX entry carries the same year


def test_about_counts_the_dataset_itself():
    at = new_app("about")
    shown = re.sub(r"<[^>]+>", " ", " ".join(m.value for m in at.main.markdown))
    assert re.search(r"scenarios\s+6\b", shown), shown[:400]
    assert "1,033,065" in shown                           # rows per scenario, counted from the table


def test_the_masthead_offers_the_worlds_and_marks_where_you_are():
    at = new_app("comparison")
    head = next(m.value for m in at.main.markdown if "<div class='nd-masthead'>" in m.value)
    for world in ("Model world", "Clinical world", "Data &amp; quality", "About"):
        assert world in head, world
    assert re.search(r"class='nd-go nd-nav on'[^>]*>Model world<", head)           # the world
    assert re.search(r"class='nd-go nd-nav on'[^>]*>Comparison<", head)            # the page
    assert head.count("class='nd-go nd-nav on'") == 2
    at = new_app("about")
    head = next(m.value for m in at.main.markdown if "<div class='nd-masthead'>" in m.value)
    assert "nd-pages" not in head                         # About belongs to no world: no second line
