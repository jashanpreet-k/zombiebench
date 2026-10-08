"""Compare independently recorded blind answers with gold, after the audit finishes."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from grading import build_prompt
HERE=Path(__file__).resolve().parent
cases={c['id']:c for c in json.loads((HERE/'cases_followup.json').read_text())}
prompts=json.loads((HERE/'audit/blind_prompts.json').read_text())
mapping=json.loads((HERE/'audit/mapping.json').read_text())
answers=json.loads((HERE/'audit/blind_answers.json').read_text())
assert len(answers)==103 and {a['id'] for a in answers}==set(mapping)
assert len({a['id'] for a in answers})==103
for p in prompts:
 assert hashlib.sha256(p['prompt'].encode()).hexdigest()==mapping[p['id']]['sha256']
 assert p['prompt']==build_prompt(cases[mapping[p['id']]['case_id']])
total=Counter();agree=Counter();disagreements=[]
for a in answers:
 c=cases[mapping[a['id']]['case_id']];total[c['experiment']]+=1
 if (a['verdict'],a['bug_id'])==(c['expected']['verdict'],c['expected']['bug_id']):agree[c['experiment']]+=1
 else:disagreements.append({'audit_id':a['id'],'case_id':c['id'],'answer':a,'expected':c['expected']})
report={'audit':'Three fresh agents, no inherited conversation; each read only one shuffled label-free batch.',
        'model':'Inherited parent model; runtime did not expose an exact version identifier.',
        'agreement':{k:{'agreed':agree[k],'total':v} for k,v in total.items()},
        'disagreements':disagreements,'ambiguities':[a['id'] for a in answers if a.get('ambiguity')],
        'limitations':'One blind AI audit is a clarity check, not independent human validation or a model-performance estimate.'}
(HERE/'audit/report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if disagreements or report['ambiguities']:raise SystemExit(1)
