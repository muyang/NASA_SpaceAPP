# Field Shift · Research Explorer

Open `index.html` directly in a browser. The English demo is one self-contained file (under 1 MB) with no runtime requests for map tiles, libraries, fonts or data. A local HTTP server is optional.

The page starts with a research knowledge graph. Choose a question, inspect a node, follow typed relationships, open a linked analysis or evidence panel, and download the enriched graph JSON. The full framework uses 24 nodes; small screens show readable question traces. Arrows describe research dependencies and provenance, not demonstrated causality.

The page also includes:

- An interactive county map: research sites, climate resemblance and data provenance; search, zoom, pan and county details.
- Farmer constraint inputs, three illustrative rotation discussions and a downloadable memo. Unknowns remain unknown; no recommendation score is generated.
- Annual Marsden contrast charts and five PFI farm results, including negative outcomes and source conflicts.
- All-assumption model-error charts and conditional historical economics.
- Evidence panels E1–E7 with source links and local JSON downloads.

The final table has 3,107 county records; supplied outlines cover 3,098. The nine records without geometry remain searchable. Climate resemblance is not crop suitability or process-model validation.

External links are optional source references. Opening them needs an internet connection; using the map, charts, filters, downloads and farmer inputs does not. Inputs are temporary and are not transmitted or saved automatically.

The old `planner/index.html`, `evidence.html`, `records.html` and `research-test.html` addresses redirect to the corresponding section in the new page. The full original test instrument remains in the complete archive; the present page does not claim a real farmer test.

To rebuild: from `repo2`, run `python3 04_reproduce/demo/build_demo.py` after installing the core Python dependencies. Source CSV/JSON evidence remains in `03_evidence`; geometry and authoring source are in `04_reproduce/demo`. The generated HTML embeds the final data for direct-file compatibility.
