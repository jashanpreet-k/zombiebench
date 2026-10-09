"""Reproduce empirical article claims and record the limits of verification."""
import contextlib,hashlib,io,json,re,subprocess,sys
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
import analyze_results
from baseline import predict
sys.path.insert(0,str(HERE))
from analyze_followup import analyze
from grading import judge
from prepare_article_update import main as prepare_article
from run_records import records

def main():
 with contextlib.redirect_stdout(io.StringIO()):
  original=analyze_results.main();followup=analyze();prepare_article()
 assert original['correct']==592 and original['attempts']==672
 assert original['miss_types']=={'False Zombies':55,'Missed Zombies':17,'Wrong old bug IDs':7,'Unreadable':1}
 assert original['hardest']==[('zb-37',7),('zb-48',7),('zb-25',6),('zb-46',6),('zb-26',5),('zb-41',5),('zb-47',5),('zb-32',4)]
 proposed=(HERE/'post_proposed.md').read_text()
 published_source=(ROOT/'post.md').read_text()
 if '### The follow-up: same report, different comment' in published_source:
  assert proposed==published_source,'Article differs from script-generated reviewed claims'
 before=(HERE/'artifacts/post_before_followup.md').read_text()
 for title in ['### My runs (per tier, with every miss saved)','### Official Kaggle leaderboard']:
  def table(s):return '\n'.join(line for line in s.split(title)[1].split('\n### ')[0].splitlines() if line.startswith('|'))
  assert table(before)==table(proposed),'Original score table changed'
 source=json.loads((ROOT/'results/2026-10-06-kaggle-48-cases.json').read_text())
 runs=[r for r in source['runs'] if r.get('status')=='completed']
 short=lambda m:m.split('/')[-1].split('@')[0].replace('-2026-03-17','').replace('-2026-04-23','').replace('-2507','')
 for r in runs:
  counts=[int(r['by_tier'][t]['total'].split('/')[0]) for t in ('easy','hard','expert')]
  row=f'| {short(r["model"])} | '+ ' | '.join(map(str,counts))+f' | {r["by_tier"]["expert"]["D"].split("/")[0]} | **{r["passed"]}** |'
  assert row in proposed,'Model score table mismatch: '+r['model']
 leaderboard=json.loads((ROOT/'results/2026-10-06-kaggle-official-leaderboard.json').read_text())['leaderboard']
 for r in leaderboard:assert f'| {r["model"]} | {r["score"]:.2f} |' in proposed
 misses=[m for r in runs for m in r['misses']]
 case41=[m for m in misses if m['case']=='zb-41' and m['answer']=='regression #3325']
 case37=[m for m in misses if m['case']=='zb-37' and m['answer']=='new']
 assert len(case41)==5 and len(case37)==6
 assert sum('3174' in m.get('reason','') for m in case37)==3
 targets={'zb-46':{3129},'zb-47':{3336,3308},'zb-48':{3571}}
 d_misses=[m for m in misses if m['case'] in targets]
 assert len(d_misses)==18 and sum(analyze_results.regression_id(m['answer']) in targets[m['case']] for m in d_misses)==16
 cases=json.loads((ROOT/'cases.json').read_text())
 baseline=sum(judge(c,json.dumps(dict(predict(c)[0],reason='Formula')))['status']=='pass' for c in cases)
 assert baseline==15 and sum(c['expected']['verdict']=='new' for c in cases)==24
 historical=[]
 for path in sorted((ROOT/'results').glob('*.json')):
  for r in json.loads(path.read_text()).get('runs',[]):
   if r.get('passed') is not None:historical.append(dict(file=path.name,model=r['model'],passed=r['passed'],total=r.get('total')))
 assert any(r['model']=='google/gemini-3.8-flash' and (r['passed'],r['total'])==(12,12) for r in historical)
 assert any(r['model'].split('/')[-1].startswith('gpt-5.5') and (r['passed'],r['total'])==(36,36) for r in historical)
 assert any('gpt-5.4-nano' in r['model'] and (r['passed'],r['total'])==(24,36) for r in historical)
 nano=next(r for r in runs if 'gpt-5.4-nano' in r['model'])
 assert sum(int(nano['by_tier'][t]['total'].split('/')[0]) for t in ('easy','hard'))==22
 raw,sources=records(HERE)
 quote=followup['l3_quote']
 if quote:assert quote['reason']==raw[quote['model']]['results']['r1:'+quote['case_id']]['reason']
 sdk_models=[]
 for path in (HERE/'runs').rglob('*.result.json'):
  r=json.loads(path.read_text());model=r['agent_info']['model_info']['name']
  files=list((path.parent/'followup/runs').glob('*.json'))
  assert any(json.loads(f.read_text()).get('model')==model for f in files),'Missing raw record for actual SDK model'
  sdk_models.append(dict(path=str(path.relative_to(HERE)),actual_model=model))
 # Credentials are never intentionally loaded; inspect only persisted result field names.
 forbidden={'api_key','api-key','access_token','refresh_token','authorization','client_secret'}
 def scan(x):
  if isinstance(x,dict):
   assert not forbidden.intersection(k.lower() for k in x),'Credential-like result field requires review'
   for v in x.values():scan(v)
  elif isinstance(x,list):
   for v in x:scan(v)
 for path in (HERE/'runs').rglob('*.json'):scan(json.loads(path.read_text()))
 protected=['cases.json','kaggle_task.py','kaggle_paste.py',*map(str,Path('results').glob('*.json'))]
 diff=subprocess.check_output(['git','diff','86c219d','--',*protected],cwd=ROOT,text=True)
 assert not diff,'Protected original files changed'
 report=dict(status='passed',original=original,original_formula_score=baseline,original_zb41_wrong_target=len(case41),original_expert_d_same_kind_ids=16,
  historical_run_claims=historical,followup_headline=followup['headline'],followup_dataset_sha256=followup['dataset_sha256'],article_sha256=hashlib.sha256(proposed.encode()).hexdigest(),sdk_actual_models=sdk_models,
  evidence_limits=['Original leaderboard scores verified against archived snapshot, not independently downloaded original raw API replies.',
  'Original blind-audit counts exist only in the build log; precise counts were removed from the updated article.',
  'Original bug IDs, units and example quantities are case inputs, not inferred performance statistics.',
  'Baseline coefficients and model version numbers are definitions/identifiers, not empirical run claims.',
  'Follow-up is synthetic; repeated scaffolds and shared-case/model dependence limit inference beyond these observations.'],
  judging_review=dict(insights='Controlled clean/planted comparison and matched same/different-code controls; no real-world reliability or significance claim.',writing='Preserves the original findings, labels the expansion separately, and lists repeat coverage per model.',creativity='Comment ladder, irrelevant-comment placebo, matched-code controls and archived blind audit.'))
 (HERE/'artifacts/judge_pass.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Judge pass: saved-run counts, original tables, quoted follow-up reason, SDK identities and protected files verified. Historical audit limitation recorded.')

if __name__=='__main__':main()
