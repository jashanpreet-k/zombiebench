"""Build a CLI notebook entry point after checking the real inference balance.
Definitions alone cannot create a Kaggle task: the backing notebook needs a run.
For a second-repetition version, embed downloaded first-run records to avoid
paying for them again. Only task responses are embedded, never credentials.
"""
import argparse
import base64
import zlib
import hashlib
import json
from run_records import records
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
seeds,_=records(HERE)
for d in seeds.values():
    if d['dataset_sha256']!=sha:raise SystemExit('Seed dataset mismatch')
if args.n_runs==2:
    needed={'r1:'+c['id'] for c in cases}
    if args.model not in seeds or not needed<=seeds[args.model]['results'].keys():
        parser.error('Download the complete first run before building a second-repetition entry point.')
source=(HERE/'kaggle_followup.py').read_text()
# Literal JSON-compatible Python data: no shell interpolation or auth material.
source+='\n\n# Restore reviewed, downloaded task responses in this notebook session.\n'
compressed=base64.b64encode(zlib.compress(json.dumps(seeds,separators=(',',':')).encode(),9)).decode()
source+='import base64 as _b64, zlib as _zl\n'
source+='SEED_RUNS = json.loads(_zl.decompress(_b64.b64decode('+repr(compressed)+')))\n'
source+='for _model, _record in SEED_RUNS.items():\n    _path=output_path(_model)\n    if not _path.exists():save(_path,_record)\n'
source+='\n# The CLI/server captures this task invocation for model evaluation.\n'
source+=f'zombiebench_followup.run(llm=kbench.llm, remaining_usd={args.remaining_usd!r}, n_runs={args.n_runs})\n'
(HERE/'kaggle_cli_source.py').write_text(source)
print('Prepared followup/kaggle_cli_source.py; pushing it can execute a paid initialization run.')
