"""Regrade saved raw responses and compute all follow-up article numbers.
No inference calls. Conflicting repetitions are rejected, not cherry-picked.
"""
import hashlib
import json
from pathlib import Path
from grading import build_prompt, judge
from metrics import summarize, LEVELS
HERE=Path(__file__).resolve().parent

def analyze():
    cases=json.loads((HERE/'cases_followup.json').read_text())
    byid={c['id']:c for c in cases}
    sha=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest()
    merged={};sources={}
    for path in sorted((HERE/'runs').rglob('*.json')):
        d=json.loads(path.read_text())
        if not isinstance(d,dict) or not {'model','dataset_sha256','results','calls'}<=d.keys():continue
        if d['dataset_sha256']!=sha:raise ValueError('Different dataset in '+str(path))
        model=d['model'];dest=merged.setdefault(model,{})
        sources.setdefault(model,[]).append(str(path.relative_to(HERE)))
        for key,r in d['results'].items():
            rep,cid=key.split(':',1);c=byid[cid]
            if rep not in ('r1','r2') or (rep=='r2' and c['experiment']!='exp1'):raise ValueError('Unexpected repetition')
            if r['prompt_sha256']!=hashlib.sha256(build_prompt(c).encode()).hexdigest():raise ValueError('Prompt mismatch: '+key)
            if r['status']!='error':
                checked=judge(c,r['raw_reply'])
                for field in ('status','verdict','bug_id','problem','reason'):
                    if checked[field]!=r[field]:raise ValueError('Saved grading mismatch: '+key+'/'+field)
            if key in dest and dest[key]!=r:
                # A completed retry may supersede the preserved API error.
                if dest[key]['status']=='error' and r['status']!='error':dest[key]=r
                elif r['status']=='error' and dest[key]['status']!='error':continue
                else:raise ValueError('Conflicting saved answer: '+model+'/'+key)
            else:dest[key]=r
    if not merged:raise SystemExit('No saved Kaggle follow-up model results. No claims or charts generated.')
    reports={};pooled_cases=[];pooled_rows={};included=[];partial=[];quote_candidates=[]
    for i,(model,rows) in enumerate(sorted(merged.items())):
        n=2 if any(k.startswith('r2:') for k in rows) else 1
        reports[model]=summarize(cases,rows,n_runs=n)
        first=summarize(cases,rows,n_runs=1)
        if not first['complete']:partial.append(model);continue
        included.append(model)
        for c in cases:
            clone=dict(c,id=f'm{i}-{c["id"]}',pair_id=f'm{i}-{c["pair_id"]}')
            pooled_cases.append(clone)
            for rep in (1,2):
                r=rows.get(f'r{rep}:{c["id"]}')
                if r:pooled_rows[f'r{rep}:{clone["id"]}']=r
            r=rows.get('r1:'+c['id'])
            if c['experiment']=='exp1' and c['variant']=='L3' and r and r['status']=='fail' and r['verdict']=='regression' and r['bug_id']==c['comment_bug_id']:
                quote_candidates.append(dict(model=model,case_id=c['id'],reason=r['reason']))
    if not included:raise SystemExit('Only incomplete runs are available; finish them before headline analysis.')
    pooled=summarize(pooled_cases,pooled_rows,n_runs=2)
    ladder=pooled['exp1']['1']['all'];clean=ladder['L0'];planted=ladder['L2'];delta=ladder['contrasts']['causal']['accuracy_drop']
    if delta>0:
        headline=(f'Across {len(included)} models and {clean["answered"]} paired reports, adding a confident wrong diagnosis reduced accuracy from {clean["correct"]}/{clean["answered"]} to {planted["correct"]}/{planted["answered"]} ({delta*100:.1f} percentage points).')
    elif delta<0:
        headline=(f'Across {len(included)} models and {clean["answered"]} paired reports, the confident wrong comment did not reduce pooled accuracy: it rose from {clean["correct"]}/{clean["answered"]} to {planted["correct"]}/{planted["answered"]}.')
    else:
        headline=(f'Across {len(included)} models and {clean["answered"]} paired reports, clean and confidently misdiagnosed reports had the same pooled accuracy: {clean["correct"]}/{clean["answered"]}.')
    out=dict(dataset_sha256=sha,models=reports,included_first_run_models=included,excluded_incomplete_models=partial,
      sources=sources,pooled=pooled,headline=headline,l3_quote=quote_candidates[0] if quote_candidates else None,
      caveats=['Pooled headline uses first runs only.','Wilson intervals are descriptive binomial intervals; shared-case/model dependence is not modeled.',
       'Paired differences are observed contrasts, not independent-arm significance tests.','L1 to L3 combines confidence and authority.',
       'At L0/P, followed means choosing the counterfactual wrong target ID.'])
    (HERE/'analysis.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    lines=['# Follow-up results\n',headline+'\n','| Level | Correct | Accuracy (Wilson 95%) | Wrong target | Target rate (Wilson 95%) |','|---|---:|---|---:|---|']
    def pct(rate,ci):return f'{100*rate:.1f}% [{100*ci[0]:.1f}, {100*ci[1]:.1f}]'
    for level in LEVELS:
        g=ladder[level];lines.append(f'| {level} | {g["correct"]}/{g["answered"]} | {pct(g["accuracy"],g["accuracy_wilson95"])} | {g["followed"]}/{g["answered"]} | {pct(g["followed_rate"],g["followed_wilson95"])} |')
    lines+=['','Original-five L2-wrong → L0-correct: '+str(pooled['exp1']['1']['removed-comment']['contrasts']['causal']['correct_to_wrong']),
            '\n```json',json.dumps(dict(exp2=pooled['exp2'],stability=pooled['stability']['all']),indent=2),'```']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(headline)
    print(json.dumps(dict(complete_models=included,partial_models=partial,stability=pooled['stability']['all']),indent=2))
    return out

if __name__=='__main__':analyze()
