"""Sequential authorized Kaggle CLI batches with quota checks and checkpoints.
The uploaded task must use kbench.llm and a $2 per-session allocation.
This driver never reads or prints credential files.
"""
import argparse,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from kaggle import api
from inference_quota import balances
from metrics import summarize
from run_records import records
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
TASK='zombiebench-followup'
PLANNED=[
 'openai/gpt-5.4-nano-2026-03-17','google/gemini-3.1-flash-lite-preview','openai/gpt-oss-20b',
 'anthropic/claude-haiku-4-5@20251001','google/gemini-2.5-flash','openai/gpt-5.4-mini-2026-03-17',
 'qwen/qwen3-235b-a22b-instruct-2507','google/gemma-4-31b','anthropic/claude-sonnet-4-5@20250929',
 'openai/gpt-6.1-sol','anthropic/claude-opus-5-5@default']

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--n-runs',type=int,choices=(1,2),default=1);args=parser.parse_args()
 cs=json.loads((HERE/'cases_followup.json').read_text());catalog=json.loads((HERE/'model_catalog.json').read_text());slugs={m['proxy']:m['slug'] for m in catalog}
 models=PLANNED if args.n_runs==1 else PLANNED[:9]
 progress={'n_runs':args.n_runs,'completed':[],'unavailable':[],'started_at':datetime.now(timezone.utc).isoformat()}
 def save(): (HERE/f'queue_{args.n_runs}.json').write_text(json.dumps(progress,indent=2)+'\n')
 def cli(*parts):
  result=subprocess.run(['kaggle','benchmarks','tasks',*parts],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  # Expected CLI operational output only; never invoke auth/debug commands here.
  print(result.stdout,flush=True)
  if result.returncode:raise RuntimeError('Kaggle command failed: '+parts[0])
 # Wait for the current uploaded task version before scheduling any work.
 while True:
  with api.build_kaggle_client() as client:task=api._get_benchmark_task(TASK,client)
  if task.creation_state==api._TASK_CREATION_COMPLETED:break
  if 'RUNNING' not in task.creation_state.name and 'QUEUED' not in task.creation_state.name:
   raise RuntimeError('Task creation failed: '+str(task.creation_error_message))
  time.sleep(30)
 from kagglesdk.benchmarks.types.benchmark_tasks_api_service import ApiListBenchmarkTaskRunsRequest
 def current_runs(wanted):
  request=ApiListBenchmarkTaskRunsRequest();request.task_slug=task.slug;request.model_version_slugs=wanted
  with api.build_kaggle_client() as client:return client.benchmarks.benchmark_tasks_api_client.list_benchmark_task_runs(request).runs
 # Launch in priority order, while reserving allocations for jobs still active.
 pending=[]
 data,_=records(HERE)
 for model in models:
  if model not in slugs:
   progress['unavailable'].append(model);save();print('UNAVAILABLE',model,flush=True);continue
  if model in data and summarize(cs,data[model]['results'],n_runs=args.n_runs)['complete']:
   progress['completed'].append(model);save();print('ALREADY SAVED',model,flush=True);continue
  pending.append(model)
 while pending:
  wanted=[slugs[m] for m in pending];runs=current_runs(wanted)
  byslug={r.model_version_slug:r for r in runs}
  finished=[m for m in pending if slugs[m] in byslug and byslug[slugs[m]].state in api._TERMINAL_RUN_STATES]
  if finished:
   cli('download',TASK,*[arg for model in finished for arg in ('-m',slugs[model])],'-o','followup/runs')
   data,_=records(HERE)
   for model in finished:
    if model not in data or not summarize(cs,data[model]['results'],n_runs=args.n_runs)['complete']:
     progress['stop']='Incomplete or actual-model mismatch: '+model;save();print('REVIEW STOP',progress['stop'],flush=True);return
    progress['completed'].append(model);pending.remove(model);save();print('SAVED',model,flush=True)
  if not pending:break
  active=[m for m in pending if slugs[m] in byslug and byslug[slugs[m]].state not in api._TERMINAL_RUN_STATES]
  waiting=[m for m in pending if slugs[m] not in byslug]
  if waiting and len(active)<3:
   q=subprocess.run(['kaggle','quota','--format','json'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   if q.returncode:raise RuntimeError('Accelerator quota command failed')
   quota=balances();progress['last_quota']=quota;save()
   remaining=min(x['remaining'] for x in quota)
   # Conservative: reserve the full $2 for each ongoing job even if some is spent.
   capacity=min(3-len(active),max(0,int((remaining-2-2*len(active))//2)))
   print('QUOTA',json.dumps(quota),'active',len(active),flush=True)
   if capacity:
    batch=waiting[:capacity]
    cli('run',TASK,*[arg for model in batch for arg in ('-m',slugs[model])])
    print('LAUNCHED',batch,flush=True)
   elif not active:
    progress['stop']='Preserving $2 account reserve plus $2 per scheduled task.';save();print('BUDGET STOP',flush=True);return
  time.sleep(30)
 progress['complete']=True;save();print('QUEUE COMPLETE',flush=True)

if __name__=='__main__':
 try:main()
 except Exception as err:raise SystemExit('Queue stopped: '+type(err).__name__+': '+str(err)) from None
