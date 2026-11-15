"""Independent integrity, unit, join and release-gate checks for this scientific replay."""
from pathlib import Path
import hashlib,json,unittest
import numpy as np
import pandas as pd

R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]; P=R/'processed'

class AdmissionChecks(unittest.TestCase):
 def test_pinned_original_files(self):
  records=json.loads((R/'sources.json').read_text()); self.assertEqual(len(records),21)
  for x in records:
   b=(R/x['file']).read_bytes()
   self.assertEqual(hashlib.sha256(b).hexdigest(),x['sha256'])
   self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),x['sha'])
   self.assertIn('01476a18c01115f70f154cf7e94c1951205fbda1',x['url'])
  papers=json.loads((R/'paper_sources.json').read_text())
  self.assertEqual(sum(x['status']=='downloaded' for x in papers),4)
  for x in papers:
   if x['status']=='downloaded':self.assertEqual(hashlib.sha256((R/x['file']).read_bytes()).hexdigest(),x['sha256'])
 def test_measured_profile_support(self):
  d=pd.read_csv(P/'measured_2014_soil_layers.csv')
  self.assertEqual(len(d),40); self.assertEqual(set(d.rot),{2,4})
  for _,g in d.groupby('plot'):
   g=g.sort_values('top_cm'); self.assertEqual(list(g.top_cm),[0,15,30,60,90]); self.assertEqual(list(g.bottom_cm),[15,30,60,90,100])
  self.assertLess(abs(d['bulkden_g.cm3']-d.drywt_g/d.voladj_cm3).max(),.01)
 def test_estimated_retention_never_measured(self):
  d=pd.read_csv(P/'hydraulic_parameter_priors.csv'); self.assertEqual(len(d),80)
  self.assertTrue((d.LL15_PTF_m3_m3<d.DUL33_PTF_m3_m3).all())
  self.assertTrue((d.DUL33_PTF_m3_m3<d.SAT_BD_porosity_proxy_m3_m3).all())
  self.assertTrue(d.status.eq('estimated_prior_not_measured_retention').all())
  s=json.loads((P/'hydraulic_audit_summary.json').read_text()); self.assertFalse(s['retention_measured']); self.assertFalse(s['initial_state_date_verified'])
 def test_water_join_units_and_support(self):
  d=pd.read_csv(P/'soil_water_2014_conditional_volume.csv')
  self.assertEqual(len(d),256); self.assertTrue(d.year.eq(2014).all()); self.assertFalse(d.aggregate_0_30_used.any())
  self.assertTrue(pd.to_datetime(d.date).dt.year.eq(2014).all())
  self.assertFalse(d.duplicated(['plot','date','top_cm']).any())
  np.testing.assert_allclose(d.conditional_storage_mm,d.gravimetric_g_g*d.effective_BD_g_cm3*(d.bottom_cm-d.top_cm)*10,rtol=1e-12)
 def test_log_conflicts_not_silently_corrected(self):
  d=pd.read_csv(P/'original_log_event_clusters.csv'); bad=d[d.year_conflict]
  self.assertEqual(len(d),1168); self.assertEqual(len(bad),40)
  self.assertTrue(bad.admission.eq('date_review_required').all())
  self.assertFalse(json.loads((P/'management_audit_summary.json').read_text())['complete_all_events_claim'])
 def test_nutrient_basis_and_treatment_scope(self):
  s=json.loads((P/'resolved_fertilizer_scope.json').read_text())
  self.assertEqual(s['2013_June28']['C4_lb_N_ac'],50)
  n=pd.read_csv(P/'resolved_2014_main_N_events.csv'); c=n[n.trt.eq('C2')]
  self.assertEqual(list(c.amount_lb_N_ac),[100,50])
  self.assertAlmostEqual(c.amount_kg_N_ha.sum(),168.1276734,places=8)
  e=pd.read_csv(R/'replay_inputs/events.csv')
  self.assertEqual(list(e.doy),[111,112,162,279]); self.assertAlmostEqual(e.amount_kg_N_ha.sum(),c.amount_kg_N_ha.sum(),places=8)
 def test_replay_complete_not_best_case(self):
  a=pd.read_csv(R/'replay_results/annual.csv'); d=pd.read_csv(R/'replay_results/daily.csv')
  self.assertEqual(len(a),32); self.assertEqual(len(d),32*365)
  self.assertEqual(set(a['plot']),{13,24,34,44}); self.assertEqual(set(a.initial_fraction),{.2,.4,.6,.8})
  self.assertEqual(set(a.OC_OM),{.5,.58}); self.assertFalse(a.duplicated(['plot','initial_fraction','OC_OM']).any())
  self.assertLess(a.water_error_mm.abs().max(),1e-6); self.assertLess(a.C_error_kg_ha.abs().max(),1e-5); self.assertLess(a.N_error_kg_ha.abs().max(),1e-6)
 def test_replay_receipt_matches_executed_inputs(self):
  receipt=json.loads((R/'replay_results/receipt.json').read_text())
  for p,h in receipt['source_sha256'].items(): self.assertEqual(hashlib.sha256((REPO/p).read_bytes()).hexdigest(),h)
  for p,h in receipt['input_sha256'].items(): self.assertEqual(hashlib.sha256((R/'replay_inputs'/p).read_bytes()).hexdigest(),h)
 def test_scores_and_baseline_scope(self):
  d=pd.read_csv(P/'field_replay_yield_pairs.csv')
  np.testing.assert_allclose(d.predicted_bu_ac_155,d.corn_yield_dry_kg_ha/1000/.845/.06277)
  s=json.loads((P/'field_replay_evaluation.json').read_text())
  self.assertEqual(s['corn_plot_years'],4); self.assertEqual(s['same_weather_years'],1)
  self.assertFalse(s['range_is_confidence_interval']); self.assertFalse(s['field_model_validated'])
  self.assertLess(s['yield_bias_bu_ac_range'][1],0); self.assertGreater(s['water_bias_mm_range'][0],0)
  self.assertLess(s['same_period_plot_mean_water_in_sample_baseline']['RMSE'],s['water_RMSE_mm_range'][0])
 def test_financial_order_requires_technology_strata(self):
  d=pd.read_csv(P/'historical_financial_point_order.csv')
  self.assertEqual(list(d[d.technology.eq('GE')].sort_values('point_estimate_rank_within_technology').rotation_years),[2,3,4])
  self.assertEqual(list(d[d.technology.eq('Non-GE')].sort_values('point_estimate_rank_within_technology').rotation_years),[3,4,2])
  self.assertTrue(np.allclose(d.phase_area_weight*d.rotation_years,1))
  grid=pd.read_csv(P/'historical_price_stress_grid.csv'); self.assertEqual(len(grid),486)
  e=json.loads((P/'economic_audit_summary.json').read_text()); self.assertFalse(e['field_complete_CBA_eligible']); self.assertFalse(e['full_MCA_eligible'])

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(AdmissionChecks)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 (P/'verification_results.json').write_text(json.dumps({'checks':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'real_farmer_participants':0,'scope':'Integrity and declared diagnostic checks; not independent field validation'},indent=2)+'\n')
 raise SystemExit(not result.wasSuccessful())
