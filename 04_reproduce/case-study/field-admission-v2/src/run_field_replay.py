"""Build a separate event-driven diagnostic; preserve legacy sources and parameters."""
from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,os,subprocess,shutil,time
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];I=R/'replay_inputs';O=R/'replay_results';P=R/'processed'
def main():
 I.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
 d=pd.read_csv(P/'hydraulic_parameter_priors.csv');d=d[d.rotation_years.eq(2)]
 measured=pd.read_csv(P/'measured_2014_soil_layers.csv');inputs=[]
 for (plot,ratio),g in d.groupby(['plot','OC_OM_assumed_ratio']):
  assert len(g)==5 and g.retention_prior_physically_admissible.all()
  row={'plot':int(plot),'OC_OM':ratio}
  for k,(top,bottom) in enumerate([(0,15),(15,45),(45,100)],1):
   overlaps=np.maximum(0,np.minimum(g.bottom_cm,bottom)-np.maximum(g.top_cm,top))
   row['cap'+str(k)]=float(((g.DUL33_PTF_m3_m3-g.LL15_PTF_m3_m3)*overlaps*10).sum());row['ll'+str(k)]=float((g.LL15_PTF_m3_m3*overlaps).sum()/(bottom-top))
  m=measured[measured['plot'].eq(plot)];th=m.bottom_cm-m.top_cm
  row['somc']=float((m.SOCfinal_prct*m['bulkden_g.cm3']*th*1000).sum());row['somn']=float((m.Ntotfinal_prct*m['bulkden_g.cm3']*th*1000).sum());inputs.append(row)
 pd.DataFrame(inputs)[['plot','OC_OM','cap1','cap2','cap3','ll1','ll2','ll3','somc','somn']].to_csv(I/'soils.csv',index=False)
 w=pd.read_csv(REPO/'case-study/boone-long-history/processed/weather_features_daily_1984_2025.csv');w=w[w.year.eq(2014)];assert len(w)==365
 w[['year','doy','tmin_c','tmax_c','rain_mm','solar_MJ_m2','ET0_FAO56_approx_mm']].to_csv(I/'weather.csv',index=False)
 pd.DataFrame([[111,'fertilize_N',100*1.120851156],[112,'sow',0],[162,'fertilize_N',50*1.120851156],[279,'harvest',0]],columns=['doy','event','amount_kg_N_ha']).to_csv(I/'events.csv',index=False)
 # Confirm calendar dates against source protocol rather than rely on hard-coded day mistakes.
 import datetime
 assert [datetime.date(2014,1,1)+datetime.timedelta(days=x-1) for x in [111,112,162,279]]==[datetime.date(2014,4,21),datetime.date(2014,4,22),datetime.date(2014,6,11),datetime.date(2014,10,6)]
 shutil.copy(REPO/'fieldshift-rs/baseline-revision/v0.2/inputs/crops.csv',I/'crops.csv')
 env=os.environ.copy();tools=REPO/'.toolchains';local_cargo=tools/'cargo/bin/cargo'
 if local_cargo.exists():
  env.update(RUSTUP_HOME=str(tools/'rustup'),CARGO_HOME=str(tools/'cargo'));env['PATH']=str(tools/'cargo/bin')+os.pathsep+env['PATH']
 cargo=env.get('FIELD_SHIFT_CARGO') or (str(local_cargo) if local_cargo.exists() else shutil.which('cargo'))
 assert cargo,'Install a Rust toolchain, or set FIELD_SHIFT_CARGO to its cargo executable.'
 sdk=Path('/Volumes/mac/Library/Developer/CommandLineTools')
 if sdk.exists():env.update(DEVELOPER_DIR=str(sdk),SDKROOT=str(sdk/'SDKs/MacOSX.sdk'),CARGO_TARGET_X86_64_APPLE_DARWIN_LINKER=str(sdk/'usr/bin/clang'))
 cmd=[cargo,'build','--release','--offline'];p=subprocess.run(cmd,cwd=R/'rust',env=env,capture_output=True,text=True);(O/'build.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 binary=R/'rust/target/release/fieldshift-field-replay';p=subprocess.run([str(binary),str(I),str(O)],capture_output=True,text=True);(O/'run.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 (O/'receipt.json').write_text(json.dumps({'command':cmd,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'source_sha256':{str(f.relative_to(REPO)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [R/'rust/src/main.rs',REPO/'fieldshift-eo-rs/src/lib.rs',R/'field_replay_protocol.json']},'input_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in I.glob('*.csv')},'note':'Measured 2014 organic stocks used as start-year proxy. Retention priors, model processes, mineral N, residues and unknown initial water remain explicit diagnostic assumptions.'},indent=2)+'\n');print(p.stdout)
if __name__=='__main__':main()
