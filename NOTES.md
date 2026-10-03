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

## Phase 3: First Kaggle test, and a hard tier (2026-10-03)

### What I asked for
- Save the first Kaggle test results in `results/` and here.
- The 12 cases are too easy, so keep them as tier "easy" and add 24 tier "hard" cases (6 per
  type) that strong models can still fail:
  - 12–15 fixed bugs per history.
  - Every A/B answer has 2–3 "siblings" (same component or cause, different defect), tracked in
    a `siblings` field.
  - At least 2 B cases are "same root cause, different screen".
  - C decoys turn on one specific detail, some matching the decoy's component and wording.
  - Messy reports: irrelevant details, log lines, wrong guesses.
- Keep the cue-word, null-component, answer-position and no-copied-data rules. Report every
  score per tier and per type.

### First Kaggle test (easy tier, 12 cases, commit e3c278a)
| Model | A | B | C | D | Total |
|---|---|---|---|---|---|
| google/gemini-3.8-flash | 3/3 | 3/3 | 3/3 | 3/3 | 12/12 |
| openai/gpt-5.4-nano-2026-03-17 | 3/3 | 2/3 | 2/3 | 3/3 | 10/12 |
| Baseline formula | 3/3 | 0/3 | 1/3 | 3/3 | 7/12 |

gpt-5.4-nano answered "new" on zb-06 (the double-sold seats) and fell for the zb-07 decoy,
citing the ₹1/day bug #823. Saved in `results/2026-10-03-first-kaggle-test.json`. I only kept
the summary, not the models' full output.

### What was built
- `cases.json`: 24 hard cases (zb-13 to zb-36). They come from 8 invented projects:
  pharmacy delivery, housing society, online exams, bike sharing, hospital lab, freelance
  invoicing, smart thermostat and transit cards. Each project has 13–14 fixed bugs, and its
  3 cases (different types) share that history, like three reports landing in one team's
  tracker. That keeps about 110 bugs to review instead of about 320.
- New fields on every case:
  - `tier`: easy or hard.
  - `siblings`: for A/B, the other history bugs that share the answer's component or cause.
  - `decoy_bug_id`: for C, the bug the report imitates.
  - `key_clue`: the exact words in the report that decide the case.
  The 12 easy cases got them too; their text didn't change.
- `validate.py`:
  - history size per tier (easy 5–8, hard 12–15)
  - siblings must be exactly the computed set, with 2–3 for hard regressions
  - a C case's decoy must be in its history
  - `key_clue` must be quoted exactly from the report
  - types balanced within each tier
  - the cue-word table per tier, failing on a leak inside either tier
  - an answer-position table, failing if over half the answers sit in one third of their history
- `baseline.py` and `kaggle_task.py`: a tier column per case, and a summary table by tier and
  type. The Kaggle score is the share passed across all 36 cases.

Cue words (reports with any): easy A 2, B 1, C 2, D 2; hard A 3, B 3, C 3, D 3.
Answer positions (first / middle / last third): easy 1/4/1, hard 4/4/4.

Baseline: easy 7/12 (58%), hard 6/24 (25%: A 2/6, B 0/6, C 1/6, D 3/6), all 13/36 (36%).

### What went wrong and how we fixed it
- **zb-23's first title echoed its answer.** "Your site says we're late a day early" shared 4
  keywords with #2643 ("Due date a day early…"), which breaks the B rule. I reworded it to
  "Marked overdue before the deadline". It now shares 0 with the answer, and 4 with sibling
  #2604 ("Overdue reminders…"), which is a fair lure for a hard case.
- **The formula can't tell siblings apart.** Keyword points stop at 4 shared words, so a
  sibling in the same component ties with the answer at 75, and the tie goes to the name that
  sorts first. On zb-13 it picked #2108 ("Dose reminders an hour late…") over the answer #2143
  ("Dose reminders fire twice…"). That's how the formula really behaves; I didn't change it.
- **The cause rule fires on any mention.** "Same cause" counts when the report names the cause,
  so a log line with `cache: HIT` (zb-33), a guess about "rounding" (zb-26) and "the timezone
  thing" (zb-32) each earn 25 points.
- **The easy answers sit mostly in the middle** (4 of 6 in the middle third). I left the
  approved easy cases alone; the position check runs over all 36, where it's 5/8/5.

### Notes for the write-up
- A model that always answers "new" scores exactly 50% (all of C and D), so 50% is the floor to
  beat. I checked this with a stand-in model locally.
- A hard prompt is about 5,400 characters (~1,350 tokens).
- The two "same root cause, different screen" cases (zb-20, zb-22) hinge on a log line or
  release note naming the code that the old bug's fix changed. The fix summary is the only place
  that names it, and the formula never reads fix summaries.

## Phase 4: Blind answer-key audit, and making the Kaggle run survive overload (2026-10-03)

### What I asked for
- Make zb-32 and zb-35 unambiguously "new": each report must rule out every timezone or clock
  bug in its history, and `why` must name them.
- An independent audit of the answer key by a fresh agent that never saw the answers, then a
  table of every disagreement with a keep / fix-the-case / fix-the-answer judgment.
- After my approval: the 6 fixes, a blind re-audit of just those 6, and a commit.
- After the first 36-case Kaggle run:
  - save the results, with gemini marked invalid
  - make `kaggle_task.py` retry 429/5xx with backoff, report failed calls as ERROR instead of
    wrong, and flag hallucinated and missing bug ids
  - add a way to rerun only one model's errored cases

