"""Extract the release, verify every file, and rerun the offline pipeline separately."""
from pathlib import Path
import hashlib,json,zipfile,tempfile,subprocess,sys,os
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];O=REPO/'outputs/field-admission-v2'
def main():
 dest=Path(tempfile.mkdtemp(prefix='field-admission-v2-reproduce-'))
 with zipfile.ZipFile(O/'Field_Records_Validation_v2.zip') as z:
  assert all(not Path(x).is_absolute() and '..' not in Path(x).parts for x in z.namelist())
  z.extractall(dest)
 manifest=json.loads((dest/'release_manifest.json').read_text())
 for x in manifest['files']:assert hashlib.sha256((dest/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
 env=os.environ.copy();tools=REPO/'.toolchains'
 if (tools/'cargo/bin/cargo').exists():
  env.update(FIELD_SHIFT_CARGO=str(tools/'cargo/bin/cargo'),RUSTUP_HOME=str(tools/'rustup'),CARGO_HOME=str(tools/'cargo'))
  env['PATH']=str(tools/'cargo/bin')+os.pathsep+env['PATH']
 steps=['audit_management','audit_hydraulics','analyze_economics','run_field_replay','evaluate_replay','verify_admission','build_deliverables'];results=[];logs=[]
 for name in steps:
  p=subprocess.run([sys.executable,str(dest/'case-study/field-admission-v2/src'/f'{name}.py')],cwd=dest,env=env,text=True,capture_output=True)
  logs.append(name+'\n'+p.stdout+p.stderr);results.append({'step':name,'exit_code':p.returncode})
  if p.returncode:
   (O/'reproduction_log.txt').write_text('\n'.join(logs));raise RuntimeError(name+' failed: '+p.stderr[-2000:])
 old=pd.read_csv(R/'replay_results/annual.csv');new=pd.read_csv(dest/'case-study/field-admission-v2/replay_results/annual.csv')
 np.testing.assert_allclose(old,new,rtol=1e-10,atol=1e-8)
 oldw=pd.read_csv(R/'processed/field_replay_water_metrics.csv');neww=pd.read_csv(dest/'case-study/field-admission-v2/processed/field_replay_water_metrics.csv')
 np.testing.assert_allclose(oldw.select_dtypes('number'),neww.select_dtypes('number'),rtol=1e-10,atol=1e-8)
 receipt={'extracted_directory':str(dest),'manifest_files_verified':len(manifest['files']),'offline_steps':results,'independently_rebuilt_and_executed':True,'annual_output_matches_at_1e_8_absolute_tolerance':True,'water_scores_match':True,'scope':'Separate extracted-copy execution; reproducibility, not independent agronomic validation'}
 (O/'reproduction_log.txt').write_text('\n'.join(logs));(O/'reproduction_verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
