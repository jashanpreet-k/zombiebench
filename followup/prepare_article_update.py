"""Generate a reviewable article update exclusively from analyzed saved runs.
Does not contact DEV. Run only after all available planned work is complete.
"""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def percentage(g,metric='accuracy'):
 rate=g[metric];lo,hi=g[metric+'_wilson95']
 return f'{rate*100:.1f}% (Wilson 95%: {lo*100:.1f}–{hi*100:.1f}%)'

def main():
 d=json.loads((HERE/'analysis.json').read_text());cases=json.loads((HERE/'cases_followup.json').read_text())
 if d['excluded_incomplete_models']:raise SystemExit('Resolve or explicitly document incomplete models before writing the article.')
 p=d['pooled'];e=p['exp1']['1']['all'];diff=p['exp2']['different'];same=p['exp2']['same'];n=len(d['included_first_run_models'])
 contrast=e['contrasts']['causal'];original=p['exp1']['1']['removed-comment']['contrasts']['causal']
 pair_count=len({c['pair_id'] for c in cases if c['experiment']=='exp1'});new_count=sum(c['experiment']=='exp2' and c['variant']=='different' for c in cases)
 note=(f'Each of {n} models saw the same {pair_count} reports in separate chats under five conditions: no comment (L0), an irrelevant confident meeting note (P), a hedged wrong diagnosis (L1), a confident wrong diagnosis (L2), and a developer claiming to have fixed that bug personally (L3). Only the terminal comment line changed; the correct answer did not. These are first-run results.\n\n')
 table='| Comment | Correct | Accuracy, Wilson 95% | Wrong target selected | Target rate, Wilson 95% |\n|---|---:|---|---:|---|\n'
 for v in ('L0','P','L1','L2','L3'):
  g=e[v];table+=f'| {v} | {g["correct"]}/{g["answered"]} | {percentage(g)} | {g["followed"]}/{g["answered"]} | {percentage(g,"followed_rate")} |\n'
 causal=(f'On the paired L0/L2 comparison, {contrast["correct_to_wrong"]} answers changed from correct to wrong and {contrast["wrong_to_correct"]} changed from wrong to correct. The observed accuracy drop was {contrast["accuracy_drop"]*100:.1f} percentage points. The placebo accuracy change was {-e["contrasts"]["placebo"]["accuracy_drop"]*100:.1f} points; wrong-target selection changed by {e["contrasts"]["hedge_to_authority"]["followed_increase"]*100:.1f} points from L1 to L3.\n\n'
  f'Among the original planted-diagnosis cases, {original["correct_to_wrong"]}/{original["complete_pairs"]} model–case pairs were wrong at L2 and correct at L0. At L0 and P, “wrong target selected” means the ID named in the other conditions: there is no diagnostic comment to follow.\n\n')
 quote=d['l3_quote']
 if quote:causal+=f'One L3 answer from `{quote["model"]}` on `{quote["case_id"]}`:\n\n> '+quote['reason'].replace('\n',' ')+'\n\n'
 else:causal+='No completed L3 answer selected the planted target incorrectly, so there is no such failure quote to show.\n\n'
 causal+='This comparison measures the effect of the whole inserted comment in this synthetic task. The L1-to-L3 comparison changes confidence and claimed authority together, so it cannot separate their effects. The placebo controls for one kind of extra text, not every semantic difference.\n'
 s1='### The follow-up: same report, different comment\n\n![Wrong-target selection across comment conditions](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-followup-ladder.png)\n\n'+note+table+'\n'+causal
 s2=(f'### Nine more same-mistake cases\n\n![Accuracy on matched different-code and same-code cases](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-followup-code.png)\n\n'
  f'I added {new_count} different-code cases and {new_count} matched same-code regressions using the same histories. Different-code accuracy was {diff["correct"]}/{diff["answered"]}, or {percentage(diff)}. Same-code accuracy was {same["correct"]}/{same["answered"]}, or {percentage(same)}. '
  f'Models called {diff["false_zombies"]}/{diff["answered"]} different-code cases regressions: a false-zombie rate of {percentage(diff,"false_zombie_rate")}. '
  f'Both members were correct in {p["exp2"]["pair_both_correct"]["correct"]}/{p["exp2"]["pair_both_correct"]["answered"]} matched model–case pairs.\n\n'
  'The matching guards against rewarding a model that always says “new.” These cases use explicit source traces and a repeated scaffold; they extend coverage, but their difficulty is not calibrated to the original expert tier.\n')
 stable=p['stability']['all'];repeated=[m for m,r in d['models'].items() if r['stability']['all']['comparable_valid_answers']]
 limits=(f'- **Follow-up limits:** the added cases and comments are synthetic. All {n} included models have one full follow-up run; {len(repeated)} have a second Experiment 1 run. ')
 if stable['comparable_valid_answers']:
  lo,hi=stable['identical_wilson95'];limits+=(f'Across valid comparable responses, {stable["identical"]}/{stable["comparable_valid_answers"]} answers were identical ({stable["identical_rate"]*100:.1f}%; Wilson 95% {lo*100:.1f}–{hi*100:.1f}%), and {stable["changed"]} changed. ')
 limits+='Repeat agreement is not proof of general reliability. Pooled Wilson intervals treat observations as binomial trials and do not model dependence from shared cases or models. The headline uses first runs only. Two type-C selection exceptions were approved because only one eligible type-C source case was universally correct. Original planted comments were moved to the same terminal position; zb-39 now explicitly names its diagnosis’s ID.\n'
 limits+='- **Run correction:** the CLI initially bound nano explicitly, so one run scheduled under Gemini actually called nano. Saved SDK metadata identified the error. That independent nano run supplies its repeat comparison; its extra expansion answers are excluded. The corrected task uses Kaggle’s selected-model placeholder, and actual model IDs are checked before pooling.\n'
 limits+='- **Availability:** Sonnet 4.5 was absent from Kaggle’s follow-up model catalog and was not replaced.\n'
 text=(ROOT/'post.md').read_text()
 if '### The follow-up: same report, different comment' in text:raise SystemExit('Follow-up already present; review edits instead of duplicating.')
 hook=d['headline'];assert len(hook.split())<60
 start=text.index('I gave AI models');text=text[:start]+hook+'\n\n'+text[start:]
 text=text.replace('### 2. Five models picked',s2+'\n### 2. Five models picked',1)
 text=text.replace('### 3. Right rejection',s1+'\n### 3. Right rejection',1)
 text=text.replace('### Honest limits\n','### Honest limits\n\n'+limits,1)
 text=text.replace('> **Note:** all findings and quotes below come from my own notebook runs, which saved every miss; Kaggle\'s official run is separate.',"> **Note:** the original 48-case findings and quotes come from my own notebook runs, which saved every miss; Kaggle's official leaderboard run is separate. The controlled follow-up below was run through Kaggle's CLI and saved every response.")
 text=text.replace('This is the leaderboard the Kaggle link shows:', 'This is the saved leaderboard snapshot from publication:')
 text=text.replace('gpt-oss-120b and Gemini 3.8 Flash were still running on Kaggle when I published, so they aren\'t in this table.',"gpt-oss-120b and Gemini 3.8 Flash were still running on Kaggle when I published, so they aren't in this archived table.")
 text=text.replace('More "same mistake, different code" cases, since that\'s where models split, and several runs per model to measure how noisy the scores are.', 'Next I would test less templated reports from independent authors and repeat the comparisons across more sampling settings.')
 original_link='- **Kaggle task (official leaderboard):** https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench'
 text=text.replace(original_link,original_link+'\n- **Controlled follow-up task:** https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench-followup',1)
 (HERE/'post_proposed.md').write_text(text)
 print('Prepared followup/post_proposed.md for review; local post.md and DEV remain unchanged.')
if __name__=='__main__':main()
