"""Bundled into kaggle_followup.py; input data and grader are prepended by build_task.py."""
import hashlib
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
import kaggle_benchmarks as kbench

PLANNED_MODELS = [
 'openai/gpt-5.4-nano-2026-03-17', 'google/gemini-3.1-flash-lite-preview',
 'openai/gpt-oss-20b', 'anthropic/claude-haiku-4-5@20251001',
 'google/gemini-2.5-flash', 'openai/gpt-5.4-mini-2026-03-17',
 'qwen/qwen3-235b-a22b-instruct-2507', 'google/gemma-4-31b',
 'anthropic/claude-sonnet-4-5@20250929', 'openai/gpt-6.1-sol',
 'anthropic/claude-opus-5-5@default',
]
CHEAPER_MODELS=PLANNED_MODELS[:9]
FRONTIER_MODELS=PLANNED_MODELS[9:]
DATA_SHA=hashlib.sha256(json.dumps(CASES,sort_keys=True).encode()).hexdigest()
# Explicit second repetition, no SDK response cache enabled.
# One source prompt per isolated chat; evaluation metadata never reaches the model.

def schedule(n_runs=1):
    if n_runs not in (1,2):raise ValueError('n_runs must be 1 or 2')
    blocks=[[(1,c) for c in CASES if c['experiment']=='exp1'],
            [(1,c) for c in CASES if c['experiment']=='exp2']]
    if n_runs==2:blocks.append([(2,c) for c in CASES if c['experiment']=='exp1'])
    for seed,block in enumerate(blocks,20261008):random.Random(seed).shuffle(block)
    return [row for block in blocks for row in block]


def output_path(model):
    directory=Path('followup')/'runs';directory.mkdir(parents=True,exist_ok=True)
    return directory/(re.sub(r'[^\w.-]+','_',model)+'_'+DATA_SHA[:12]+'.json')


def save(path, data):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');temp.replace(path)


def load(model):
    path=output_path(model)
    if path.exists():
        data=json.loads(path.read_text())
        if data['dataset_sha256']!=DATA_SHA or data['model']!=model:raise ValueError('Incompatible saved run.')
        return data
    seed=globals().get('SEED_RUNS',{}).get(model)
    if seed is not None:
        if seed['dataset_sha256']!=DATA_SHA:raise ValueError('Seed dataset mismatch.')
        import copy
        data=copy.deepcopy(seed);save(path,data);return data
    return {'model':model,'dataset_sha256':DATA_SHA,'settings':'provider defaults; no response cache',
            'results':{},'calls':[],'created_at':datetime.now(timezone.utc).isoformat()}


class BudgetStop(RuntimeError):pass


class Budget:
    """Session guard, NOT a guaranteed pre-call billing cap or account quota reader.

    User supplies currently displayed remaining quota. Keep $2 reserve. Stop if
    usage is absent or remaining allocation is below max($0.10, 3 * largest call).
    One retry per API error; failed calls can still consume quota. The platform's
    daily quota is the final cap; avoid concurrent sessions and recheck the UI.
    """
    def __init__(self, remaining_usd):
        if not 2 < remaining_usd <= 10:raise ValueError('Enter current remaining daily quota, > $2 and <= $10.')
        self.allowance=remaining_usd-2;self.spent=0.0;self.largest=0.0;self.unknown=False
    def before(self):
        if self.unknown:raise BudgetStop('Missing cost metadata: check Kaggle quota before continuing.')
        if self.allowance-self.spent<max(0.10,3*self.largest):raise BudgetStop('Budget reserve reached. Save outputs and continue after quota refill.')
    def record(self,usage):
        a=usage.get('input_tokens_cost_nanodollars');b=usage.get('output_tokens_cost_nanodollars')
        if a is None or b is None:self.unknown=True;return
        cost=(a+b)/1e9;self.spent+=cost;self.largest=max(self.largest,cost)


ACTIVE_BUDGET=None


def usage_dict(chat):
    u=getattr(chat,'usage',None)
    return {name:getattr(u,name,None) for name in ('input_tokens','output_tokens','input_tokens_cost_nanodollars',
               'output_tokens_cost_nanodollars','total_backend_latency_ms')}


