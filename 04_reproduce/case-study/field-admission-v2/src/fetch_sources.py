"""Fetch pinned public raw files through GitHub's official contents API, then hash-check."""
from pathlib import Path
import json,hashlib,base64,subprocess
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def fetch(j):
 out=ROOT/j['file'];out.parent.mkdir(parents=True,exist_ok=True)
 record={**j,'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
 try:
  if not out.exists() or out.stat().st_size!=j['bytes']:
   r=subprocess.run(['curl','--fail','--silent','--show-error','--connect-timeout','15','--max-time','60',j['url']],capture_output=True,text=True)
   if r.returncode:raise RuntimeError(r.stderr.strip())
   body=json.loads(r.stdout)
   if body.get('encoding')!='base64':raise RuntimeError('No base64 file content')
   out.write_bytes(base64.b64decode(body['content']))
  data=out.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  if blob!=j['sha']:raise RuntimeError('Pinned Git blob does not match')
  record.update(status='verified',actual_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),actual_git_blob=blob)
 except Exception as e:record.update(status='failed',error=str(e))
 return record
if __name__=='__main__':
 jobs=json.loads((ROOT/'acquisition_manifest.json').read_text())['jobs']
 receipts={}
 with ThreadPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(fetch,j) for j in jobs]):
   r=f.result();receipts[r['file']]=r;(ROOT/'sources.json').write_text(json.dumps(list(receipts.values()),indent=2)+'\n');print(r['file'],r['status'],r.get('actual_bytes',r.get('error')),flush=True)
 if any(r['status']!='verified' for r in receipts.values()):raise SystemExit(1)
