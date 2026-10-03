# ZombieBench

*Work in progress for the DEV Kaggle Benchmarking Challenge.*

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

| | Easy | Hard (A / B / C / D) | All |
|---|---|---|---|
| openai/gpt-5.4-nano-2026-03-17 | 11/12 | 13/24 (5/6, 1/6, 2/6, 5/6) | 24/36 |
| Baseline formula | 7/12 | 5/24 (2/6, 0/6, 1/6, 2/6) | 12/36 |
| Always answering "new" | 6/12 | 12/24 | 18/36 |

google/gemini-3.8-flash's run is invalid (every call failed with 429 "heavy load") and is being
rerun. Saved runs are in `results/`.
