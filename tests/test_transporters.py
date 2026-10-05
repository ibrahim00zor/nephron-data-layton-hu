"""
Tests for the transporter-flux layer (kod/transport.py) and the Transporters page.

Run:   python tests/test_transporters.py     (or all tests: python tests/run_all.py)

Covered: the unit conversion closes the mass balance; membrane copies of one transporter
are summed rather than drawn as one zig-zag line; the page falls back honestly when a
solute has no exported flux; a clinical case opens the page with its context.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_app import CASES, captions, jump, main_select, new_app, page  # noqa: E402,F401

def test_flux_units_close_the_mass_balance():
    """600 pmol/(min*cm2) per model unit is only right if fluxes reproduce the flow drop."""
    import transport
    for scenario, nephron, segment, solute in [
        ("F_normal", "sup", "PT", "Na"), ("F_normal", "sup", "S3", "K"), ("M_SGLT2", "jux5", "LAL", "Na"),
        ("F_diab_mod", "jux3", "mTAL", "K"), ("F_HT", "sup", "cTAL", "Na"), ("F_SGLT2", "sup", "SDL", "Na"),
    ]:
        from_fluxes, flow_drop = transport.mass_balance(scenario, segment, nephron, solute)
        assert abs(from_fluxes / flow_drop - 1) < 1e-5, (scenario, nephron, segment, solute, from_fluxes, flow_drop)
    from_fluxes, flow_drop = transport.mass_balance("F_normal", "DCT", "sup", "Na")
    assert abs(from_fluxes / flow_drop - 1) < 0.01
    # not evaluable: coalescing tubule / a solute without pathway totals
    assert transport.mass_balance("F_normal", "CNT", "sup", "Na") is None
    assert transport.mass_balance("F_normal", "PT", "sup", "glu") is None


def test_transporter_profiles_have_one_value_per_position():
    """NaKATPase sits on two basolateral membranes in PT; the dataset stores both under one key."""
    import transport
    df = transport.profiles("F_normal", "PT", "sup", "Na")
    assert not df.duplicated(["pathway", "position"]).any()
    pump = df[df["transporter"] == "NaKATPase"]
    assert set(pump["pathway"]) == {"NaKATPase · basolateral (2 membranes summed)"}
    assert set(pump["profiles_summed"]) == {2} and len(pump) == 181
    # every (segment, transporter) in the data has a known membrane
    inventory = transport.q(f"SELECT DISTINCT segment, transporter FROM {transport.DB} WHERE variable='flux'")
    unknown = [(r.segment, r.transporter) for r in inventory.itertuples()
               if r.transporter not in transport.PATHWAY_TOTALS and (r.segment, r.transporter) not in transport.MEMBRANES]
    assert not unknown, unknown


def test_transporters_page():
    at = new_app("transporters")
    assert main_select(at, "Segment").value == "PT" and main_select(at, "Solute").value == "Na"
    assert any("Mass balance" in s.value and "ratio 1.0000" in s.value for s in at.success)
    assert len(at.main.get("plotly_chart")) == 2          # one per tab

    # a solute no transporter moves in this segment: fall back, say so, keep the selection
    at = new_app("transporters", solute="urea", segment="mTAL")
    assert main_select(at, "Solute").value != "urea"
    assert any("No exported flux moves urea" in i.value for i in at.info)
    assert at.session_state["ctx_solute"] == "urea"

    # collecting duct: flux density only, and the page says why there is no total
    at = new_app("transporters", segment="CCD")
    assert "coalescing tubule" in captions(at)
    assert not at.success


def test_clinical_case_opens_transporters():
    at = jump(new_app("clinical", scenario="F_SGLT2", case="SGLT2"), "case_SGLT2_trn")
    assert page(at) == "transporters"
    assert main_select(at, "Segment").value == "cTAL"
    assert at.main.multiselect[0].value == ["F_normal", "F_SGLT2"]
    assert CASES["SGLT2"]["title"] in captions(at)

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
