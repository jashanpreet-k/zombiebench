"""Load raw records with explicit, auditable run-label corrections.
Raw downloaded files are never edited. Actual model identity wins over a
scheduler label. Duplicate seed copies are deduplicated by response identity.
"""
import copy,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def records(root=HERE):
 adjustments=json.loads((root/'run_adjustments.json').read_text()) if (root/'run_adjustments.json').exists() else {}
 merged={};sources={}
 for path in sorted((root/'runs').rglob('*.json')):
  d=json.loads(path.read_text())
  if not isinstance(d,dict) or not {'model','dataset_sha256','results','calls'}<=d.keys():continue
  rel=str(path.relative_to(root));d=copy.deepcopy(d)
  matches=[a for prefix,a in adjustments.items() if rel.startswith(prefix)]
  if len(matches)>1:raise ValueError('Overlapping run corrections')
  if matches:
   a=matches[0]
   if d['model']!=a['actual_model']:raise ValueError('Correction does not match actual model')
   transformed={}
   for key,r in d['results'].items():
    if r['experiment']!='exp1':continue
    r['repetition']=a['exp1_repetition'];transformed[f'r{r["repetition"]}:'+r['id']]=r
   d['results']=transformed
   calls=[]
   for r in d['calls']:
    if r['experiment']!='exp1':continue
    r['repetition']=a['exp1_repetition'];r['key']=f'r{r["repetition"]}:'+r['id'];calls.append(r)
   d['calls']=calls
  model=d['model'];sources.setdefault(model,[]).append(rel)
  dest=merged.setdefault(model,dict(model=model,dataset_sha256=d['dataset_sha256'],results={},calls=[],settings=d.get('settings'),created_at=d.get('created_at')))
  if dest['dataset_sha256']!=d['dataset_sha256']:raise ValueError('Mixed dataset versions')
  for key,r in d['results'].items():
   prior=dest['results'].get(key)
   if prior and prior!=r:
    if prior['status']=='error' and r['status']!='error':pass
    elif r['status']=='error' and prior['status']!='error':continue
    else:raise ValueError('Conflicting raw response: '+model+'/'+key)
   dest['results'][key]=r
  seen={(r['key'],r['started_at']) for r in dest['calls']}
  for r in d['calls']:
   identity=(r['key'],r['started_at'])
   if identity not in seen:dest['calls'].append(r);seen.add(identity)
 return merged,sources
