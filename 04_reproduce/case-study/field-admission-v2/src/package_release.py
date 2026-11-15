"""Package an offline, minimal research release without caches, credentials or invented data."""
from pathlib import Path
import json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];O=REPO/'outputs/field-admission-v2'
def main():
 files={}
 def add(p):
  p=Path(p)
  if p.is_file():files[str(p.relative_to(REPO))]=p
 for p in R.rglob('*'):
  if 'target' not in p.parts and '__pycache__' not in p.parts:add(p)
 for path in ['case-study/boone-v2/processed/marsden_soil_water_gravimetric.csv','case-study/boone-v2/processed/marsden_corn_yield_clean.csv',
  'case-study/boone-v2/raw/marsden/data-raw/will_soilh2o/raw_soilH2O13-14.csv',
  'case-study/boone-v2/raw/marsden/data-raw/yields/mrs_cornylds.csv',
  'case-study/boone-v2/raw/marsden/data-raw/plotkey/plotkey.csv',
  'case-study/boone-v2/raw/marsden/LICENSE.md',
  'case-study/boone-long-history/processed/weather_features_daily_1984_2025.csv',
  'case-study/boone-long-history/sources.json','case-study/boone-long-history/protocol.json',
  'fieldshift-rs/baseline-revision/v0.2/inputs/crops.csv',
  'fieldshift-eo-rs/Cargo.toml','fieldshift-eo-rs/Cargo.lock','fieldshift-eo-rs/LICENSE']:
  p=REPO/path;assert p.exists(),p;add(p)
 for p in (REPO/'fieldshift-eo-rs/src').glob('*.rs'):add(p)
 for p in O.glob('*.md'):add(p)
 for p in O.glob('*.json'):
  if p.name not in ['release_manifest.json','archive_receipt.json','reproduction_verification.json']:add(p)
 for name in ['records-browser-results.json','evidence-browser-results.json','browser-results.json','records-desktop.png','records-mobile.png']:
  p=REPO/'sites/field-shift-farmer-planner/tests/artifacts'/name
  if p.exists():add(p)
 assert not any('.git/' in x or '/target/' in x or '/.toolchains/' in x for x in files)
 manifest={'release':'Field_Records_Validation_v2','scientific_scope':'Diagnostic replay and conditional historical economics; no operational recommendation','files':[{'path':k,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in sorted(files.items())]}
 (O/'release_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 archive=O/'Field_Records_Validation_v2.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for path,p in sorted(files.items()):z.write(p,path)
  z.write(O/'release_manifest.json','release_manifest.json')
 receipt={'archive':str(archive.relative_to(REPO)),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifest_file_count':len(files),'zip_file_count':len(files)+1,'cache_or_credentials_included':False}
 (O/'archive_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
