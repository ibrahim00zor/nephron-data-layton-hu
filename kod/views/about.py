"""about.py — What this is, how to cite it, what is in it, and where to report an error.

Everything here is a statement of fact about the project (taken from CITATION.cff, the
licence, the dataset itself). The citation strings are kept in step with CITATION.cff;
tests/test_about.py checks that.
"""
import html

import streamlit as st

import nav
import style
from ui_kit import REFERENCES, build_id, dataset_fingerprint, health_metrics, reference_card

REPOSITORY = "https://github.com/ibrahim00zor/nefron-veri-gezgini"
TOOL_DOI = "10.5281/zenodo.20489610"
MODEL_DOI = "10.1016/j.isci.2021.102667"

BIBTEX = f"""@software{{zor_nephron_data_2026,
  author    = {{Zor, İbrahim}},
  title     = {{Nephron Data (Layton/Hu)}},
  year      = {{2026}},
  publisher = {{Zenodo}},
  doi       = {{{TOOL_DOI}}},
  url       = {{{REPOSITORY}}}
}}

@article{{hu_sex_2021,
  author  = {{Hu, Rui and McDonough, Alicia A. and Layton, Anita T.}},
  title   = {{Sex differences in solute and water handling in the human kidney:
             Modeling and functional implications}},
  journal = {{iScience}},
  year    = {{2021}},
  volume  = {{24}},
  number  = {{6}},
  pages   = {{102667}},
  doi     = {{{MODEL_DOI}}}
}}"""


def go(page, label):
    """A link to another page of the site, answered in place."""
    return (f"<a class='nd-go' href='{html.escape(nav.href(page), quote=True)}' "
            f"target='_self'>{label}</a>")


st.markdown("## About")
st.markdown(
    "<p class='nd-lede'>Nephron Data (Layton/Hu) is a reader for the output of a published "
    "mathematical model of the human nephron. It does not run the model and adds nothing to it: "
    "it lays the output out so that it can be read, compared and checked.</p>",
    unsafe_allow_html=True,
)

left, right = st.columns([3, 2], gap="large")

with left:
    # ------------------------------------------------------------ citing
    st.markdown("### Citing")
    st.markdown("A figure or a number taken from this site comes from the model. Cite the model, "
                "and this tool as the way you read it.")
    reference_card(REFERENCES["hu2021"])
    st.markdown(
        "<div class='nd-ref'><span class='nd-label'>Software</span>"
        "Zor İ. (2026). Nephron Data (Layton/Hu). <i>Zenodo</i>. "
        f"<a href='https://doi.org/{TOOL_DOI}' target='_blank'>doi:{TOOL_DOI}</a>"
        "<span class='gloss'>This tool. The DOI always points to the latest archived version.</span></div>",
        unsafe_allow_html=True,
    )
    with st.expander("BibTeX"):
        st.code(BIBTEX, language="bibtex")

    # ------------------------------------------------------------ what it is not
    st.markdown("### What this is not")
    st.markdown(
        "- **Not medical advice.** The charts are the output of a mathematical model, not patient "
        "data. They cannot be used for a diagnosis, a treatment or any decision about a patient.\n"
        "- **Not the model.** The model is the work of the Layton group; this site only reads what "
        "it writes. The exact command behind every scenario is on "
        + go("provenance", "Model &amp; Provenance") + ".\n"
        "- **Not complete.** Six of the ten scenarios that were attempted converged, and in two of "
        "those the end of the collecting duct did not. What is missing is listed on "
        + go("integrity", "Data Integrity") + ".\n"
        "- **Not a clinical text.** The clinical cases show model data; their text will be written "
        "from a verified source and is not there yet.",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------ corrections
    st.markdown("### Corrections")
    st.markdown(
        "An error in a number, a label or a citation is worth reporting. Open an issue in the "
        f"[repository]({REPOSITORY}/issues), with the address of the page: the address carries the "
        "selection, so it shows exactly what you were looking at."
    )

with right:
    # ------------------------------------------------------------ the dataset
    facts = health_metrics()
    per_scenario = facts["rows"] // max(facts["scenario_count"], 1)
    st.markdown("### The dataset")
    st.markdown(
        "<table class='nd-table'><tbody>"
        f"<tr><td>scenarios</td><td class='num'>{facts['scenario_count']}</td></tr>"
        f"<tr><td>rows per scenario</td><td class='num'>{per_scenario:,}</td></tr>"
        f"<tr><td>segments</td><td class='num'>{facts['segments']}</td></tr>"
        f"<tr><td>solutes</td><td class='num'>{facts['solutes']}</td></tr>"
        f"<tr><td>nephron types</td><td class='num'>{facts['nephrons']}</td></tr>"
        "</tbody></table>",
        unsafe_allow_html=True,
    )
    commit, data = build_id(), dataset_fingerprint()
    imprint = []
    if data:
        imprint.append(f"dataset <span class='nd-print' title='sha256 {data}'>{data[:12]}</span>")
    if commit:
        imprint.append(f"build <span class='nd-print' title='commit {commit}'>{commit[:7]}</span>")
    if imprint:
        st.markdown(f"<div class='nd-side-meta'>{' · '.join(imprint)}</div>", unsafe_allow_html=True)
    st.caption("Two copies of the dataset with the same fingerprint hold the same numbers.")

    # ------------------------------------------------------------ units
    st.markdown("### Units")
    st.markdown(
        "<table class='nd-table'><tbody>"
        "<tr><td>concentration</td><td class='num'>mM</td></tr>"
        "<tr><td>osmolality</td><td class='num'>mOsm</td></tr>"
        "<tr><td>water flow</td><td class='num'>nl/min</td></tr>"
        "<tr><td>solute flow</td><td class='num'>pmol/min</td></tr>"
        "<tr><td>transporter flux</td><td class='num'>pmol/(min·cm²)</td></tr>"
        "<tr><td>potential</td><td class='num'>mV</td></tr>"
        "</tbody></table>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------ licence
    st.markdown("### Licence")
    st.markdown(f"The code is under the MIT licence; the content is under CC BY 4.0. "
                f"The source is [on GitHub]({REPOSITORY}).")

    # ------------------------------------------------------------ keys
    st.markdown("### Keys")
    st.markdown(
        "<table class='nd-table'><tbody>"
        "<tr><td class='key'>]</td><td>the next segment along the nephron</td></tr>"
        "<tr><td class='key'>[</td><td>the previous segment</td></tr>"
        "<tr><td class='key'>¶</td><td>beside a page title: copy a link to this exact view</td></tr>"
        "<tr><td class='key'>?</td><td>show the keys on any page</td></tr>"
        "</tbody></table>",
        unsafe_allow_html=True,
    )
