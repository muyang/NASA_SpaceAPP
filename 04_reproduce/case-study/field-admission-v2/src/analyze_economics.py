"""Recompute historical point-estimate comparisons; never label them farmer recommendations."""
from pathlib import Path
import json,pandas as pd,numpy as np,itertools
R=Path(__file__).resolve().parents[1];P=R/'processed'
def main():
 source=json.loads((R/'published_economics_transcription.json').read_text());d=pd.DataFrame(source['rows']);d.to_csv(P/'published_crop_phase_economics.csv',index=False)
 base=[];portfolio={}
 for tech in ['GE','Non-GE']:
  for years in [2,3,4]:
   g=d[(d.rotation_years==years)&d.technology.isin([tech,'shared'])].copy()
   expected={2:{'corn','soybean'},3:{'corn','soybean','oat'},4:{'corn','soybean','oat','alfalfa'}}[years]
   assert set(g.crop)==expected and len(g)==years
   value=float(g.net_return.sum()/years);portfolio[(tech,years)]=g
   base.append({'technology':tech,'rotation_years':years,'annualized_mean_USD_ac':value,'phase_area_weight':1/years,'period':'2008–2012','scope':'Historical published economic estimate; no yield/price model or current farmer recommendation'})
 b=pd.DataFrame(base);b['point_estimate_rank_within_technology']=b.groupby('technology').annualized_mean_USD_ac.rank(ascending=False,method='min').astype(int);b.to_csv(P/'historical_financial_point_order.csv',index=False)
 scenarios=[]
 for tech in ['GE','Non-GE']:
  for dc,ds,do,da in itertools.product([-2.,0.,2.],[-4.,0.,4.],[-1.,0.,1.],[-40.,0.,40.]):
   delta={'corn':dc,'soybean':ds,'oat':do,'alfalfa':da};values=[]
   for years in [2,3,4]:
    g=portfolio[(tech,years)]
    # This is a common additive offset to each historical year's price, not replacement by a fixed new price.
    value=sum(row.net_return+row['yield']*delta[row.crop] for _,row in g.iterrows())/years
    values.append((years,value))
   order=sorted(values,key=lambda x:-x[1]);ranks={year:i+1 for i,(year,_) in enumerate(order)}
   for years,value in values:scenarios.append({'technology':tech,'corn_price_additive_offset_USD_bu':dc,'soy_price_additive_offset_USD_bu':ds,'oat_price_additive_offset_USD_bu':do,'alfalfa_price_additive_offset_USD_ton':da,'rotation_years':years,'conditional_historical_mean_USD_ac':value,'financial_point_order':ranks[years],'assumption':'No yield response, unchanged costs and outlets; arbitrary stress grid, not a forecast or probability distribution'})
 s=pd.DataFrame(scenarios);s.to_csv(P/'historical_price_stress_grid.csv',index=False)
 wins=s[s.financial_point_order==1].groupby(['technology','rotation_years']).size().rename('grid_cases_first_of_81').reset_index();wins.to_csv(P/'historical_stress_order_counts.csv',index=False)
 # Keep a cost-scope ledger, including missing items instead of zero-filled totals.
 costs=pd.read_csv(P/'recorded_seed_costs.csv')
 ledger=[]
 for item in ['seed','fertilizer','manure_material','manure_haul','application','tillage','crop_protection_material','labor','machinery_ownership','drying','storage','transport','land','insurance','finance','oat_straw','terminal_stock']:
  ledger.append({'category':item,'source_support':'2014 corn and soybean source-log seed prices' if item=='seed' else ('some total-load transport charges, field allocation missing' if item=='manure_haul' else 'not closed as a common field-year line-item ledger'),'verified_common_field_year_cost':False,'missing_cost_is_zero':False})
 pd.DataFrame(ledger).to_csv(P/'economic_scope_admission.csv',index=False)
 mixed=(323.93+110.67)/2-(495.32+172.96-17.119)/3
 summary={'published_crop_phase_rows':15,'historic_system_technology_cases':6,'additive_price_stress_cases_per_technology':81,'mean_order_GE':'2-year > 3-year > 4-year','mean_order_non_GE':'3-year > 4-year > 2-year','GE_2y_vs_nonGE_3y_difference_USD_ac_year':mixed,'ranking_scope':'Historical published point estimates within technology strata; no inferential confidence or operational recommendation','field_complete_CBA_eligible':False,'full_MCA_eligible':False,'reasons':['No field-year line-item accounts or covariance data to reconstruct full original budgets.','No current verified oat/alfalfa buyer/quality/transport contract.','No common validated water-use or soil-benefit value functions and farmer weights.','Planner rye strategy is absent from these three observed systems.','Whole-return economic definition differs from Davis 2012 return-to-land-and-management.']}
 (P/'economic_audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(b.to_string(index=False));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
