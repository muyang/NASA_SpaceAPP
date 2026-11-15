"""Reanalyze observed rotation contrasts with frozen time splits. No crop-model run."""
from pathlib import Path
import json,hashlib,shutil,math
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
P=ROOT/'processed';P.mkdir(exist_ok=True)
OUT=REPO/'outputs/public-field-validation';OUT.mkdir(exist_ok=True)
V2=REPO/'case-study/boone-v2';PROTOCOL=json.loads((ROOT/'analysis_protocol.json').read_text())
CHECKS=[]
def check(name,ok):
 CHECKS.append({'check':name,'passed':bool(ok)})
 if not ok:raise ValueError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_csv(name,d):d.to_csv(P/name,index=False,float_format='%.8f')
def boot_mean(values):
 rng=np.random.default_rng(7112026);a=np.asarray(values,float)
 q=np.quantile(rng.choice(a,(10000,len(a)),replace=True).mean(axis=1),[.025,.975])
 return [float(v) for v in q]

def analyze():
 inputs=[V2/'processed/marsden_corn_yield_clean.csv',V2/'processed/marsden_soy_yield_clean.csv',ROOT/'analysis_protocol.json',ROOT/'pfi_verified_transcription.json',ROOT/'raw/marsden/code_proc-yields.R',ROOT/'raw/marsden/Corn yield 2002-2020.xlsx',P/'workbook_audit_summary.json']
 receipt={'protocol_sha256':sha(ROOT/'analysis_protocol.json'),'sources':[{'file':str(p.relative_to(REPO)),'sha256':sha(p)} for p in inputs]}
 corn=pd.read_csv(inputs[0]);soy=pd.read_csv(inputs[1])
 check('corn source processing explicitly labels dry mass', 'DRY Mg/ha' in (ROOT/'raw/marsden/code_proc-yields.R').read_text())
 check('corn conversion uses 0.845 dry fraction', '(1-0.155)' in (ROOT/'raw/marsden/code_proc-yields.R').read_text())
 corn['crop']='corn';corn['rotation_years']=corn.rot_trt.str[0].astype(int);corn['block_number']=corn.block.str[1:].astype(int)
 corn['yield_reported_Mg_ha']=corn.yield_Mgha;corn['yield_standard_Mg_ha']=corn.yield_Mgha/.845;corn['yield_bu_ac']=corn.yield_standard_Mg_ha/.06277
 corn['source_basis']='dry mass';corn['standard_moisture_pct']=15.5
 soy['crop']='soybean';soy['block_number']=soy.block.astype(int);soy['yield_reported_Mg_ha']=soy.Mg_ha;soy['yield_standard_Mg_ha']=soy.Mg_ha;soy['yield_bu_ac']=soy.bu_ac;soy['source_basis']='13% moisture';soy['standard_moisture_pct']=13
 check('soy mass and bushel conversion reconciles',np.allclose(soy.Mg_ha,soy.bu_ac*.06719,atol=1e-8))
 cols=['crop','year','rotation_years','block_number','yield_reported_Mg_ha','source_basis','yield_standard_Mg_ha','standard_moisture_pct','yield_bu_ac']
 data=pd.concat([corn[cols],soy[cols]],ignore_index=True)
 subset=data[data.year.between(2006,2017)&data.rotation_years.isin([2,3])].copy()
 check('192 crop/system/year/block observations in primary subset',len(subset)==192)
 check('one observation per crop/year/system/block',not subset.duplicated(['crop','year','rotation_years','block_number']).any())
 check('all measurements positive and finite',np.isfinite(subset.yield_bu_ac).all() and subset.yield_bu_ac.gt(0).all())
 wide=subset.pivot(index=['crop','year','block_number'],columns='rotation_years',values='yield_bu_ac').reset_index().rename(columns={2:'baseline_2y_bu_ac',3:'diversified_3y_bu_ac'})
 check('96 paired comparisons; no unmatched records',len(wide)==96 and not wide.isna().any().any())
 wide['delta_bu_ac']=wide.diversified_3y_bu_ac-wide.baseline_2y_bu_ac
 wide['period']=np.where(wide.year<=2011,'training','held_out')
 annual=wide.groupby(['crop','year','period'],as_index=False).agg(baseline_bu_ac=('baseline_2y_bu_ac','mean'),diversified_bu_ac=('diversified_3y_bu_ac','mean'),delta_bu_ac=('delta_bu_ac','mean'),blocks=('block_number','count'))
 check('four matched blocks per crop/year',annual.blocks.eq(4).all())
 weather=pd.read_csv(REPO/'case-study/boone-cn-weather-audit/processed/weather_exposure_screens.csv')
 weather=weather[(weather.site=='Boone')&(weather.driver=='POWER')][['year','May_Sep_rain_mm','Tmax_ge35_days']]
 annual=annual.merge(weather,on='year',validate='many_to_one',how='left')
 check('NASA context joins every annual contrast',annual.May_Sep_rain_mm.notna().all())
 rows=[];metrics=[]
 for crop,g in annual.groupby('crop'):
  train=g[g.period=='training'];test=g[g.period=='held_out'];effect=float(train.delta_bu_ac.mean())
  for period,x in g.groupby('period'):
   values=x.delta_bu_ac.to_numpy()
   rows.append({'crop':crop,'period':period,'years':len(x),'paired_blocks':len(x)*4,'baseline_mean_bu_ac':float(x.baseline_bu_ac.mean()),'diversified_mean_bu_ac':float(x.diversified_bu_ac.mean()),'mean_delta_bu_ac':float(values.mean()),'mean_delta_pct_of_baseline':float(values.mean()/x.baseline_bu_ac.mean()*100),'year_bootstrap_mean_interval_bu_ac':boot_mean(values),'annual_delta_min_bu_ac':float(values.min()),'annual_delta_max_bu_ac':float(values.max()),'positive_years':int((values>0).sum())})
  for label,pred in [('no_change',0.0),('training_mean_contrast',effect)]:
   error=pred-test.delta_bu_ac.to_numpy()
   metrics.append({'crop':crop,'baseline':label,'training_years':'2006–2011','held_out_years':'2012–2017','held_out_n_years':6,'prediction_delta_bu_ac':pred,'RMSE_delta_bu_ac':float(np.sqrt(np.mean(error**2))),'MAE_delta_bu_ac':float(np.mean(abs(error))),'bias_delta_bu_ac':float(error.mean()),'scope':'Historical annual 3y–2y contrast only; no absolute-yield or process-model validation'})
 write_csv('marsden_standardized_observations.csv',subset);write_csv('marsden_paired_block_contrasts.csv',wide);write_csv('marsden_annual_contrasts.csv',annual);write_csv('contrast_backtest_metrics.csv',pd.DataFrame(metrics))
 summary=pd.DataFrame([{k:v for k,v in x.items() if not isinstance(v,list)}|{'bootstrap_low':x['year_bootstrap_mean_interval_bu_ac'][0],'bootstrap_high':x['year_bootstrap_mean_interval_bu_ac'][1]} for x in rows]);write_csv('contrast_summary.csv',summary)
 pfi=json.loads((ROOT/'pfi_verified_transcription.json').read_text());farms=pd.DataFrame(pfi['farms']);farms['delta_bu_ac']=farms.cover_yield_bu_ac-farms.control_yield_bu_ac
 farms['management_date_conflict']=(farms.seeding_date_table1!=farms.seeding_date_table2)|(farms.termination_date_table1!=farms.termination_date_table2)
 check('PFI rounded treatment means give signed contrasts [0,1,2,1,-11]',farms.delta_bu_ac.tolist()==[0,1,2,1,-11]);check('PFI management date conflicts retained at three farms',farms.management_date_conflict.sum()==3)
 check('PFI water sensor failures retained',farms.sensor_usable.sum()==3)
 write_csv('pfi_2022_farm_summary.csv',farms)
 # Published economic estimates, not newly reconstructed full budgets or current quotes.
 economics=[{'system_years':2,'period':'2006–2011','net_return_USD_ha_year':953,'SEM_USD_ha_year':36},{'system_years':3,'period':'2006–2011','net_return_USD_ha_year':965,'SEM_USD_ha_year':34},{'system_years':4,'period':'2006–2011','net_return_USD_ha_year':913,'SEM_USD_ha_year':26}]
 for x in economics:x.update(definition='Published return to land and management; excludes land cost, management time and subsidies; on-farm manure material valued at zero, spreading charged',source='Davis et al. 2012, Fig 1d / Results, established phase; main system p=0.57',data_type='published modeled economic estimate based on trial yields and budget assumptions, not cash-account records')
 write_csv('published_historic_economics.csv',pd.DataFrame(economics))
 bundle={'version':'public-trials-1','date':'2026-11-15','protocol':PROTOCOL,'marsden':{'site':'Marsden Farm, Boone County, Iowa','source':'https://github.com/vanichols/maRsden/tree/01476a18c01115f70f154cf7e94c1951205fbda1','paper':'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0047149','observations':192,'matched_pairs':96,'unit_note':'Corn dry Mg/ha divided by 0.845, then converted with 0.06277 Mg/ha per bu/ac; soy at 13% moisture, 0.06719 conversion. Do not compare dry and moist grain directly.','summary':rows,'backtest':metrics,'economics':economics,'limits':['One experiment, four repeatedly sampled blocks. Bootstrap intervals condition on these blocks.','Management-system contrast and author averaging over split herbicide treatments; not pure red-clover causality.','Historical crop-phase yield contrast is not whole-rotation annual revenue.','Backtest concerns an empirical contrast benchmark, not the Rust or APSIM process model.','Complete verified event-level management, soil hydraulic profile, oat phase output and line-item economics are not closed.']},'pfi':pfi|{'farms':farms.replace({np.nan:None}).to_dict('records')},'receipt':receipt,'checks':CHECKS,'human_tests':{'status':'not_conducted','participants':0,'reason':'No participants available; the test package contains blank instruments only'}}
 bundle['raw_workbook_audit']=json.loads((P/'workbook_audit_summary.json').read_text())
 bundle['marsden']['limits'].append('Original corn workbook uses an approximate 0.06271 mass/bushel conversion; declared standardized analysis uses 0.06277, a 0.096% convention difference. Later soybean harvest records are audited but excluded from fitting pending management metadata review.')
 (P/'trial_evidence.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 (P/'validation_checks.json').write_text(json.dumps(CHECKS,indent=2)+'\n')
 report=['# 公开田块试验验证结果','', '本轮完成真实公开试验的单位核验、配对重分析与历史差值回测。没有完成真实农户可用性测试，也未验证个人田块的未来收益。','', '## Marsden：3 年系统与 2 年系统的产量差值','', '统一到常用收获含水率后，按同一年、同一重复区组配对。2006–2011 为训练，2012–2017 为锁定检验。共 192 条作物／系统／年／区组观测，96 个配对。玉米干物质量不能直接与 15.5% 含水率粮重混用。','', '|作物|时期|2 年系统 bu/ac|3 年系统 bu/ac|差值 bu/ac|年均差值范围|','|---|---|---:|---:|---:|---|']
 for x in rows:report.append(f"|{x['crop']}|{x['period']}|{x['baseline_mean_bu_ac']:.2f}|{x['diversified_mean_bu_ac']:.2f}|{x['mean_delta_bu_ac']:+.2f}|{x['annual_delta_min_bu_ac']:+.2f} 至 {x['annual_delta_max_bu_ac']:+.2f}|")
 report += ['', '## 锁定年份回测','', '|作物|差值基线|RMSE bu/ac|MAE bu/ac|偏差 bu/ac|','|---|---|---:|---:|---:|']
 for x in metrics:report.append(f"|{x['crop']}|{x['baseline']}|{x['RMSE_delta_bu_ac']:.2f}|{x['MAE_delta_bu_ac']:.2f}|{x['bias_delta_bu_ac']:+.2f}|")
 report += ['', '这是历史系统差值能否跨时期保持的检验，不是过程模型校准验收或播前产量预测。若训练均值基线不优于零差值基线，应明确保留失败，不重新划分年份来改善结果。具体四区组条件下的年重采样区间见 JSON／CSV，不能解释为跨农场预测区间。','', '## 黑麦独立案例','', '|2022 农场|作物|覆盖 bu/ac|无覆盖 bu/ac|有符号差值|原报告显著性|','|---|---|---:|---:|---:|---|']
 for _,x in farms.iterrows():report.append(f"|{x['farm']} ({x['town']})|{x['crop']}|{x.cover_yield_bu_ac}|{x.control_yield_bu_ac}|{x.delta_bu_ac:+g}|{'Y' if x.reported_significant else 'N'}|")
 report += ['', '这些是报告中的四重复处理均值，非下载到的条带原始值。显著性保留原报告，不从四舍五入的均值和 LSD 伪造 p 值。N 不代表等效。Brown 为黑麦＋冬豌豆混播，Ose 为黑麦后玉米，均不能直接验证当前 S1 的黑麦后大豆阶段。','', '三处播期／终止日期存在表间冲突，Boone 的 Gustafson 终止时间甚至跨越大豆播期前后，均保留待核实。Ose 结果段／Table 3 与结论段冲突，保留表中 −11 bu/ac 并标注冲突。土壤水分只在三个农场有可用传感器记录；没有获得原始时序，不能计算 ET、灌溉节省或水量平衡。','', '## 经济证据的边界','', 'Davis 等（2012）报告的 2006–2011 年 2／3／4 年系统土地与管理回报分别为 953／965／913 USD/ha/年（SEM 36／34／26），系统差异检验 p=0.57，不能按点估计排推荐名次。它们是基于真实试验产量和历史预算假设的经济估算，非现金流水；排除土地、管理时间和补助，并假设场内粪肥材料免费。未获得完整逐项预算，不能独立复算全部 CBA，也不外推为当前利润。','', '## 数据来源与完整性','', '- [作者数据，固定提交](https://github.com/vanichols/maRsden/tree/01476a18c01115f70f154cf7e94c1951205fbda1)；保留 MIT 许可证。','- [Davis et al. 2012](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0047149)。','- [PFI 试验报告](https://practicalfarmers.org/resources/research-reports/cover-crop-effect-on-soil-water/)，2022 试验／2023 发表，网页年份标签不作为试验年。','- NASA POWER 为已有区域背景汇总，未伪造私人田块坐标。','', '当前可验证的是公开观测与历史处理差值；完整田块过程输入、真实交易与农户理解仍需后续实证。']
 report += ['', '## 新取得原始工作簿的复核', '', '固定版本原始玉米 384 条完整／分区记录可全部重建为作者的 228 个小区年，干物质量最大误差约 5×10⁻⁹ Mg/ha。原表每 bu/ac 对应 0.06271 Mg/ha，略不同于本次冻结的标准 0.06277（约 0.096%）；正文为声明口径统一后的计算值，非逐字抄录原表 bu/ac。2018–2020 年新增 72 个大豆分区收获记录均可从实收质量、面积与水分复算，但后续工作簿沿用 2018 年管理注释，且存在采样宽度变化，先单列待核实，不加入已锁定回测。86 项原始工作簿检查通过。']
 (OUT/'Public_Field_Validation_Report_CN.md').write_text('\n'.join(report)+'\n')
 shutil.copy(V2/'raw/marsden/LICENSE.md',ROOT/'MARSden_LICENSE.md')
 print(json.dumps({'checks_passed':len(CHECKS),'summary':rows,'backtest':metrics},indent=2,ensure_ascii=False))
if __name__=='__main__':analyze()
