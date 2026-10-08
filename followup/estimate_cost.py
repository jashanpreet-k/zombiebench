"""Reproducible workload with hypothetical tariff scenarios, not price quotes."""
import json
from pathlib import Path
from grading import build_prompt
HERE=Path(__file__).resolve().parent
cs=json.loads((HERE/'cases_followup.json').read_text())
full_chars=sum(len(build_prompt(c)) for c in cs)
repeat_chars=sum(len(build_prompt(c)) for c in cs if c['experiment']=='exp1')
full_calls=len(cs);repeat_calls=sum(c['experiment']=='exp1' for c in cs)
scenarios=[]
for name,ratio,out in [('short replies',4,150),('planning buffer',2.5,500),('long reasoning stress',2.5,2000)]:
    cheap_full=(full_chars/ratio+full_calls*out*5)/1e6
    frontier=(full_chars/ratio*5+full_calls*out*25)/1e6
    cheap_repeat=(repeat_chars/ratio+repeat_calls*out*5)/1e6
    scenarios.append(dict(name=name,chars_per_input_token=ratio,output_tokens_per_call=out,
      priority1_nine_full_usd=round(9*cheap_full,2),priority2_two_frontier_usd=round(2*frontier,2),
      priority3_nine_repeats_usd=round(9*cheap_repeat,2),total_usd=round(9*cheap_full+2*frontier+9*cheap_repeat,2)))
result=dict(full_run_calls=full_calls,second_exp1_calls=repeat_calls,models=11,
            planned_calls_before_retries=11*full_calls+9*repeat_calls,
            full_run_characters=full_chars,repeat_characters=repeat_chars,
            rate_assumptions_usd_per_million=dict(cheap=dict(input=1,output=5),frontier=dict(input=5,output=25)),
            warning='Hypothetical rates, not current Kaggle quotes. No guarantee of finishing within two daily allocations. Check actual daily/monthly dollar balances and recorded usage. Retry errors once; never spend the $2 reserve.',scenarios=scenarios)
(HERE/'cost_plan.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
