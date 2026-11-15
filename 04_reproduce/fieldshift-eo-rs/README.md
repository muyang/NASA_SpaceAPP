# FieldShift EO experiments 0.3.0

Independent reduced crop model; not APSIM. This opt-in experimental fork preserves the original `fieldshift-rs` source and default numerical behavior when new switches are off.

New baseline-only switches:

- `--use-reference-et`: strict daily `atmosphere.csv` input, `year,doy,reference_ET0_mm`; dates must exactly match weather and finite values must be 0–25 mm/day. This replaces the old atmospheric demand proxy. Canopy demand remains a reduced partition, not a complete FAO dual-Kc model.
- `--organic-mulch`: replace exponentially vanishing potential soil evaporation with `1 - 0.5 * residue_cover`, using FAO56's approximate organic-mulch guidance. The cover estimate itself is still uncalibrated and may remain too high. Frozen soil, snow and hydraulic redistribution are not added.
- `--dynamic-fixation`: request soil mineral N first, then cap remaining fixation by crop maximum fraction, relative water supply, an emergence ramp to progress 0.2 and a decline over progress 0.85–1.05. These stage coefficients are assumptions; no nodule/carbon-cost model or locally observed seasonal Ndfa calibration is claimed.

Each switch requires `--calibration`, restricting the new features to the corn–soybean baseline. Fertilizer, initial survey soil stocks, RUE and maturity coefficients are unchanged in the 16-way experimental comparison. Default switches off preserve v0.2 baseline numerical output.

`canopy_daily.csv` is a diagnostic trace for both starting phases on the first representative soil and initial-water fraction 0.4; it is not every scenario or a measured field. The full annual output and water/C/N ledgers remain the authoritative ensemble outputs. Tests include strict ET0 dates/units, bounded mulch/fixation responses, mineral-N suppression of fixation and conservation.

Study methods, status, sources, data and reproduction instructions are in `../case-study/boone-eo-constraints/README.md`. No operational rotation recommendation is released.
