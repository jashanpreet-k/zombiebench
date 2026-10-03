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
- `embed_cases.py`: copies `cases.json` into `kaggle_task.py`
- `validate.py`: checks the cases, including that cue words like "again" don't give the answer away
- `results/`: saved model runs
- `NOTES.md`: build log

## Run

```sh
python validate.py          # check cases.json
python baseline.py --verbose
python embed_cases.py       # after editing cases.json
```

On Kaggle, paste `kaggle_task.py` into a Benchmarks notebook cell, then run
`%choose zombiebench` in the last cell. If the summary reports errors, run
`zombiebench.run(llm=kbench.llms["<model>"], rerun_errors=True)` to retry only those cases.

## Results

| | Easy | Hard (A / B / C / D) | All |
|---|---|---|---|
| openai/gpt-5.4-nano-2026-03-17 | 11/12 | 13/24 (5/6, 1/6, 2/6, 5/6) | 24/36 |
| Baseline formula | 7/12 | 5/24 (2/6, 0/6, 1/6, 2/6) | 12/36 |
| Always answering "new" | 6/12 | 12/24 | 18/36 |

google/gemini-3.8-flash's run is invalid (every call failed with 429 "heavy load") and is being
rerun. Saved runs are in `results/`.
