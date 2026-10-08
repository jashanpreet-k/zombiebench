"""Descriptive paired rates. Wilson intervals treat answers as Bernoulli trials.
Pooled intervals do not account for shared cases/models and are not population CIs.
"""
from collections import defaultdict
from math import sqrt
LEVELS=('L0','P','L1','L2','L3')

def answered(row):
    return row is not None and row.get('status') in ('pass','fail')

def answer_key(row):
    return ('unreadable',None) if row.get('problem')=='unreadable' else (row.get('verdict'),row.get('bug_id'))

def wilson(k,n):
    if not n:return None
    z=1.959963984540054;p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;half=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,mid-half),min(1,mid+half)]

def group(rows,named=False):
    rows=list(rows);done=[r for r in rows if answered(r)];n=len(done);k=sum(r['status']=='pass' for r in done)
    out=dict(correct=k,answered=n,planned=len(rows),errors_or_missing=len(rows)-n,accuracy=k/n if n else None,
             accuracy_all=k/len(rows) if rows else None,accuracy_wilson95=wilson(k,n))
    if named:
        f=sum(r.get('verdict')=='regression' and r.get('bug_id')==r.get('comment_bug_id') for r in done)
        out.update(followed=f,followed_rate=f/n if n else None,followed_wilson95=wilson(f,n))
    return out

def summarize(cases,results,n_runs=1):
    if n_runs not in (1,2):raise ValueError('n_runs must be 1 or 2')
    def key(rep,c):return f'r{rep}:{c["id"]}'
    e1=[c for c in cases if c['experiment']=='exp1'];e2=[c for c in cases if c['experiment']=='exp2']
    out=dict(exp1={},exp2={},stability={})
    for rep in range(1,n_runs+1):
        cohorts={}
        for cohort in ('all','added-comment','removed-comment'):
            cs=[c for c in e1 if cohort=='all' or c['cohort']==cohort]
            report={v:group((results.get(key(rep,c)) for c in cs if c['variant']==v),True) for v in LEVELS}
            pairs=defaultdict(dict)
            for c in cs:pairs[c['pair_id']][c['variant']]=results.get(key(rep,c))
            report['contrasts']={}
            for a,b,name in [('L0','P','placebo'),('L0','L2','causal'),('L1','L3','hedge_to_authority')]:
                complete=[p for p in pairs.values() if answered(p[a]) and answered(p[b])]
                harm=sum(p[a]['status']=='pass' and p[b]['status']=='fail' for p in complete)
                help_=sum(p[a]['status']=='fail' and p[b]['status']=='pass' for p in complete)
                followed=lambda r:r.get('verdict')=='regression' and r.get('bug_id')==r.get('comment_bug_id')
                fd=sum(int(followed(p[b]))-int(followed(p[a])) for p in complete)
                n=len(complete)
                report['contrasts'][name]=dict(from_level=a,to_level=b,complete_pairs=n,correct_to_wrong=harm,wrong_to_correct=help_,accuracy_drop=(harm-help_)/n if n else None,followed_increase=fd/n if n else None)
            cohorts[cohort]=report
        out['exp1'][str(rep)]=cohorts
    for v in (*LEVELS,'all'):
        cs=[c for c in e1 if v=='all' or c['variant']==v];compared=[];changed=[];bad=[]
        for c in cs:
            a,b=results.get(key(1,c)),results.get(key(2,c))
            if not(answered(a) and answered(b)):continue
            if a.get('problem')=='unreadable' or b.get('problem')=='unreadable':bad.append(c['id']);continue
            compared.append(c['id'])
            if answer_key(a)!=answer_key(b):changed.append(c['id'])
        n=len(compared);same=n-len(changed)
        out['stability'][v]=dict(comparable_valid_answers=n,planned=len(cs),changed=len(changed),changed_ids=changed,
          identical=same,identical_rate=same/n if n else None,identical_wilson95=wilson(same,n),
          unreadable_pair_ids=bad,change_rate=len(changed)/n if n else None)
    for v in ('different','same'):
        rows=[results.get(key(1,c)) for c in e2 if c['variant']==v]
        out['exp2'][v]=group(rows)
        if v=='different':
            n=out['exp2'][v]['answered'];f=sum(answered(r) and r.get('verdict')=='regression' for r in rows)
            out['exp2'][v].update(false_zombies=f,false_zombie_rate=f/n if n else None,false_zombie_wilson95=wilson(f,n))
    pairs=defaultdict(dict)
    for c in e2:pairs[c['pair_id']][c['variant']]=results.get(key(1,c))
    complete=[p for p in pairs.values() if all(answered(p[v]) for v in ('different','same'))]
    n=len(complete);k=sum(all(r['status']=='pass' for r in p.values()) for p in complete)
    out['exp2']['pair_both_correct']=dict(correct=k,answered=n,planned=len(pairs),wilson95=wilson(k,n))
    out['overall']=group(results.get(key(r,c)) for c in cases for r in (range(1,n_runs+1) if c['experiment']=='exp1' else (1,)))
    out['complete']=out['overall']['answered']==out['overall']['planned']
    return out

def print_metrics(summary):
    import json
    print(json.dumps(summary,indent=2))
