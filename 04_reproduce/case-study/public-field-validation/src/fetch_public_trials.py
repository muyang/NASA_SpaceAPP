"""Acquire public trial records without logins, form submissions or contacting anyone."""
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib, json, subprocess, base64

ROOT=Path(__file__).resolve().parents[1]
JOBS=[
 ('pfi_soil_water_2022.pdf','https://practicalfarmers.org/wp-content/uploads/2026/03/22.FC_.CC.-Cover-crop-soil-water.pdf'),
 ('pfi_soil_water_page.html','https://practicalfarmers.org/resources/research-reports/cover-crop-effect-on-soil-water/'),
 ('marsden_2012_table_s5.docx','https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0047149.s006&type=supplementary'),
 ('marsden_2012_weather.docx','https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0047149.s002&type=supplementary'),
 ('cscap_download_page.html','https://datateam.agron.iastate.edu/cscap/dl/'),
 ('cscap_adc_landing.html','https://data.nal.usda.gov/dataset/sustainable-corn-cap-research-data-usda-nifa-award-no-2011-68002-30190'),
 ('cscap_ardn_landing.html','https://data.nal.usda.gov/dataset/sustainable-corn-cap-research-data-usda-nifa-award-no-2011-68002-30190-ardn-products'),
]
def fetch(job):
 name,url=job;out=ROOT/'raw'/name;out.parent.mkdir(parents=True,exist_ok=True)
 record={'file':'raw/'+name,'requested_url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
 if out.exists() and out.stat().st_size>0:return {**record,'status':'retained','sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size}
 try:
  result=subprocess.run(['curl','--fail','--location','--silent','--show-error','--connect-timeout','15','--max-time','55','--max-filesize','50000000','--output',str(out),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}',url],capture_output=True,text=True)
  if result.returncode and 'raw.githubusercontent.com/vanichols/maRsden/' in url:
   tail=url.split('raw.githubusercontent.com/vanichols/maRsden/',1)[1]
   commit,path=tail.split('/',1)
   api='https://api.github.com/repos/vanichols/maRsden/contents/'+path+'?ref='+commit
   response=subprocess.run(['curl','--fail','--silent','--show-error','--connect-timeout','15','--max-time','40',api],capture_output=True,text=True)
   if response.returncode:raise RuntimeError(response.stderr.strip())
   body=json.loads(response.stdout)
   if body.get('encoding')!='base64':raise RuntimeError('GitHub contents API did not provide a base64 file')
   out.write_bytes(base64.b64decode(body['content']))
   (out.parent/(out.name+'.api.json')).write_text(response.stdout)
   result.returncode=0;result.stdout='200\n'+api+'\napplication/octet-stream'
  if result.returncode:raise RuntimeError(result.stderr.strip())
  status,final,ctype=result.stdout.splitlines()[:3]
  if out.stat().st_size==0:raise RuntimeError('Empty body; no usable data acquired')
  record.update(status='downloaded',http_status=int(status),response_url=final,content_type=ctype,bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest())
 except Exception as exc:record.update(status='failed',error=str(exc))
 return record
if __name__=='__main__':
 more=json.loads((ROOT/'marsden_acquisition.json').read_text()) if (ROOT/'marsden_acquisition.json').exists() else []
 JOBS += [(r['file'],r['url']) for r in more]
 old={r['file']:r for r in json.loads((ROOT/'sources.json').read_text())} if (ROOT/'sources.json').exists() else {}
 with ThreadPoolExecutor(max_workers=4) as pool:
  for future in as_completed([pool.submit(fetch,j) for j in JOBS]):
   r=future.result()
   expected=next((x['git_blob_sha'] for x in more if x['file']==r['file']),None)
   if expected and r['status']!='failed':
    data=(ROOT/r['file']).read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    r['git_blob_sha']=actual
    if actual!=expected:r.update(status='failed',error='Pinned Git blob mismatch')
   old[r['file']]=r;(ROOT/'sources.json').write_text(json.dumps(list(old.values()),indent=2)+'\n');print(r['file'],r['status'],r.get('bytes',r.get('error')),flush=True)
