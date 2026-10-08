"""Run the unchanged root baseline formula on follow-up cases; no models called."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from baseline import predict
sys.path.insert(0,str(HERE))
from grading import judge
from metrics import summarize
cases=json.loads((HERE/'cases_followup.json').read_text())
rows={}
for c in cases:
 prediction,best=predict(c)
 prediction['reason']=f"Formula score {best['score']} for #{best['bug']['id']}."
 for rep in ((1,2) if c['experiment']=='exp1' else (1,)):
  r=judge(c,json.dumps(prediction));r['comment_bug_id']=c.get('comment_bug_id')
  rows[f'r{rep}:{c["id"]}']=r
summary=summarize(cases,rows,n_runs=2)
out={'note':'The formula is deterministic. Its repeated answers are not evidence that LLM outputs are stable.',
     'unique_prompts':len(cases),'unique_correct':sum(r['status']=='pass' for key,r in rows.items() if key.startswith('r1:')),
     'summary':summary,'answers':rows}
(HERE/'baseline_results.json').write_text(json.dumps(out,indent=2)+'\n')
print('Unique prompts:',out['unique_correct'],'/',len(cases))
print('Exp1:',json.dumps(summary['exp1']['1']['all']))
print('Exp2:',json.dumps(summary['exp2']))
