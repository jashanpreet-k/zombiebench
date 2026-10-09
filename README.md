# [ZombieBench — write-up](https://dev.to/jashanpreet_kaur_917e774f/same-kind-of-bug-isnt-the-same-bug-where-ai-models-get-fooled-21dd)

*Submitted to the DEV Kaggle Benchmarking Challenge. Write-up: https://dev.to/jashanpreet_kaur_917e774f/same-kind-of-bug-isnt-the-same-bug-where-ai-models-get-fooled-21dd*

Given a short history of fixed bugs and one new bug report, can an AI model tell
"this is bug #N coming back" from "this is a new bug"? And does it beat a simple
keyword formula?

<!-- FOLLOWUP RESULTS START -->
## Follow-up experiment

In a controlled test across 9 models, adding a confident wrong diagnosis reduced accuracy from 145/153 to 121/153 (15.7 percentage points). Each comparison used the same report, with only the comment changed.

| Model | Clean | Confident comment | Wrong target: clean → comment | Different code | Same code | Repeat changes |
|---|---:|---:|---:|---:|---:|---:|
| claude-haiku-4-5 | 17/17 | 13/17 | 0 → 0 | 0/9 | 9/9 | 1/85 |
| claude-opus-5-5 | 17/17 | 17/17 | 0 → 0 | 9/9 | 9/9 | Not repeated |
| gemini-2.5-flash | 16/17 | 15/17 | 1 → 1 | 6/9 | 9/9 | Not repeated |
| gemini-3.1-flash-lite-preview | 17/17 | 15/17 | 0 → 1 | 7/9 | 9/9 | 2/85 |
| gemma-4-31b | 17/17 | 17/17 | 0 → 0 | 9/9 | 9/9 | Not repeated |
| gpt-5.4-mini | 16/17 | 12/17 | 0 → 0 | 9/9 | 9/9 | Not repeated |
| gpt-5.4-nano | 11/17 | 2/17 | 5 → 13 | 0/9 | 9/9 | 9/85 |
| gpt-6.1-sol | 17/17 | 17/17 | 0 → 0 | 9/9 | 9/9 | Not repeated |
| gpt-oss-20b | 17/17 | 13/17 | 0 → 3 | 4/9 | 9/9 | 10/85 |

Accuracy denominators are answered prompts; full first runs are required for inclusion. Repeat changes compare verdict plus ID, excluding unreadable/API-error pairs. The original test and follow-up use distinct datasets.

[Full rates and Wilson 95% intervals](followup/results_summary.md) · [Raw responses](followup/runs/) · [Design and audit](followup/README.md) · [Public follow-up task](https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench-followup)
<!-- FOLLOWUP RESULTS END -->

## Key findings

These figures describe **14 completed single model runs on ZombieBench**: 672 model-case
attempts, with 592 correct (**88.1%**).

| Tier | Correct | Accuracy |
|---|---:|---:|
| Easy | 164/168 | 97.6% |
| Hard | 299/336 | 89.0% |
| Expert | 129/168 | 76.8% |

For comparison, the Bug Graveyard formula scored 15/48 on these cases; always answering "new"
scored 24/48.

Across the same runs, misses by case type were A: 9/168, B: 15/168, C: 25/168, and D: 31/168
attempts. A **False Zombie** is a genuinely new bug incorrectly classified as a regression; a
**Missed Zombie** is a true regression incorrectly classified as new. There were 55 False
Zombies and 17 Missed Zombies—about 3.2 times as many false-zombie verdict errors. Seven other
answers selected the wrong historical bug ID, and one response was unreadable. Completed runs
had no API errors.

In Expert D, models missed 18 of 42 attempts. In 16 of those 18 misses, the answer selected an
old bug involving the same general kind of mistake. **Same kind of mistake is not necessarily
the same bug.**

### Case autopsy: zb-41

**History:** #3325 was a 1:5 stock split fixed by updating share quantity; #3374 was a 1:1 bonus
issue fixed by updating quantity and average price. **Report:** the user describes free shares,
one for each existing share, and a large loss—evidence matching the bonus issue. **Planted
diagnosis:** the support note says the split bug #3325 is back. **Outputs:** five model outputs
selected the bug ID named in the support note, making the planted diagnosis a strong misleading
clue in this case. The original study had no clean control, so that observation alone does not establish causation.
The controlled follow-up above tests standardized comment insertions separately. **Gold answer:** regression #3374.

### Scope and limitations

- These are 48 synthetic, author-created cases, with one completed run per model in the analyzed
  results.
- The results describe ZombieBench, not real-world bug triage in general.
- Generated explanations are model outputs, not direct access to internal reasoning.
- Complete raw replies were not archived for every run.

## Case types

| Type | What it tests | Correct answer |
|---|---|---|
| A | Clear regression: same bug, similar words | the old bug's id |
| B | Reworded regression: same bug in a user's words, almost no shared keywords | the old bug's id |
| C | Keyword decoy: shares words with an old bug, but the cause is different | new |
| D | Clearly new bug | new |

There are three tiers:

- **Easy:** 12 cases, 3 per type, with 5–8 fixed bugs each.
- **Hard:** 24 cases, 6 per type, with 12–15 fixed bugs each. Every right answer has 2–3
  "sibling" bugs in the same component or with the same cause, and the reports are messy.
