# ZombieBench build log

## Phase 1: First 12 cases, baseline and Kaggle task (2026-10-02)

### What I asked for
A Kaggle benchmark for the DEV Kaggle Benchmarking Challenge (deadline Oct 11, 11:59 PM PDT).
The question: given a few fixed bugs and one new report, can a model say "this is bug #N coming
back" or "this is new", and does it beat my Bug Graveyard formula? Step 1 was:

- `cases.json` with 12 invented cases, 3 of each type: A clear regression, B reworded regression,
  C keyword decoy, D clearly new.
- `baseline.py`: my Bug Graveyard formula (25 cause + 15 language + 25 component +
  35 × min(shared keywords, 4)/4, regression at 60 or more), using only what the report says.
- `kaggle_task.py`: one file to paste into a Kaggle Benchmarks notebook, JSON-only answers,
  parsed defensively, a case passes only when the verdict and bug_id are both right.
- `validate.py`, this log, a README stub, and a local git commit. No secrets, nothing copied
  from GitHub or a dataset, plain Python.

### What was built
- `cases.json`: 12 cases, each a different invented project (clinic booking, food delivery,
  school portal, expense splitting, meditation app, concert tickets, payroll, travel booking,
  chat app, warehouse, library, weather stations), with 5–8 fixed bugs each.
- `baseline.py`: a line-by-line port of `bug-graveyard/sanity/lib/detector.ts` (same stop
  words, DST/TZ aliases, stemming, rounding and tie-break). `--verbose` shows each signal.
- `kaggle_task.py`: the `zombiebench` task. Each case is asked in a fresh chat, the reply is
  scanned for the first JSON object with a `verdict`, and the task returns the share passed.
- `embed_cases.py`: copies `cases.json` into `kaggle_task.py`'s `CASES` block.
- `validate.py`: checks fields, answers vs. types, bug ids in history, balance, duplicates,
  and that `kaggle_task.py` carries the same cases as `cases.json`.
- `README.md` stub and `.gitignore` (keeps `kaggle.json` and `.env*` out of git).

Baseline result: A 3/3, B 0/3, C 0/3, D 3/3, overall 6/12 = 50%.

### What went wrong and how we fixed it
- **The report has no cause field**, so "same cause" needed a rule. The baseline gives the 25
  cause points only when the report's own title or description names the history bug's cause
  (e.g. "timezone", "merge conflict"). It never reads `expected`.
- **B cases can't reach 60 by construction.** With no component and no cause named, the best a
  B report can score is 15 + 35 = 50, so the formula always says "new" on B. That's the gap the
  benchmark is meant to show, but it's worth saying out loud in the write-up.
- **Two B reports leaked keywords.** My first zb-05 report said "I haven't reinstalled anything
  or changed phones", which shared 3 keywords with the *other* streak bug (#621) and turned the
  case into half a decoy. My first zb-06 report shared "same" and "moment" with its answer.
  I reworded both; every B report now shares 0 keywords with its answer.
- **`tuple[int, int]` isn't supported on the leaderboard yet.** The library's source says
  `PassCount`: "Note the backend doesn't support PassCount yet." The task returns a `float`.
- **Failed assertions fail the whole run.** `Run.passed` requires every assertion to pass, so
  per-case `assert_true` calls would mark any imperfect model as failed. The task prints a
  per-case table instead and returns the score.
- **`%choose zombiebench` is an IPython magic**, so it can't live in a `.py` file. It goes in
  the notebook's last cell (the docstring says so).
- I tested `kaggle_task.py` locally with a stand-in `kaggle_benchmarks` module (outside the
  repo): perfect answers score 1.0, garbage text and failing model calls score 0.0, and the
  run finishes in every case.

### Notes for the write-up
- The keyword stemmer is inherited from Bug Graveyard as is, including a quirk: "names" stems to
  "nam" but "name" stays "name", so they don't match. I kept it for a faithful baseline.
- Decoys (C) score 75 on the formula: same language + same component + 5–7 shared keywords.
  Keywords and component alone are enough to cross 60 without any shared cause.
