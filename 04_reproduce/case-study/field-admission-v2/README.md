# Field-record admission and diagnostic replay v2

This release supports research verification, not a farmer-specific yield/profit forecast or rotation recommendation. Full CBA, MCA and field-validation gates remain closed. The original field record is not replaced by an estimated hydraulic parameter or an inferred zero.

Start with `outputs/field-admission-v2/Field_Admission_Validation_Report_CN.md` and `processed/admission_gates.json`. Source receipts contain URLs, fixed Git commit, Git blob SHA-1 and SHA-256. New diagnostics are separate from the frozen legacy model parameters. `fieldshift-eo-rs` is an independent exploratory model, not APSIM.

## Reproduce offline

Extract the ZIP and change to its root. Prerequisites: Python 3.12 with numpy, pandas and openpyxl; Rust/Cargo plus a working C linker. Authoring used numpy 2.3.5, pandas 2.2.3 and openpyxl 3.1.5 on macOS x86_64. No GPU, Google credentials, NASA login, external Cargo crates or network downloads are needed to reproduce the included inputs.

Run in order:

```sh
python3 case-study/field-admission-v2/src/audit_management.py
python3 case-study/field-admission-v2/src/audit_hydraulics.py
python3 case-study/field-admission-v2/src/analyze_economics.py
python3 case-study/field-admission-v2/src/run_field_replay.py
python3 case-study/field-admission-v2/src/evaluate_replay.py
python3 case-study/field-admission-v2/src/verify_admission.py
python3 case-study/field-admission-v2/src/build_deliverables.py
```

The model runner uses system `cargo` if the original repository toolchain is absent. `FIELD_SHIFT_CARGO` can select another executable; Rustup users must also keep their normal `RUSTUP_HOME` and `CARGO_HOME`. The Mac SDK override is used only if that SDK exists. Linux/macOS are the supported reproduction targets here; a Windows executable path adaptation has not been tested.

Re-running overwrites derived audit and diagnostic files in the extracted copy. All 32 assumption combinations are retained. Check numerical scores with tolerance, not binary hashes across compiler/platforms. `replay_results/receipt.json` records the executed code and input hashes, and `verification_results.json` is a technical integrity check, not independent agronomic validation. `fetch_sources.py` and `fetch_papers.py` are acquisition helpers and are **not** required for offline reproduction.

## Source and unit caveats

- 2014 soil cores cover eight plots in 2- and 4-year corn phases, five horizons to 100 cm. No measured retention curve, Ksat or exact sample date is supplied. PTF priors are estimates; SOC/OM and particle-density assumptions remain explicit.
- 2014 water conversions use same-plot bulk density with declared depth mapping. The dry-soil-mass basis is presumed from the original g/g label. The year-conflicting and ambiguous aggregate records remain excluded.
- 1,168 source log clusters are not 1,168 unique operations. Forty date/sheet-year conflicts and source-version overlap remain visible.
- The four 2014 corn plot-years share a weather year. Thirty-two model runs and 64 water plot-dates do not create independent climate replicates. Regional POWER weather is not field-station ground truth.
- Soil SOC/total-N stocks are used as a diagnostic January organic-pool proxy. Total N has not been separated from mineral N; the separate assumed initial mineral pool may overlap that basis. Initial residue C/N, organic-mulch flag, crop parameters and simplified flows remain assumptions.
- Historical 2008–2012 estimated returns are stratified by GE/Non-GE management package and annualized at equal phase areas. Point-estimate order is not statistical superiority, a current-price budget, a discounted transition CBA or farmer-weighted MCA. No current buyer contract was verified.
- No actual farmer usability participants or synthetic farmer feedback are included.

## Attribution and redistribution

`case-study/field-admission-v2/MARSden_LICENSE.md` preserves the author repository MIT notice. Repository source: Vanessa Nichols and contributors, `vanichols/maRsden`, commit `01476a18c01115f70f154cf7e94c1951205fbda1`. Raw source files retain their author attribution; derived unit conversions and diagnostics are this project's analysis.

Soil supplement: Lazicki PA, Liebman M, Wander MM (2016), *Root Parameters Show How Management Alters Resource Distribution and Soil Quality in Conventional and Low-Input Cropping Systems in Central Iowa*, PLOS ONE 11(10): e0164209, https://doi.org/10.1371/journal.pone.0164209 . S1/S2 and article are CC BY; original CSV/HTML and citations are retained.

Economic paper: Mulik K (2015), *Economic Impacts of Diversified Cropping Systems*, AAEA/WAEA selected conference paper, https://ageconsearch.umn.edu/record/205805 . The unmodified PDF retains its copyright/noncommercial-copy notice. It is included for noncommercial research verification, not relicensed under MIT. Table 1 was transcribed and visually checked; this release is not a reproduction of the paper's full econometric analysis.

Retention priors cite Saxton KE & Rawls WJ (2006), https://doi.org/10.2136/sssaj2005.0117 . The failed mirror PDF download is not counted as acquired.

Independent Rust library license: `fieldshift-eo-rs/LICENSE`. No credentials, `.git`, toolchain caches, target binaries or participant data are included. Site source and private-host deployment receipt, if present, are separate delivery artifacts; do not distribute a signed-in browser profile.
