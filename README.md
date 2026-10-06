# ZombieBench

*Submitted to the DEV Kaggle Benchmarking Challenge. Write-up: https://dev.to/jashanpreet_kaur_917e774f/same-kind-of-bug-isnt-the-same-bug-where-ai-models-get-fooled-21dd*

Given a short history of fixed bugs and one new bug report, can an AI model tell
"this is bug #N coming back" from "this is a new bug"? And does it beat a simple
keyword formula?

## Case types

| Type | What it tests | Correct answer |
|---|---|---|
| A | Clear regression: same bug, similar words | the old bug's id |
| B | Reworded regression: same bug in a user's words, almost no shared keywords | the old bug's id |
| C | Keyword decoy: shares words with an old bug, but the cause is different | new |
| D | Clearly new bug | new |

There are two tiers:

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
- `results/`: saved model runs
- `NOTES.md`: build log

## Run

```sh
python validate.py          # check cases.json
python baseline.py --verbose
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

All 48 cases on Kaggle Benchmarks (commit `5897756`, run on 2026-10-06), 14 models:

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
stopped after 3 cases, so neither has a score. Every miss, with the model's reason, is in
`results/2026-10-06-kaggle-48-cases.json`; earlier runs are in `results/` too.

Five models score 48/48, so the benchmark doesn't separate the top tier. The hardest category is
expert D, the same kind of mistake made again in different code: 18 of 42 tries missed.
