# Public field validation release 1

This release verifies **observed historic trial outcomes and a fixed statistical contrast benchmark**, not the Rust or APSIM process model. Human usability testing is not conducted: no participants are currently available.

## Reproduce inside the original NASA workspace

Use the bundled Python environment with numpy, pandas, openpyxl, pdfplumber and python-docx. No source repository R code is executed.

```sh
python3 case-study/public-field-validation/src/fetch_public_trials.py
python3 case-study/public-field-validation/src/audit_workbooks.py
python3 case-study/public-field-validation/src/analyze_trials.py
```

Acquisition stores source URLs, timestamps, SHA-256 and (for pinned author files) Git blob hashes. The GitHub raw file host failed in this session; acquisition succeeded using the official contents API and decoded files matched the pinned Git blobs. Failed CSCAP landing/API attempts remain recorded. No email forms were submitted and no researchers, buyers or farmers were contacted.

The analysis reads the retained v2 standardized extracts and verifies corn against its raw workbook in the audit. `analysis_protocol.json` freezes the 2006–2011 training / 2012–2017 held-out primary comparison before its scores were calculated. The portable bundle includes the minimum original source / v2 extracts required by the scripts and their license.

## Data admission

- **Marsden:** raw corn harvest summary workbook, split management, processed plot-year / soybean records, historical methods / seeding / nutrient material and later 2018–2020 harvest records. The corn dry-mass table reproduces from 384 raw full/subplot rows to 228 plot years. The primary paired subset has 192 crop-system-year-block observations and 96 pairs.
- **PFI:** published treatment means, LSD / significance labels, management and qualitative soil-water summaries for five farms in 2022. Not raw strip yields. Three management-date conflicts, one conclusion inconsistency and two sensor failures are retained.
- **CSCAP:** a promising multi-site catalog advertises yield, operations, soil and weather records; the data portal requests email submission and retrieved repository landing pages were empty. The public Figshare search returned HTTP 403. No complete CSCAP data were acquired; catalog coverage is not counted as downloaded data.
- **Human testing:** an actual facilitator instrument, blank forms and analysis software. Rehearsals do not count as participants or farmer findings.

## Limits that remain

The primary crop-phase contrasts compare management systems, including differences in manure / fertilizer / herbicide / cultivar history and author aggregation of corn subplots. They do not isolate clover or sequence causality. Six-year mean effects and year bootstrap intervals condition on one experiment and its four blocks; they do not establish cross-farm predictive uncertainty.

Corn author outputs are dry Mg/ha. This release divides by 0.845 for 15.5% moisture, then uses the declared 0.06277 mass-to-bushel conversion. The raw historic workbook uses a rounded 0.06271 conversion; source bushels differ by about 0.096%. This small convention difference is recorded rather than silently changing the frozen protocol. Soybean values retain 13% moisture and the source 0.06719 conversion.

Later soybean harvest records (72 subdivisions) pass harvest-weight / area / moisture checks, but are not admitted to the frozen primary backtest. Notes in the 2019 / 2020 workbooks still name 2018 when describing herbicide management, and one plot has an altered sampling width. Resolve those metadata before treating the extra rows as comparable management trials.

No site currently closes every required field-process / economics gate: verified layer hydraulic state, all dated nutrient / water events, complete oat/clover crop outputs, delivered incremental costs and a real current market contract are not all available together. Consequently no unsupported field forecast, ET / irrigation saving, full CBA or MCA ranking is released. Published historic economic results retain the original exclusions and manure assumptions.
