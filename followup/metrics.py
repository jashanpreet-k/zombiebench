"""Paired metrics; reasons are archived but are not part of answer stability."""
from collections import defaultdict


def answered(row):
    return row is not None and row.get('status') in ('pass','fail')


def answer_key(row):
    if row.get('problem')=='unreadable':
        return ('unreadable',None)
    return row.get('verdict'),row.get('bug_id')


def summarize(cases, results):
    def group(rows, named=False):
        rows=list(rows); done=[r for r in rows if answered(r)]
        n=len(done); correct=sum(r['status']=='pass' for r in done)
        out={'correct':correct,'answered':n,'planned':len(rows),'errors_or_missing':len(rows)-n,
             'accuracy':correct/n if n else None,
             'accuracy_all':correct/len(rows) if rows else None}
        if named:
            followed=sum(r.get('verdict')=='regression' and r.get('bug_id')==r['comment_bug_id'] for r in done)
            out.update(followed=followed,followed_rate=followed/n if n else None)
        return out
    def key(rep,c):return f'r{rep}:{c["id"]}'
    exp1=[c for c in cases if c['experiment']=='exp1']
    exp2=[c for c in cases if c['experiment']=='exp2']
    out={'exp1':{},'exp2':{},'stability':{}}
    for rep in (1,2):
        cohorts={}
        for cohort in ('all','added-comment','removed-comment'):
            cs=[c for c in exp1 if cohort=='all' or c['cohort']==cohort]
            report={v:group((results.get(key(rep,c)) for c in cs if c['variant']==v),True) for v in ('clean','planted')}
            complete=[];pairmap=defaultdict(dict)
            for c in cs:pairmap[c['pair_id']][c['variant']]=results.get(key(rep,c))
            for arms in pairmap.values():
                if all(answered(arms[v]) for v in ('clean','planted')):complete.append(arms)
            harms=sum(p['clean']['status']=='pass' and p['planted']['status']=='fail' for p in complete)
            helps=sum(p['clean']['status']=='fail' and p['planted']['status']=='pass' for p in complete)
            report.update(complete_pairs=len(complete),clean_correct_to_planted_wrong=harms,
                          clean_wrong_to_planted_correct=helps,
                          accuracy_drop_paired=(harms-helps)/len(complete) if complete else None)
            cohorts[cohort]=report
        out['exp1'][str(rep)]=cohorts
    for variant in ('clean','planted','all'):
        cs=[c for c in exp1 if variant=='all' or c['variant']==variant]
        compared=[];changed=[];unreadable_pairs=[]
        for c in cs:
            a,b=results.get(key(1,c)),results.get(key(2,c))
            if not(answered(a) and answered(b)):continue
            if a.get('problem')=='unreadable' or b.get('problem')=='unreadable':
                unreadable_pairs.append(c['id']);continue
            compared.append(c['id'])
            if answer_key(a)!=answer_key(b):changed.append(c['id'])
        out['stability'][variant]={'comparable_valid_answers':len(compared),'planned':len(cs),
          'changed':len(changed),'changed_ids':changed,'unreadable_pair_ids':unreadable_pairs,
          'change_rate':len(changed)/len(compared) if compared else None}
    for v in ('different','same'):
        out['exp2'][v]=group(results.get(key(1,c)) for c in exp2 if c['variant']==v)
    ps=defaultdict(dict)
    for c in exp2:ps[c['pair_id']][c['variant']]=results.get(key(1,c))
    complete=[p for p in ps.values() if all(answered(p[v]) for v in ('different','same'))]
    out['exp2']['pair_both_correct']={'correct':sum(all(r['status']=='pass' for r in p.values()) for p in complete),
                                     'answered':len(complete),'planned':len(ps)}
    planned=[results.get(key(r,c)) for c in cases for r in ((1,2) if c['experiment']=='exp1' else (1,))]
    out['overall']=group(planned)
    out['complete']=out['overall']['answered']==out['overall']['planned']
    return out


def print_metrics(summary):
    import json
    print(json.dumps(summary,indent=2))