### The audit method
- I gave a fresh agent only what a model sees: each case's fixed-bug history and new report,
  in the same prompt text `kaggle_task.py` builds. It never saw `expected`, `why`,
  `key_clue`, `siblings` or `decoy_bug_id`.
- The 36 cases were shuffled and renamed Q01–Q36, so neither the order (A cases first) nor
  the `zb-` ids gave anything away. The id mapping sat in a file the agent was told not to
  open, and it reported reading only the input file.
- It answered each case with a verdict, a bug id, a one-line reason and, when torn, a "doubt".

**Result: 34/36 agreed, then fixes.**
- **2 disagreements:** zb-01 and zb-02 (easy A). It called both "new".
- **4 agreed with doubts:** zb-03, zb-14, zb-15, zb-30.
- I fixed the wording of all six. **No answer changed.**
  - zb-01: reminder times "saved since Friday's deploy", not by a new feature.
  - zb-02: carts "with a percentage discount", the exact path #329 fixed.
  - zb-03: "the conflict-marker step was skipped" in CI.
  - zb-14: the add-on line includes "parking", #2222's original case.
  - zb-15: the log shows an autosave started *before* the submit.
  - zb-30: "the validator logged a single card read".
- A second fresh agent re-audited just those 6, shuffled and renamed R1–R6: **6/6 agreed**.
  zb-03 kept one doubt, the same as in the first audit: the conflict came from a new branch.

**The insight: "new code repeating an old mistake" reads as new.** The weakest cases all had
a report blaming a newly released feature that repeats a fixed bug's mistake (float money in a
new combo discount, naive times in a new recurring-appointments feature, a new EV add-on).
Under our rule (same defect in the same code path), a careful reader calls that "new", because
the fixed code didn't break; new code made the same mistake. A regression report has to show
the fixed path itself breaking again (a deploy, a revert, a skipped guard, the original
trigger). That rule also explains zb-03's lingering doubt, since every merge conflict is a
fresh event.

### zb-32 and zb-35
- **zb-32:** the report now says the evening exam "opened and closed on time" and the
  results page shows the right date; only the certificate PDF is wrong. That rules out
  #2301 (exams opening an hour late) and the timer bugs #2339 and #2304.
- **zb-35:** the report now says the schedule "never resumes, not even an hour late" on any
  day, and the neighbour's holiday ended "a week after the clock change". That rules out
  #2701 (an hour late) and #2736 (wrong days); #2711 only miscounted the energy report.
- Both auditors called both "new" with no doubt.
- **The validator caught a leak while I edited:** my first zb-35 wording, "the schedule never
  **comes back**", counts as the cue phrase "came back", which then appeared only in a new
  bug. I changed it to "never resumes".
- **Baseline side effect:** zb-32's new clue "opened and closed on time" shares words with
  #2301 ("Exams open an hour late"), and the formula can't read negation. It now calls zb-32 a
  regression, so the baseline's hard tier dropped from 6/24 to 5/24.

### First Kaggle run of all 36 cases
| Model | Easy | Hard (A / B / C / D) | All |
|---|---|---|---|
| google/gemini-3.8-flash | invalid | invalid | invalid: all 36 calls failed with 429 "heavy load" |
| openai/gpt-5.4-nano-2026-03-17 | 11/12 | 13/24 (5/6, 1/6, 2/6, 5/6) | 24/36 |
| Baseline formula | 7/12 | 5/24 (2/6, 0/6, 1/6, 2/6) | 12/36 |

- **The hard tier works:** nano went from 10/12 on easy-only to 13/24 on hard, with B (1/6) and
  C (2/6) the hardest.
- On zb-17 nano answered #2618. I first took that for a hallucinated id, but #2618 is a real
  bug in zb-17's history ("CSV export splits names with commas"), so it's a wrong pick. On
  zb-20 it said "regression" with no id.
- Saved in `results/2026-10-03-kaggle-36-cases.json`. Only the summary was kept, not the full
  output.

### What was built
- `kaggle_task.py`:
  - **Retries:** a call failing with 429, 5xx, a timeout or a dropped connection is retried
    after 5, 10, 20, 40, 60 and 60 seconds, which is 7 tries in all. Other errors (like a 400)
    aren't retried.
  - **Pacing:** a 1.5 s pause between cases.
  - **ERROR status:** a call that still fails is ERROR, not wrong. The summary shows
    passed/answered per tier and type, "errors: N", accuracy over answered cases and over all
    cases, and "RESULT INVALID: rerun" when over 10% of cases errored. The task's score is now
    accuracy over answered cases.
  - **Answer problems:** the summary also counts unreadable replies, missing ids (regression
    with no id, shown as "regression (no id)") and hallucinated ids (an id not in that case's
    history).
  - **Rerun:** each model's results are saved to `zombiebench_results_<model>.json` after
    every case. `zombiebench.run(llm=..., rerun_errors=True)` asks only the errored cases again
    and merges them in.
- `kaggle_paste.py` (git-ignored): `kaggle_task.py` without the auto-run lines, plus run code
  for one model.
- Tested locally with stand-in models. A model that's always overloaded gets 7 tries per
  case, 36 errors and RESULT INVALID. A flaky model passes after 2 retries. A 400 isn't
  retried. Missing, hallucinated and unreadable answers are each listed. A rerun asked only the
  5 errored cases and merged them.

### What went wrong and how we fixed it
- **The gemini run was all errors, and the old code scored errors as wrong.** It printed 0%
  for a model that never answered. That's why errors are now ERROR, kept out of the score, and
  flagged as invalid.
- **#2618 wasn't a hallucination.** The new check compares every id with the case's own
  history, so a wrong-but-real pick like that is counted as plain wrong.