- **Expert:** 12 cases, 3 per type, with 25–30 fixed bugs each, many with similar names. They
  include twin candidates decided by a fix-summary detail, two issues in one report, a
  confident but wrong diagnosis, and the same kind of mistake made again in different code.

All cases are invented for this benchmark.

## Files

- `cases.json`: the cases
- `baseline.py`: the Bug Graveyard Zombie Detector formula, as a baseline
- `kaggle_task.py`: the Kaggle Benchmarks task (one file, cases embedded)
- `kaggle_paste.py`: the same without the lines that run a model, for loading from GitHub
- `embed_cases.py`: copies `cases.json` into `kaggle_task.py` and writes `kaggle_paste.py`
- `validate.py`: checks the cases, including that cue words like "again" don't give the answer away
- `analyze_results.py`: derives the summary statistics below from saved results
- `results/`: scores and parsed miss answers/reasons; not a complete archive of raw model replies
- `NOTES.md`: build log

## Run

```sh
python validate.py          # check cases.json
python baseline.py --verbose
python analyze_results.py  # summarize the saved 48-case runs
python embed_cases.py       # after editing cases.json
```

On Kaggle, load the code from GitHub in a Benchmarks notebook, then run the models you want:

```python
import urllib.request
exec(urllib.request.urlopen("https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/kaggle_paste.py").read().decode())
run_models(["google/gemini-3.8-flash"])
```

`kaggle_paste.py` is `kaggle_task.py` without its last two lines, so loading it calls no model.
If a model's summary reports errors, `run_models([...], rerun_errors=True)` retries only those
cases. For the leaderboard, run `zombiebench.run(kbench.llm)` and then `%choose zombiebench` in
the last cell.

## Results

All 48 cases on Kaggle Benchmarks (commit `5897756`, run on 2026-10-06), 14 completed single model runs:

| Model | Easy (12) | Hard (24) | Expert (12) | Expert A / B / C / D | All (48) |
|---|---|---|---|---|---|
| openai/gpt-6.1-sol | 12/12 | 24/24 | 12/12 | 3/3 / 3/3 / 3/3 / 3/3 | **48/48** |
| anthropic/claude-opus-5-5@default | 12/12 | 24/24 | 12/12 | 3/3 / 3/3 / 3/3 / 3/3 | **48/48** |
| google/gemini-3.1-pro-preview | 12/12 | 24/24 | 12/12 | 3/3 / 3/3 / 3/3 / 3/3 | **48/48** |
| openai/gpt-5.5-2026-04-23 | 12/12 | 24/24 | 12/12 | 3/3 / 3/3 / 3/3 / 3/3 | **48/48** |
| google/gemini-3.8-flash | 12/12 | 24/24 | 12/12 | 3/3 / 3/3 / 3/3 / 3/3 | **48/48** |
| google/gemma-4-31b | 12/12 | 23/24 | 12/12 | 3/3 / 3/3 / 3/3 / 3/3 | **47/48** |
| google/gemini-2.5-flash | 12/12 | 22/24 | 8/12 | 2/3 / 2/3 / 3/3 / 1/3 | **42/48** |
| anthropic/claude-sonnet-4-5@20250929 | 12/12 | 22/24 | 7/12 | 2/3 / 3/3 / 2/3 / 0/3 | **41/48** |
| openai/gpt-5.4-mini-2026-03-17 | 12/12 | 21/24 | 8/12 | 2/3 / 1/3 / 3/3 / 2/3 | **41/48** |
| google/gemini-3.1-flash-lite-preview | 12/12 | 21/24 | 8/12 | 2/3 / 3/3 / 3/3 / 0/3 | **41/48** |
| openai/gpt-oss-20b | 12/12 | 19/24 | 9/12 | 3/3 / 2/3 / 3/3 / 1/3 | **40/48** |
| anthropic/claude-haiku-4-5@20251001 | 12/12 | 21/24 | 6/12 | 1/3 / 3/3 / 2/3 / 0/3 | **39/48** |
| qwen/qwen3-235b-a22b-instruct-2507 | 11/12 | 17/24 | 7/12 | 2/3 / 2/3 / 3/3 / 0/3 | **35/48** (1 unreadable) |
| openai/gpt-5.4-nano-2026-03-17 | 9/12 | 13/24 | 4/12 | 1/3 / 0/3 / 1/3 / 2/3 | **26/48** (1 hallucinated id) |
| Always answering "new" | 6/12 | 12/24 | 6/12 | 0/3 / 0/3 / 3/3 / 3/3 | 24/48 |
| Bug Graveyard formula (`baseline.py`) | 7/12 | 5/24 | 3/12 | 0/3 / 0/3 / 0/3 / 3/3 | 15/48 |

xai/grok-4.6 was unavailable (every call returned 404), and deepseek-ai/deepseek-r1-0528 was
stopped after 3 cases, so neither has a score. The 48-case results file preserves the scores and
parsed answers/reasons for each miss; it is not a complete archive of every raw model response.
Earlier run records are in `results/` too.

Five models score 48/48, so the benchmark doesn't separate the top tier. The hardest category is
expert D, the same kind of mistake made again in different code: 18 of 42 tries missed.
