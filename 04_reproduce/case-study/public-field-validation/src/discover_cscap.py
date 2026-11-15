"""Search the public Figshare API for the official CSCAP deposits; no account/form submission."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
url='https://api.figshare.com/v2/articles/search'
query={'search_for':'"Sustainable corn CAP"','page_size':100}
r=subprocess.run(['curl','--fail','--silent','--show-error','--connect-timeout','15','--max-time','55','-H','Content-Type: application/json','--data-binary','@-',url],input=json.dumps(query),capture_output=True,text=True)
if r.returncode:raise RuntimeError(r.stderr)
(ROOT/'raw/cscap_figshare_search.json').write_text(r.stdout)
data=json.loads(r.stdout)
matches=[x for x in data if 'sustainable corn cap' in x.get('title','').lower()]
(ROOT/'cscap_deposits.json').write_text(json.dumps(matches,indent=2)+'\n')
print(json.dumps([{'id':x['id'],'title':x['title'],'url':x.get('url'),'doi':x.get('doi')} for x in matches],indent=2))
