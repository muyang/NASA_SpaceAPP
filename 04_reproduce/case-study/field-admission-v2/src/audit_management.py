"""Normalize original log clusters; preserve dates, continuations, scope and conflicts."""
from pathlib import Path
from datetime import datetime,date
import pandas as pd,openpyxl,re,json,hashlib,calendar
R=Path(__file__).resolve().parents[1];P=R/'processed';P.mkdir(exist_ok=True)
MONTHS={n.lower():i for i,n in enumerate(calendar.month_name) if n};MONTHS.update({n.lower():i for i,n in enumerate(calendar.month_abbr) if n});MONTHS['sept']=9
def parsed(v,year):
 if isinstance(v,(datetime,date)):return v.date().isoformat() if isinstance(v,datetime) else v.isoformat(),'exact_excel'
 s=str(v or '').strip()
 if not s:return None,'missing'
 if any(c in s for c in ['~','?']) or re.search(r'\d\s*[-–/]\s*\d',s):return None,'approximate_or_range_retained'
 m=re.fullmatch(r'([A-Za-z]+)\.?\s*(\d{1,2})(?:\s*,?\s*(\d{4}))?',s)
 if m and year and m[1].lower() in MONTHS:
  try:return date(int(m[3] or year),MONTHS[m[1].lower()],int(m[2])).isoformat(),'day_month_plus_documented_year'
  except ValueError:pass
 return None,'unparsed_retained'
def category(s):
 v=[]
 for key,pattern in [('sowing',r'plant(?:ed|ing)?|seed(?:ed|ing)?|drill'),('harvest',r'harvest|baled|baling|mowed|cutting'),('fertilizer',r'fertiliz|UAN|urea|superphosphate|potash|manure|compost|\blb\.? ?N'),('tillage',r'plow|cultivat|disk|cultipack'),('crop_protection',r'herbicide|spray|glyphosate|Corvus|Laudis'),('measurement',r'sampl|stand count|emerg|\bV\d|soil core')]:
  if re.search(pattern,s,re.I):v.append(key)
 return '|'.join(v) or 'other_recorded_activity'
def normalize_sheet(path,sheet,year_col,date_col,text_start,year=None):
 ws=openpyxl.load_workbook(path,data_only=True,read_only=True)[sheet];records=[];current=None;context=year
 for number,row in enumerate(ws.iter_rows(values_only=True),1):
  y=row[year_col] if year_col is not None and year_col<len(row) else None
  if isinstance(y,(int,float)) and 2000<=y<=2030:context=int(y)
  value=row[date_col] if date_col<len(row) else None
  text=' | '.join(str(v).strip() for v in row[text_start:] if v is not None and str(v).strip())
  if not text:continue
  if value is not None and str(value).strip():
   if current:records.append(current)
   event_date,status=parsed(value,context)
   current={'source_file':str(path.relative_to(R)),'source_sheet':sheet,'start_row':number,'end_row':number,'context_year':context,'date_original':str(value),'event_date':event_date,'date_status':status,'text':text}
  elif current:
   current['end_row']=number;current['text']+='\n'+text
 if current:records.append(current)
 for d in records:
  d['event_year']=int(d['event_date'][:4]) if d['event_date'] else None
  d['nominal_sheet_year']=int(sheet) if str(sheet).isdigit() else None
  d['year_conflict']=bool(d['event_year'] and d['context_year'] and d['event_year']!=d['context_year']) or bool(d['nominal_sheet_year'] and d['event_year'] and d['nominal_sheet_year']!=d['event_year'])
  d['types']=category(d['text']);d['treatment_codes']='|'.join(sorted(set(re.findall(r'\b(?:C[234]|S[234]|O[34]|A4|T[34])\b',d['text']))))
  d['scope_status']='explicit_treatment_codes' if d['treatment_codes'] else ('all_plots_explicit' if re.search(r'all (?:36 )?plots',d['text'],re.I) else 'free_text_scope_requires_review')
  d['contains_assumption']=bool(re.search(r'assum|guess|not record|no record|probably',d['text'],re.I))
  d['admission']='dated_source_record_needs_scope_and_quantity_review' if d['event_date'] and not d['year_conflict'] else 'date_review_required'
 return records