def execute_model(llm, model, budget, max_calls=0, n_runs=1):
    data=load(model); path=output_path(model);made=0;stop=None
    for rep,case in [item for item in schedule(n_runs) for _ in range(2)]:
        key=f'r{rep}:{case["id"]}'
        if answered(data['results'].get(key)):continue
        if sum(x['key']==key for x in data['calls'])>=2:continue
        if max_calls and made>=max_calls:stop='Requested call checkpoint reached';break
        try:budget.before()
        except BudgetStop as err:stop=str(err);break
        prompt=build_prompt(case);started=datetime.now(timezone.utc).isoformat()
        reply=None;failure=None;usage={}
        with kbench.chats.new(f'followup-{key}-{len(data["calls"])}') as chat:
            try:
                reply=llm.prompt(prompt)
                if reply is None or not str(reply).strip():failure='Empty model response'
            except Exception as err:
                # Never dump headers, auth, or full exception payloads.
                failure=type(err).__name__
            usage=usage_dict(chat)
        budget.record(usage);made+=1
        result=judge(case,reply) if failure is None else dict(id=case['id'],tier=case['tier'],type=case['type'],
                  status='error',problem=None,verdict=None,bug_id=None,reason=failure)
        result.update(repetition=rep,experiment=case['experiment'],variant=case['variant'],pair_id=case['pair_id'],
                      cohort=case.get('cohort'),comment_bug_id=case.get('comment_bug_id'),raw_reply=reply,
                      prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),started_at=started,usage=usage)
        data['results'][key]=result
        data['calls'].append(dict(result,key=key))
        save(path,data)
        print(key,result['status'],describe(result.get('verdict'),result.get('bug_id')))
        if result['status']!='pass':print('reason:',result['reason'])
        if budget.unknown:
            stop='Cost metadata unavailable: check inference quota before resuming.';break
        time.sleep(1.5)
    summary=summarize(CASES,data['results'],n_runs=n_runs);data['summary']=summary;data['n_runs']=n_runs;save(path,data)
    print_metrics(summary)
    print('All saved misses/errors:')
    for key,result in data['results'].items():
        if result['status']!='pass':print(key,result.get('raw_reply'),result['reason'])
    print('Session recorded spend:',round(budget.spent,6),'USD; output:',path)
    if stop:raise BudgetStop(stop)
    if not summary['complete']:raise RuntimeError('Incomplete run: no leaderboard score until all planned answers exist (API errors retry at most once).')
    # Keep the published score comparable when optional stability calls are added.
    return summarize(CASES,data['results'],n_runs=1)['overall']['accuracy']


@kbench.task(name='zombiebench_followup',description='Controlled bug-comment ablations with repeat runs and matched same-code versus different-code defects.')
def zombiebench_followup(llm, remaining_usd: float = 0.0, max_calls: int = 0, n_runs: int = 1, max_session_usd: float = 2.0) -> float:
    model=getattr(llm,'model',None) or getattr(llm,'name',None)
    if not model:raise ValueError('Model must have a stable identifier.')
    # Repeats are planned only for the cheaper requested models. A platform
    # initialization model must not trigger an unrequested extra repetition.
    if str(model) not in CHEAPER_MODELS:n_runs=1
    budget=ACTIVE_BUDGET or Budget(remaining_usd)
    if ACTIVE_BUDGET is None:
        if not 0 < max_session_usd <= remaining_usd-2:raise ValueError('Session allocation exceeds available quota minus reserve.')
        budget.allowance=min(budget.allowance,max_session_usd)
    return execute_model(llm,str(model),budget,max_calls=max_calls,n_runs=n_runs)


def run_models(models, remaining_usd, max_calls=0, n_runs=1):
    """Resume saved runs; n_runs=2 adds only missing second-repetition Exp1 calls."""
    global ACTIVE_BUDGET
    models=[models] if isinstance(models,str) else list(models)
    missing=[m for m in models if m not in kbench.llms]
    if missing:raise ValueError('Model IDs unavailable: '+repr(missing)+'; inspect list(kbench.llms.keys()).')
    ACTIVE_BUDGET=Budget(remaining_usd)
    try:
        for model in models:
            run=zombiebench_followup.run(llm=kbench.llms[model],remaining_usd=remaining_usd,max_calls=max_calls,n_runs=n_runs)
            # SDK may capture task exceptions instead of propagating them. Stop
            # the batch whenever its persisted model record is incomplete.
            if not load(model).get('summary',{}).get('complete'):
                print('Batch stopped at incomplete model; check quota/output before resuming.');break
    finally:ACTIVE_BUDGET=None


def run_plan(remaining_usd):
    """One notebook cell, ordered priorities, resumable files, shared daily reserve."""
    global ACTIVE_BUDGET
    missing=[m for m in PLANNED_MODELS if m not in kbench.llms]
    if missing:raise ValueError('Unavailable requested model IDs: '+repr(missing)+'. No substitutions or calls made.')
    ACTIVE_BUDGET=Budget(remaining_usd)
    try:
        for models,n_runs in ((CHEAPER_MODELS,1),(FRONTIER_MODELS,1),(CHEAPER_MODELS,2)):
            for model in models:
                zombiebench_followup.run(llm=kbench.llms[model],remaining_usd=remaining_usd,n_runs=n_runs)
                summary=summarize(CASES,load(model)['results'],n_runs=n_runs)
                if not summary['complete']:
                    print('STOP: incomplete model; save all followup/runs files, check quota, and resume.');return
        print('COMPLETE: all priority batches and stability repetitions saved.')
    finally:
        import shutil
        shutil.make_archive('zombiebench-followup-results','zip','followup','runs')
        ACTIVE_BUDGET=None


def preview_plan():
    print('103 unique prompts: 85 Exp1 + 18 Exp2. Second Exp1 adds 85/model. Planned total: 1,898 calls.')
    print('Planned IDs must be checked against this notebook catalog:',PLANNED_MODELS)
    print('No calls have been made. Check daily/monthly quota, then supply remaining_usd.')

# Defining/pasting this file never calls a model. Run run_models(...) explicitly.
