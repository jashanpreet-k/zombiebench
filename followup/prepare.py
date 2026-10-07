"""Freeze original prompt/grader helpers and create shuffled, answer-free audit inputs."""
import ast
import hashlib
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FUNCTIONS=['build_prompt','first_json_object','read_bug_id','parse_answer','judge','describe']
source=(ROOT/'kaggle_task.py').read_text()
tree=ast.parse(source)
helpers='"""Original ZombieBench prompt and grading rules, frozen for this follow-up."""\nimport json\nimport re\nVERDICTS = ("regression", "new")\n\n'
helpers+='\n\n'.join(ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in FUNCTIONS)+'\n'
(HERE/'grading.py').write_text(helpers)
ns={};exec(helpers,ns)
cases=json.loads((HERE/'cases_followup.json').read_text())
random.Random(20261007).shuffle(cases)
inputs=[];mapping={}
for i,c in enumerate(cases,1):
    audit_id=f'prompt-{i:03d}'
    prompt=ns['build_prompt'](c)
    inputs.append({'id':audit_id,'prompt':prompt})
    mapping[audit_id]={'case_id':c['id'],'sha256':hashlib.sha256(prompt.encode()).hexdigest()}
(HERE/'audit').mkdir(exist_ok=True)
(HERE/'audit'/'blind_prompts.json').write_text(json.dumps(inputs,indent=2,ensure_ascii=False)+'\n')
(HERE/'audit'/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
print(f'Prepared {len(inputs)} randomized prompts without labels, pair IDs, clues or gold answers.')
