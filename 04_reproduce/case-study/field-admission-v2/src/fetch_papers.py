from pathlib import Path
import subprocess,json,hashlib
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1];D=R/'raw/papers';D.mkdir(exist_ok=True)
jobs=[('root_soil_data_s1.csv','https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0164209.s001&type=supplementary'),('root_carbon_data_s2.csv','https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0164209.s002&type=supplementary'),('root_paper.html','https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0164209'),('AAEA_2015_economics.pdf','https://ageconsearch.umn.edu/record/205805/files/AAEA%202015%20paper.pdf')]
jobs.append(('saxton2006.pdf','https://www.atmos.illinois.edu/~sshu3/model/saxton2006.pdf'))
records=[]
for name,url in jobs:
 p=D/name;r={'file':str(p.relative_to(R)),'url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
 try:
  if not p.exists():
   c=subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','60','--connect-timeout','15','--output',str(p),url],capture_output=True,text=True)
   if c.returncode:raise RuntimeError(c.stderr.strip())
  if p.stat().st_size<10:raise RuntimeError('Empty response')
  r.update(status='downloaded',bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 except Exception as e:r.update(status='failed',error=str(e))
 records.append(r);print(name,r['status'],r.get('bytes',r.get('error')),flush=True)
(R/'paper_sources.json').write_text(json.dumps(records,indent=2)+'\n')
