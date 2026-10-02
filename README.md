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

All cases are invented for this benchmark.

## Files

- `cases.json`: the cases
- `baseline.py`: the Bug Graveyard Zombie Detector formula, as a baseline
- `kaggle_task.py`: the Kaggle Benchmarks task (one file, cases embedded)
- `embed_cases.py`: copies `cases.json` into `kaggle_task.py`
- `validate.py`: checks the cases, including that cue words like "again" don't give the answer away
- `NOTES.md`: build log

## Run

```sh
python validate.py          # check cases.json
python baseline.py --verbose
python embed_cases.py       # after editing cases.json
```

On Kaggle, paste `kaggle_task.py` into a Benchmarks notebook cell, then run
`%choose zombiebench` in the last cell.

## Results

Baseline (12 cases): A 3/3, B 0/3, C 1/3, D 3/3, overall 7/12 = 58%. Model results to come.
