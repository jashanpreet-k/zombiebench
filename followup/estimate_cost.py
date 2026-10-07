"""Reproducible workload estimates with explicit hypothetical rates, not Kaggle quotes."""
import json
from pathlib import Path
from grading import build_prompt
HERE=Path(__file__).resolve().parent
cases=json.loads((HERE/'cases_followup.json').read_text())
chars=sum(len(build_prompt(c))*(2 if c['experiment']=='exp1' else 1) for c in cases)
scenarios=[]
for name,chars_per_token,output_per_call in [('short replies',4,150),('planning buffer',2.5,500),('long reasoning stress',2.5,2000)]:
    input_tokens=chars/chars_per_token
    output_tokens=86*output_per_call
    # These are illustrative planning assumptions, NOT fetched current model prices.
    other=(input_tokens*1+output_tokens*5)/1e6
    frontier=(input_tokens*5+output_tokens*25)/1e6
    scenarios.append({'name':name,'characters_per_input_token':chars_per_token,'output_tokens_per_call':output_per_call,
      'estimated_input_tokens_per_model':round(input_tokens),'estimated_output_tokens_per_model':output_tokens,
      'oct8_nine_models_usd':round(9*other,2),'oct9_two_controls_usd':round(2*frontier,2),
      'total_usd':round(9*other+2*frontier,2)})
out={'prompts_per_model':86,'models':11,'calls_before_retries':946,'characters_per_model':chars,
     'rate_assumptions_usd_per_million':{'nine_models':{'input':1,'output':5},'two_controls':{'input':5,'output':25}},
     'warning':'Rates and token ratios are hypothetical; actual Kaggle tariff, reasoning tokens, failed calls and quota must be checked. These are scenarios, not a guarantee of completion within two days.',
     'scenarios':scenarios}
(HERE/'cost_plan.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