def main():
 folder=R/'raw/field-logs';events=[]
 events+=normalize_sheet(folder/'Field-activities-Marsden_2001-2017.xlsx','Dates-all',0,1,2)
 path=folder/'Marsden-field-activities-Woods-2013-2018.xlsx'
 workbook=openpyxl.load_workbook(path,data_only=True,read_only=True)
 layouts=[]
 for year in [2013,2014,2016,2017,2018]:
  preview=list(workbook[str(year)].iter_rows(max_row=20,values_only=True))
  counts=[sum(isinstance(r[c],(datetime,date)) for r in preview if len(r)>c) for c in [0,1]]
  col=int(counts[1]>counts[0]);layouts.append({'sheet':str(year),'date_column_1based':col+1,'preview_datetime_counts':counts})
  events+=normalize_sheet(path,str(year),0 if col else None,col,col+1,year)
 events+=normalize_sheet(folder/'Marsden-field-activities-Woods-2019.xlsx','Field Activities',None,0,1,2019)
 events+=normalize_sheet(folder/'Marsden-field-activities-Woods-2020.xlsx','Sheet1',None,0,1,2020)
 d=pd.DataFrame(events);d.to_csv(P/'original_log_event_clusters.csv',index=False)
 (P/'log_sheet_layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
 d[d.year_conflict].to_csv(P/'original_log_date_conflicts.csv',index=False)
 coverage=d.groupby(['source_file','source_sheet','context_year'],dropna=False).agg(source_clusters=('text','size'),dated=('event_date','count'),date_conflicts=('year_conflict','sum')).reset_index();coverage.to_csv(P/'management_source_coverage.csv',index=False)
 primary='raw/field-logs/Marsden-field-activities-Woods-2013-2018.xlsx'
 # Explicit source lines verified against original log; no product-fraction double multiplication.
 nutrients=[(2014,'2014-04-21','C2',100,4,'100 lb. N/acre rate'),(2014,'2014-06-11','C2',50,25,'50 lb N/ac to C2'),(2014,'2014-06-11','C3',25,25,'25 lb N/ac to C3 and C4'),(2014,'2014-06-11','C4',25,25,'25 lb N/ac to C3 and C4')]
 approved=[]
 for year,dt,trt,lb,row,text in nutrients:
  matches=d[(d.source_file==primary)&(d.source_sheet=='2014')&(d.start_row<=row)&(d.end_row>=row)]
  assert len(matches)==1 and text in matches.iloc[0]['text']
  approved.append({'year':year,'date':dt,'trt':trt,'nutrient':'N','amount_lb_N_ac':lb,'amount_kg_N_ha':lb*1.120851156,'source_file':primary,'sheet':'2014','row':row,'basis':'explicit nutrient N; do not multiply by UAN fraction','scope':'main mineral N event, not complete all-subplot nutrient ledger'})
 pd.DataFrame(approved).to_csv(P/'resolved_2014_main_N_events.csv',index=False)
 # Resolve the former 2013 C4 overlapping 75 + 50 entry using the exact original diary text.
 diary=d[(d.source_sheet=='Dates-all')&d.event_date.eq('2013-06-28')];text='\n'.join(diary.text)
 assert '100 lb N/ac to C2, 75 lb/ac to C3 and 50 lb/ac to C4' in text
 (P/'resolved_fertilizer_scope.json').write_text(json.dumps({'2013_June28':{'C2_lb_N_ac':100,'C3_lb_N_ac':75,'C4_lb_N_ac':50,'C4_is_not_75_plus_50':True,'source_file':'raw/field-logs/Field-activities-Marsden_2001-2017.xlsx','sheet':'Dates-all','source_row':764},'2014_C2_main_N_kg_ha':150*1.120851156,'residual_note':'Spray/adjuvant UAN recorded separately; density and subplot basis are not silently resolved. Main events are not claimed to be the complete all-N ledger.'},indent=2)+'\n')
 costs=[{'item':'2014 corn seed','USD_per_unit':152,'seeds_per_unit':80000,'seeds_per_ac':32200,'calculated_USD_ac':152/80000*32200,'reported_approx_USD_ac':61.5,'source_file':primary,'sheet':'2014','row':7}, {'item':'2014 soybean seed','USD_per_unit':57,'seeds_per_unit':140000,'seeds_per_ac':160000,'calculated_USD_ac':57/140000*160000,'reported_approx_USD_ac':65.14,'source_file':primary,'sheet':'2014','row':16}]
 pd.DataFrame(costs).to_csv(P/'recorded_seed_costs.csv',index=False)
 summary={'source_event_clusters':len(d),'dated_clusters':int(d.event_date.notna().sum()),'date_conflicts':int(d.year_conflict.sum()),'important_scope_resolution':'2013 C4 mineral N is 50 lb N/ac, not overlapping 75+50','complete_all_events_claim':False,'reason':'Free-text scope, source duplicates, year conflicts, incidental nutrient inputs and management operations not represented by the reduced model remain. Original chronological clusters and source rows are retained.'}
 (P/'management_audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
