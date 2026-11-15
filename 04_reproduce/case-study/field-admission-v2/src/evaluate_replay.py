from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];P=R/'processed';O=R/'replay_results'
def metrics(obs,pred):
 e=np.asarray(pred)-np.asarray(obs);return {'RMSE':float(np.sqrt(np.mean(e*e))),'MAE':float(abs(e).mean()),'bias':float(e.mean())}
def main():
 a=pd.read_csv(O/'annual.csv');d=pd.read_csv(O/'daily.csv');s=json.loads((O/'execution_status.json').read_text());assert s['runs']==32
 assert a.fertilizer_N_kg_ha.sub(150*1.120851156).abs().max()<1e-7
 assert a.water_error_mm.abs().max()<1e-6 and a.C_error_kg_ha.abs().max()<1e-5 and a.N_error_kg_ha.abs().max()<1e-6
 obs=pd.read_csv(REPO/'case-study/boone-v2/processed/marsden_corn_yield_clean.csv');obs=obs[obs.year.eq(2014)&obs.rot_trt.eq('2y')]
 obs=obs[['plot','yield_Mgha']].rename(columns={'yield_Mgha':'observed_dry_Mg_ha'});obs['observed_bu_ac_155']=obs.observed_dry_Mg_ha/.845/.06277
 j=a.merge(obs,on='plot',validate='many_to_one');j['predicted_bu_ac_155']=j.corn_yield_dry_kg_ha/1000/.845/.06277;j.to_csv(P/'field_replay_yield_pairs.csv',index=False)
 ym=[]
 for (ratio,fraction),g in j.groupby(['OC_OM','initial_fraction']):ym.append({'OC_OM':ratio,'initial_fraction':fraction,'plots':len(g),'observed_mean_bu_ac':g.observed_bu_ac_155.mean(),'predicted_mean_bu_ac':g.predicted_bu_ac_155.mean(),**metrics(g.observed_bu_ac_155,g.predicted_bu_ac_155)})
 ym=pd.DataFrame(ym);ym.to_csv(P/'field_replay_yield_metrics.csv',index=False)
 water=pd.read_csv(P/'soil_water_2014_conditional_volume.csv');water=water[water.system.eq(2)];water['date']=pd.to_datetime(water.date);water['doy']=water.date.dt.dayofyear
 obs_water=water.groupby(['plot','date','doy'],as_index=False).agg(observed_storage_0_300_mm=('conditional_storage_mm','sum'),n_layers=('top_cm','count'));assert obs_water.n_layers.eq(2).all()
 w=d.merge(obs_water,on=['plot','doy'],validate='many_to_one',how='inner');w.to_csv(P/'field_replay_conditional_water_pairs.csv',index=False)
 wm=[]
 for (ratio,fraction),g in w.groupby(['OC_OM','initial_fraction']):wm.append({'OC_OM':ratio,'initial_fraction':fraction,'matched_plot_dates':len(g),'unit':'mm in 0-300 mm; conditional g/g/BD conversion',**metrics(g.observed_storage_0_300_mm,g.water_0_300_mm)})
 wm=pd.DataFrame(wm);wm.to_csv(P/'field_replay_water_metrics.csv',index=False)
 baseline=obs_water.copy();baseline['same_period_plot_mean']=baseline.groupby('plot').observed_storage_0_300_mm.transform('mean');base=metrics(baseline.observed_storage_0_300_mm,baseline.same_period_plot_mean)
 result={'scope':'source-driven field diagnostic, no newly fitted crop or hydraulic coefficients','runs':32,'corn_plot_years':4,'same_weather_years':1,'conditional_water_plot_dates':len(obs_water),'year':2014,'yield_RMSE_bu_ac_range':[float(ym.RMSE.min()),float(ym.RMSE.max())],'yield_bias_bu_ac_range':[float(ym.bias.min()),float(ym.bias.max())],'observed_corn_mean_bu_ac':float(ym.observed_mean_bu_ac.iloc[0]),'predicted_corn_mean_bu_ac_range':[float(ym.predicted_mean_bu_ac.min()),float(ym.predicted_mean_bu_ac.max())],'water_RMSE_mm_range':[float(wm.RMSE.min()),float(wm.RMSE.max())],'water_bias_mm_range':[float(wm.bias.min()),float(wm.bias.max())],'same_period_plot_mean_water_in_sample_baseline':base,'mass_balances_passed':True,'range_is_confidence_interval':False,'field_model_validated':False,'reasons':['Initial state date, mineral N and residue conditions not verified; organic stocks are a 2014-to-January proxy.','PTF retention is estimated, not a measured retention curve; conditional water depth mapping remains.','Single year, four repeated blocks, regional weather; this is not independent multi-year climate validation.','Source seeding rate, hybrid, tillage, P/K, incidental spray N, pests and tile/water-table processes are not all represented in the reduced model.','This diagnostic does not validate rye, clover, oat or cross-strategy economic effects.']}
 (P/'field_replay_evaluation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
