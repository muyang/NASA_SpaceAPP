"""Verify source workbooks, reproduce dry-mass aggregation and retain later soy rows for review."""
from pathlib import Path
import pandas as pd
import numpy as np
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1];R=ROOT/'raw/marsden';P=ROOT/'processed'
checks=[]
def check(name,ok,detail=''):
 checks.append({'check':name,'passed':bool(ok),'detail':detail})
 if not ok:raise ValueError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in json.loads((ROOT/'marsden_acquisition.json').read_text()):
 p=ROOT/'raw'/x['file'];b=p.read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 check('Pinned Git blob '+p.name,actual==x['git_blob_sha'])
raw=pd.read_excel(R/'Corn yield 2002-2020.xlsx');raw.columns=['year','block','plot','plot_side','rotation_years','herbicide_regime','yield_bu_ac_155_source','yield_Mg_ha_155_source']
check('384 raw corn subplot/full-plot records',len(raw)==384)
check('No duplicate raw corn year/plot/side records',not raw.duplicated(['year','plot','plot_side']).any())
group=raw.groupby(['year','block','plot','rotation_years'],as_index=False).agg(mean_standard_Mg_ha=('yield_Mg_ha_155_source','mean'),source_bu_ac=('yield_bu_ac_155_source','mean'),source_subplots=('plot_side','count'))
group['reconstructed_dry_Mg_ha']=group.mean_standard_Mg_ha*.845
old=pd.read_csv(REPO/'case-study/boone-v2/processed/marsden_corn_yield_clean.csv');old['rotation_years']=old.rot_trt.str[0].astype(int);old['block']=old.block.str[1:].astype(int)
j=group.merge(old[['year','block','plot','rotation_years','yield_Mgha']],on=['year','block','plot','rotation_years'],validate='one_to_one',how='outer',indicator=True)
check('All 228 author-processed corn plot years reproduce from raw workbook',j._merge.eq('both').all() and len(j)==228)
err=float((j.reconstructed_dry_Mg_ha-j.yield_Mgha).abs().max());check('Dry-mass aggregation agrees numerically',err<1e-7,f'max absolute error {err:.3g} Mg/ha')
ratios=raw.yield_Mg_ha_155_source/raw.yield_bu_ac_155_source
check('Raw workbook uses its own near-constant mass conversion',np.allclose(ratios,.06271,atol=2e-7))
raw['native_mass_conversion_Mg_ha_per_bu_ac']=ratios
raw.to_csv(P/'corn_raw_subplots_audited.csv',index=False)
group.to_csv(P/'corn_raw_aggregation_audited.csv',index=False)
rows=[];notes=[]
for year in [2018,2019,2020]:
 p=next(R.glob(f'Marsden {year} Corn-Soybean Yields*.xlsx'))
 sheet=pd.read_excel(p,sheet_name='Soybean',header=None)
 header=next(i for i,row in sheet.iterrows() if str(row.iloc[0]).strip()=='Plot' and 'Rotation' in row.values)
 for i,row in sheet.iloc[:header].iterrows():
  for value in row:
   if isinstance(value,str) and value.strip():notes.append({'year':year,'source_row':i+1,'note':value.strip()})
 data=sheet.iloc[header+1:].copy();names=sheet.iloc[header].tolist();names=[str(x).strip() if pd.notna(x) else 'unnamed_'+str(i) for i,x in enumerate(names)];data.columns=names
 data['Plot']=data.Plot.ffill();data['Rotation']=data.Rotation.ffill()
 for i,row in data.iterrows():
  rot=str(row.get('Rotation',''));treat=str(row.get('Treatment','')).strip().lower()
  if not re.fullmatch(r'S[234]',rot) or treat not in ['conv.','low','conv','conventional']:continue
  if not isinstance(row.get('Yield (bu/acre @ 13%)'),(float,int)):continue
  plot_text=str(row['Plot']);plot=int(re.sub(r'[^0-9]','',plot_text.split('.')[0]))
  weight=float(row['Harvested Weight (lbs.)']);moist=float(row['% Moisture']);area=float(row['Harvest strip area (acres)']);yield13=float(row['Yield (bu/acre @ 13%)'])
  derived=weight*(1-moist/100)/.87/area/60
  check(f'Soy {year} row {i+1} harvest mass/area/moisture reconstruction',abs(yield13-derived)<1e-6)
  rows.append({'year':year,'plot':plot,'block':plot//10,'rotation_years':int(rot[1]),'historical_subdivision_label':treat,'harvested_weight_lb':weight,'harvest_moisture_pct':moist,'harvest_area_ac':area,'reported_yield_bu_ac_13':yield13,'reconstructed_yield_bu_ac_13':derived,'source_file':str(p.relative_to(REPO)),'source_row':i+1,'plot_footnote_marker':'*' in plot_text,'analysis_admission':'quarantined_from_primary_backtest; whole-plot management note says 2018 in later workbooks too'})
later=pd.DataFrame(rows);check('72 later soybean harvested subdivisions (24 per year)',len(later)==72 and later.groupby('year').size().eq(24).all())
later.to_csv(P/'soy_2018_2020_harvest_subdivisions_for_review.csv',index=False)
pd.DataFrame(notes).to_csv(P/'later_soy_workbook_notes.csv',index=False)
management=pd.read_excel(R/'Split plot management_2008-2020.xlsx',header=None)
check('Split management has distinct hybrid/herbicide columns',management.astype(str).apply(lambda c:c.str.contains('Low herbicide',case=False)).any().any())
(P/'workbook_audit_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(P/'workbook_audit_summary.json').write_text(json.dumps({'checks_passed':len(checks),'corn_raw_rows':384,'corn_reproduced_plot_years':228,'max_dry_mass_reconstruction_error_Mg_ha':err,'raw_corn_bu_mass_conversion':.06271,'analysis_declared_corn_conversion':.06277,'conversion_note':'Historical workbook rounded conversion differs from the declared standard by about 0.096%; primary protocol remains unchanged and results are expressed from standardized mass. Do not silently relabel those as verbatim source bushels.','additional_soy_harvest_subdivision_rows':72,'additional_soy_admission':'Not fitted or included in the frozen primary backtest. Later workbooks retain a note naming 2018 for no herbicide split; clarify true later-year management and field flags first.','complete_process_input_gate':False},indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'corn_plot_years_reproduced':228,'later_soy_rows_audited_not_fitted':len(later),'max_dry_error':err},indent=2))
