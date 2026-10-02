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
  I reworded both. (Correction from Phase 2: zb-05 and zb-06 share 0 keywords with their
  answer, but zb-04 shares 1, "names". I had reported all three as 0.)
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
- In Phase 1, decoys (C) scored 75 on the formula: same language + same component + 5–7 shared
  keywords. Keywords and component alone are enough to cross 60 without any shared cause.

## Phase 2: Fixes from my review of the first 12 cases (2026-10-02)

### What I asked for
Three fixes before growing the set:
1. Remove cue-word leaks: "again", "still", "came back", "used to work", "stopped working" must
   not only appear in regressions. Put them in at least 1 C and 1 D report, take them out of at
   least 1 A report, and make `validate.py` count them per type.
2. Make the baseline comparison fair: a component in at least 1 B report (the screen the report
   came from), a null component in at least 1 C or D report, and at least 1 C decoy in a
   different component from its decoy bug. Nothing tuned toward the formula passing or failing.
3. For every C case, the report's own text must contain the evidence for the different cause.

### What was built
- `cases.json`:
  - zb-03 (A) title lost "again", and zb-02 (A) lost "is back".
  - zb-07 (C) says "again", like an HR person who remembers the old ₹1 bug would.
  - zb-08 (C) and zb-10 (D) say "used to".
  - zb-12 (D) lost an incidental "counting up again".
  - zb-05 (B) now gives the component `streaks`, the screen the report came from.
  - zb-12 (D) has a null component, as if filed by the field team.
  - zb-09 (C) is filed under `media`, because the developer traced the crash to thumbnails.
- `validate.py`:
  - B reports may now give a component.
  - New leak table: for each cue word and for a null component, how many reports of each
    type have it. It fails if one shows up only in regressions or only in new bugs.
- `kaggle_task.py`: re-embedded; a failed model call now prints "no reply".

Cue words per type (reports with any): A 2, B 1, C 2, D 2. Null component: A 0, B 2, C 0, D 1.
Baseline: A 3/3, B 0/3, C 1/3, D 3/3, overall 7/12 = 58% (was 6/12).

### What went wrong and how we fixed it
- My Phase 1 summary said every B report shares 0 keywords with its answer. zb-04 shares 1
  ("names"). I corrected the Phase 1 entry.
- Two D reports already had "again" by accident ("fast again", "counting up again"), so D wasn't
  free of cue words before. But neither one claimed a bug came back. I kept zb-11's, removed
  zb-12's, and gave zb-10 a real "used to be readable" so D has one genuine regression-sounding
  phrase without having more cue words than A.
- I tested the leak check on a copy with the C and D cue words removed. It flagged
  'again', 'used to' and 'any cue word' as only appearing in regressions.
- All three C reports already contained their evidence sentence; no text was added for that.

### Notes for the write-up
- zb-09 now scores 50 (language 15 + keywords 35, no component), so the formula gets it right.
  When a decoy sits in another component, the formula's 25 component points are what stop it.
- A B report with a component can now reach 60 in principle (15 + 25 + 35 × keywords), but
  zb-05 scores 40 for its answer and 49 for the other streak bug (#621), because it shares
  almost no words with the bug it really is.
