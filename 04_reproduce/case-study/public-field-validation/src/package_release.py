"""Package reproducible factual extracts and tools. Prior releases remain unchanged."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1];OUT=REPO/'outputs/public-field-validation'
files=[]
for base in [ROOT,REPO/'farmer-testing',REPO/'sites/field-shift-farmer-planner/dist']:
 for p in base.rglob('*'):
  if not p.is_file() or any(x in p.parts for x in ['__pycache__','sessions','.openai']):continue
  if p.name.endswith('.api.json') or p.suffix.lower() in ['.png','.pyc']:continue
  if p.name in ['pfi_soil_water_2022.pdf','pfi_soil_water_page.html']:continue
  if p.stat().st_size==0:continue
  files.append(p)
for rel in [
 'case-study/boone-v2/processed/marsden_corn_yield_clean.csv',
 'case-study/boone-v2/processed/marsden_soy_yield_clean.csv',
 'case-study/boone-v2/raw/marsden/LICENSE.md',
 'case-study/boone-v2/raw/marsden/data-raw/yields/mrs_cornylds.csv',
 'case-study/boone-v2/raw/marsden/data-raw/yields/raw/rd_soyyld_2003-17.csv',
 'case-study/boone-v2/raw/marsden/data-raw/plotkey/plotkey.csv',
 'case-study/boone-v2/raw/marsden/data-raw/apsim_mgmt/Marsden-activites-for-apsim.xlsx',
 'case-study/boone-v2/raw/marsden/data-raw/yields/raw/raw-from-ML/Fert & Manure NPK 2003-20.xlsx',
 'case-study/boone-v2/raw/marsden_2012_methods.docx',
 'case-study/boone-v2/raw/marsden_2012_nutrients.docx',
 'case-study/boone-v2/raw/marsden_2012_seeding.docx',
 'case-study/boone-v2/raw/marsden_article.html',
 'case-study/boone-v2/repository_selection.json',
 'case-study/boone-v2/sources.json',
 'case-study/boone-cn-weather-audit/processed/weather_exposure_screens.csv',
 'outputs/farmer-centered-app/Farmer_Usability_Test_Protocol_CN.md',
 'outputs/public-field-validation/Public_Field_Validation_Report_CN.md',
 'outputs/public-field-validation/Data_Admission_and_Next_Gates_CN.md',
 'outputs/public-field-validation/Release_Notes_CN.md',
 'outputs/public-field-validation/human_test_status.json',
 'outputs/public-field-validation/rehearsal_exclusion_check.json',
 'sites/field-shift-farmer-planner/README.md',
 'sites/field-shift-farmer-planner/tests/evidence.test.mjs',
 'sites/field-shift-farmer-planner/tests/domain.test.mjs',
 'sites/field-shift-farmer-planner/tests/browser.test.mjs',
 'sites/field-shift-farmer-planner/tests/evidence-browser.test.mjs',
 'sites/field-shift-farmer-planner/tests/all-browser.test.mjs',
 'sites/field-shift-farmer-planner/tests/artifacts/browser-results.json',
 'sites/field-shift-farmer-planner/tests/artifacts/evidence-browser-results.json'
]:files.append(REPO/rel)
files=sorted(set(files));assert all(p.exists() for p in files)
manifest={'version':'public-field-validation-1','files':[{'path':str(p.relative_to(REPO)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],'original_reports_not_redistributed':['PFI full report and webpage: fetch from the recorded original URLs if needed. The verified factual transcription and source hashes are included.'],'human_participants':0,'scope':'Observed public outcome validation; no process model validation or farmer-specific recommendation'}
readme='''# Field Shift public trial validation + farmer test kit

This package contains real public trial extracts, raw author workbooks, a frozen analysis protocol, reproducible audits and a browser-local app. Human participants: 0. Rehearsal tests are not farmer findings.

From the extracted root, use Python 3.12+ with the pinned requirements:

    python3 -m pip install -r case-study/public-field-validation/requirements.txt
    python3 case-study/public-field-validation/src/audit_workbooks.py
    python3 case-study/public-field-validation/src/analyze_trials.py

No network is needed for these two analysis commands. Do not execute downloaded author R scripts. They are retained for unit and transformation inspection only. Original PFI report text/graphics are not redistributed; the verified factual extraction, source URL and checksum are retained. `fetch_public_trials.py` can retrieve the original report when desired.

Run the app locally:

    python3 -m http.server 8817 --bind 127.0.0.1 --directory sites/field-shift-farmer-planner/dist

Open http://127.0.0.1:8817/evidence.html for observed trials or /research-test.html for the facilitator instrument. Direct file:// opening is unsupported. Records stay on the device; no contacts or researcher messages are sent.

Read outputs/public-field-validation/Public_Field_Validation_Report_CN.md and Data_Admission_and_Next_Gates_CN.md for results and remaining gates. Start genuine farmer testing with farmer-testing/README_CN.md. Do not treat soil moisture as ET / irrigation saving, historical returns as current farm profit, or a statistical contrast benchmark as APSIM / Rust process-model validation.
'''
archive=OUT/'Field_Validation_and_Farmer_Test_Kit_v1.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(REPO))
 z.writestr('REPRODUCE.md',readme);z.writestr('release_manifest.json',json.dumps(manifest,indent=2)+'\n')
(OUT/'release_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'REPRODUCE.md').write_text(readme)
print(json.dumps({'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))
