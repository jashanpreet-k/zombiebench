"""Build a CLI notebook entry point after checking the real inference balance.
Definitions alone cannot create a Kaggle task: the backing notebook needs a run.
For a second-repetition version, embed downloaded first-run records to avoid
paying for them again. Only task responses are embedded, never credentials.
"""
import argparse
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--remaining-usd',type=float,required=True)
parser.add_argument('--n-runs',type=int,choices=[1,2],default=1)
parser.add_argument('--model',default='openai/gpt-5.4-nano-2026-03-17')
args=parser.parse_args()
if not 2<args.remaining_usd<=10:parser.error('Current quota must exceed $2 and not exceed $10.')
cases=json.loads((HERE/'cases_followup.json').read_text())
sha=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest()
seeds={}
for path in sorted((HERE/'runs').rglob('*.json')):
    d=json.loads(path.read_text())
    if not isinstance(d,dict) or not {'model','results','calls','dataset_sha256'}<=d.keys():continue
    if d['dataset_sha256']!=sha:raise SystemExit('Dataset mismatch: '+str(path))
    if d['model'] in seeds and d!=seeds[d['model']]:raise SystemExit('Conflicting run records: '+d['model'])
    seeds[d['model']]=d
if args.n_runs==2:
    needed={'r1:'+c['id'] for c in cases}
    if args.model not in seeds or not needed<=seeds[args.model]['results'].keys():
        parser.error('Download the complete first run before building a second-repetition entry point.')
source=(HERE/'kaggle_followup.py').read_text()
# Literal JSON-compatible Python data: no shell interpolation or auth material.
source+='\n\n# Restore reviewed, downloaded task responses in this notebook session.\n'
source+='SEED_RUNS = '+repr(seeds)+'\n'
source+='for _model, _record in SEED_RUNS.items():\n    _path=output_path(_model)\n    if not _path.exists():save(_path,_record)\n'
source+='\n# The CLI/server captures this task invocation for model evaluation.\n'
source+=f'zombiebench_followup.run(llm=kbench.llms[{args.model!r}], remaining_usd={args.remaining_usd!r}, n_runs={args.n_runs})\n'
(HERE/'kaggle_cli_source.py').write_text(source)
print('Prepared followup/kaggle_cli_source.py; pushing it can execute a paid initialization run.')
