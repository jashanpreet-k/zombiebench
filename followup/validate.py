"""Extend the original validator without changing root files. Run from any directory."""
import copy
import difflib
import json
import re
import sys
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from validate import check_case, check_leaks, check_positions, CUE_WORDS
sys.path.insert(0,str(HERE))
from grading import build_prompt
from build_cases import SELECTION, REMOVALS


def main():
    cases=json.loads((HERE/'cases_followup.json').read_text())
    originals={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())}
    runs=[r for r in json.loads((ROOT/'results/2026-10-06-kaggle-48-cases.json').read_text())['runs'] if r['status']=='completed']
    errors=[]; pairs=defaultdict(list)
    def require(ok, message):
        if not ok: errors.append(message)
    require(len(cases)==52,'Expected 52 prompts.')
    require(len({c['id'] for c in cases})==len(cases),'Duplicate prompt IDs.')
    require(len(runs)==14 and len({r['model'] for r in runs})==14,'Expected 14 distinct source runs.')
    require(all(r['total']==48 and r.get('errors',0)==0 for r in runs),'Source runs incomplete.')
    misses=Counter(m['case'] for r in runs for m in r['misses'])
    for c in cases:
        check_case(c,errors)
        pairs[(c['experiment'],c['pair_id'])].append(c)
    diffs=['# All Experiment 1 twin diffs\n\nGenerated from the actual model prompts; only the description comment changes.\n']
    added=[];e2=[]
    for (experiment,pair_id),twins in pairs.items():
        require(len(twins)==2,f'{pair_id}: expected two twins')
        variants={c['variant']:c for c in twins}
        if experiment=='exp1':
            require(set(variants)=={'clean','planted'},f'{pair_id}: missing arm')
            clean,planted=variants['clean'],variants['planted']
            source=originals[clean['source_case_id']]
            named=clean['comment_bug_id']
            require(named in {b['id'] for b in clean['history']},f'{pair_id}: absent named ID')
            require(named!=clean['expected']['bug_id'],f'{pair_id}: named ID is gold')
            require(clean['expected']==planted['expected']==source['expected'],f'{pair_id}: changed gold')
            require(misses[pair_id]==clean['source_misses'],f'{pair_id}: wrong source miss count')
            added_pair=clean['cohort']=='added-comment'
            comment=(' ' if added_pair else '')+clean['comment']
            require(planted['new_report']['description'].count(comment)==1,f'{pair_id}: comment not unique')
            require(planted['new_report']['description'].replace(comment,'',1)==clean['new_report']['description'],f'{pair_id}: more than comment changed')
            for field in ('history','expected','tier','type','siblings','decoy_bug_id','key_clue','why'):
                require(clean[field]==planted[field]==source[field],f'{pair_id}: changed {field}')
            for field in ('title','language','component'):
                require(clean['new_report'][field]==planted['new_report'][field]==source['new_report'][field],f'{pair_id}: changed {field}')
            unmodified=clean if added_pair else planted
            require(unmodified['new_report']==source['new_report'],f'{pair_id}: original arm altered')
            if added_pair:
                added.append(clean)
                require(clean['tier'] in ('easy','hard'),f'{pair_id}: source is not easy/hard')
                require(misses[pair_id]==(1 if pair_id in ('zb-07','zb-27') else 0),f'{pair_id}: selection exception not approved')
                if clean['type'] in 'AB':require(named in source['siblings'],f'{pair_id}: wrong ID is not a sibling')
                if clean['type']=='C':require(named==source['decoy_bug_id'],f'{pair_id}: wrong C decoy')
            require(clean['key_clue'] in clean['new_report']['description'] or clean['key_clue'] in clean['new_report']['title'],f'{pair_id}: removal destroyed clue')
            delta='\n'.join(difflib.unified_diff(build_prompt(clean).splitlines(),build_prompt(planted).splitlines(),fromfile=clean['id'],tofile=planted['id'],lineterm='',n=0))
            diffs.append(f'\n## {pair_id}\n\n```diff\n{delta}\n```\n')
        else:
            require(set(variants)=={'different','same'},f'{pair_id}: bad matched arms')
            d,a=variants['different'],variants['same'];e2+=twins
            require(d['history']==a['history'],f'{pair_id}: history differs')
            require(d['type']=='D' and a['type']=='A',f'{pair_id}: unbalanced labels')
            require(d['expected']=={'verdict':'new','bug_id':None},f'{pair_id}: D gold invalid')
            require(a['expected']=={'verdict':'regression','bug_id':a['comparison_bug_id']},f'{pair_id}: matched gold invalid')
            for field in ('title','language','component'):
                require(d['new_report'][field]==a['new_report'][field],f'{pair_id}: metadata cues differ')
            for label,pattern in CUE_WORDS.items():
                texts=[c['new_report']['title']+' '+c['new_report']['description'] for c in (d,a)]
                require(len(re.findall(pattern,texts[0],re.I))==len(re.findall(pattern,texts[1],re.I)),f'{pair_id}: cue count differs: {label}')
    require(Counter(c['type'] for c in added)==dict.fromkeys('ABCD',3),'Added-comment sample not 3 per type.')
    require(Counter(c['tier'] for c in added)=={'easy':6,'hard':6},'Added-comment tiers not 6/6.')
    require({p for e,p in pairs if e=='exp1'}==set(SELECTION)|set(REMOVALS),'Exp1 source set differs.')
    require(len(e2)==18 and Counter(c['type'] for c in e2)=={'A':9,'D':9},'Exp2 not balanced 9/9.')
    check_leaks(e2,errors)
    check_positions(e2,errors)
    (HERE/'twin_diffs.md').write_text(''.join(diffs))
    if errors:raise SystemExit('\n'.join(errors))
    print('PASS: 52 cases; 17 comment-only pairs; 12 additions balanced 3/type and 6/tier; 9 matched Exp2 pairs; no tested cue leaks.')
    print('Approved exceptions: zb-07 and zb-27 each missed by 1/14 models. zb-39 names a diagnosis, not an explicit ID.')

if __name__=='__main__':main()
