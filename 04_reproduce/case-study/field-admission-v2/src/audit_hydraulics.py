"""Admit measured soil profiles, provide clearly separated retention priors and conditional joins."""
from pathlib import Path
import pandas as pd,numpy as np,json,math
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];P=R/'processed'
def retention_prior(sand,clay,om):
 # Saxton & Rawls (2006) texture/OM equations; OM is percent, sand/clay fractions.
 s,c=sand/100,clay/100
 a=-.024*s+.487*c+.006*om+.005*s*om-.013*c*om+.068*s*c+.031
 ll=a+(.14*a-.02)
 b=-.251*s+.195*c+.011*om+.006*s*om-.027*c*om+.452*s*c+.299
 fc=b+(1.283*b*b-.374*b-.015)
 e=.278*s+.034*c+.022*om-.018*s*om-.027*c*om-.584*s*c+.078
 sat=fc+(e+.636*e-.107)-.097*s+.043
 return ll,fc,sat
def main():
 raw=pd.read_csv(R/'raw/soiltexture/rd_texture2014.csv')
 d=raw[raw.site.eq('mars')&raw.year.eq(2014)].copy()
 assert len(d)==40 and not d.duplicated(['year','plot','depth_cm']).any()
 depth=d.depth_cm.str.split('-',expand=True).astype(float);d['top_cm']=depth[0];d['bottom_cm']=depth[1]
 d['BD_from_mass_volume_g_cm3']=d.drywt_g/d.voladj_cm3;d['BD_rounding_difference']=d['bulkden_g.cm3']-d.BD_from_mass_volume_g_cm3
 assert abs(d.BD_rounding_difference).max()<.01
 assert abs(d.sand_prct+d.silt_prct+d.clay_prct-100).max()<.05
 d['measured_parameter_support']='reported 2014 Marsden cores; laboratory texture and core dry bulk density; exact sample date not supplied in this CSV'
 d.to_csv(P/'measured_2014_soil_layers.csv',index=False)
 priors=[]
 for _,x in d.iterrows():
  for oc_om in [.58,.50]:
   om=x.SOCfinal_prct/oc_om;ll,fc,sat=retention_prior(x.sand_prct,x.clay_prct,om);phi=1-x['bulkden_g.cm3']/2.65
   # No clipping invalid retention estimates into an apparently valid measured profile.
   valid=0<ll<fc<phi<1
   priors.append({'year':2014,'plot':int(x['plot']),'block':int(x.block),'rotation_years':int(x.rot),'top_cm':x.top_cm,'bottom_cm':x.bottom_cm,'BD_measured_g_cm3':x['bulkden_g.cm3'],'SOC_measured_pct':x.SOCfinal_prct,'OC_OM_assumed_ratio':oc_om,'OM_estimated_pct':om,'LL15_PTF_m3_m3':ll,'DUL33_PTF_m3_m3':fc,'SAT_PTF_normal_density_m3_m3':sat,'SAT_BD_porosity_proxy_m3_m3':phi,'retention_prior_physically_admissible':valid,'layer_PAW_prior_mm':(fc-ll)*(x.bottom_cm-x.top_cm)*10 if valid else np.nan,'status':'estimated_prior_not_measured_retention','limitations':'PTF normal-density FC is not density-adjusted; porosity uses assumed particle density 2.65; no measured Ksat or initial-date water; invalid layers remain rejected'})
 pr=pd.DataFrame(priors);pr.to_csv(P/'hydraulic_parameter_priors.csv',index=False)
 profiles=pr.groupby(['plot','rotation_years','OC_OM_assumed_ratio'],as_index=False).agg(n_layers=('top_cm','count'),max_depth_cm=('bottom_cm','max'),all_layers_valid=('retention_prior_physically_admissible','all'),PAW_sum_valid_layers_mm=('layer_PAW_prior_mm',lambda s:s.sum(min_count=len(s))))
 profiles.to_csv(P/'hydraulic_profile_admission.csv',index=False)
 # Conditional g/g -> volume conversion for the same 2014 plot. Source layers differ.
 obs=pd.read_csv(REPO/'case-study/boone-v2/processed/marsden_soil_water_gravimetric.csv');obs['date']=pd.to_datetime(obs.date)
 results=[]
 for _,o in obs.iterrows():
  if int(o.year)!=2014 or o.date.year!=2014:continue
  layers=d[d['plot'].eq(o['plot'])]
  if len(layers)!=5:continue
  a=float(layers[layers.top_cm.eq(0)]['bulkden_g.cm3'].iloc[0]);b=float(layers[layers.top_cm.eq(15)]['bulkden_g.cm3'].iloc[0])
  for top,bottom,col,bd in [(0,10,'0-10cm_soilH2O_g.g',a),(10,30,'10-30cm_soilH2O_g.g',(.05*a+.15*b)/.20)]:
   g=float(o[col]);v=g*bd
   results.append({'date':o.date.date().isoformat(),'year':2014,'plot':int(o['plot']),'system':int(o.system),'top_cm':top,'bottom_cm':bottom,'gravimetric_g_g':g,'effective_BD_g_cm3':bd,'conditional_VWC_m3_m3':v,'conditional_storage_mm':v*(bottom-top)*10,'status':'conditional_conversion_with_depth_mapping','assumptions':'g/g dry-soil-mass basis presumed from label; uniform BD within 0-15 and 15-30 cm; exact core sampling date unavailable; not a direct VWC measurement','aggregate_0_30_used':False})
 converted=pd.DataFrame(results);converted.to_csv(P/'soil_water_2014_conditional_volume.csv',index=False)
 # Published all-system paired BD/WFPS values are separate from the 2014 profiles.
 soil=pd.read_csv(R/'raw/papers/root_soil_data_s1.csv',na_values=['.']);soil=soil.drop(columns=[c for c in soil if c.startswith('Unnamed') or c.startswith('/*')]);soil['top_cm']=soil.depth;soil['bottom_cm']=soil.depth+10
 soil['sampling_period']=soil.date.map({1:'fall_2008',2:'spring_2009',3:'summer_2009',4:'fall_2009',5:'spring_2010'})
 soil.to_csv(P/'published_2008_2010_soil_observations.csv',index=False)
 dates={2:2009,3:2009,4:2009,5:2010};summary=[]
 for (system,period,top),g in soil.groupby(['system','sampling_period','top_cm']):
  summary.append({'system':int(system),'sampling_period':period,'top_cm':int(top),'bottom_cm':int(top)+10,'rows':len(g),'BD_observed_n':int(g.bulk_density.notna().sum()),'BD_mean_g_cm3':g.bulk_density.mean(),'WFPS_observed_n':int(g.WFPS.notna().sum()),'WFPS_mean_pct':g.WFPS.mean(),'warning':'WFPS is a derived state indicator, not water retention/ET/irrigation saving. Sampling season is not an exact day.'})
 pd.DataFrame(summary).to_csv(P/'published_soil_state_summary.csv',index=False)
 sensor=R/'raw/soilsensors/rd_mars-soil_sensor-install.xlsx'
 s=pd.read_excel(sensor,header=5);s=s[s.block.astype(str).str.match('B[1-4]')].copy()
 s.to_csv(P/'sensor_dry_sat_readings_not_soil_retention.csv',index=False)
 result={'measured_layers':40,'complete_measured_BD_texture_SOC_profiles_0_100cm':8,'represented_rotations':[2,4],'all_system_shallow_soil_rows':360,'BD_WFPS_nonmissing_pairs':int(soil[['bulk_density','WFPS']].notna().all(axis=1).sum()),'conditional_2014_water_layer_records':len(converted),'PTF_candidates':len(pr),'PTF_candidates_rejected':int((~pr.retention_prior_physically_admissible).sum()),'profiles_all_prior_layers_physical':int(profiles.all_layers_valid.sum()),'retention_measured':False,'initial_state_date_verified':False,'sensor_sat_not_admitted_as_soil_SAT':True,'limitations':['The 2014 deep profile dataset covers 2- and 4-year corn phases only, not 3-year.','2013 water is not silently paired with 2014 BD.','0-30 cm aggregate is not used due prior unresolved support.','LL/DUL and SAT priors are estimates; no synthetic measurement or clipping.','2018 sensor dry_VWC/sat_VWC are installation calibration readings, not an admitted field retention curve.']}
 (P/'hydraulic_audit_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
