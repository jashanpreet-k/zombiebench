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

## Phase 5: Loading the code from GitHub, and Claude Haiku 4.5's run (2026-10-03)

### What I asked for
- Copying the 4,000-line block into Kaggle kept failing, so load the code from GitHub instead:
  - a `kaggle_paste.py` that only defines things, plus `run_models(models)`
  - commit it, and push to a new public repo, jashanpreet-k/zombiebench
  - no secrets in the repo
- No AI attribution on GitHub: rewrite the existing commits to drop every "Co-Authored-By:"
  line before the first push, and never add one again in this repo.
- Save Claude Haiku 4.5's run of all 36 cases, and note the pattern in its misses.

### What was built
- `kaggle_paste.py`: generated from `kaggle_task.py` by `embed_cases.py`. It's
  `kaggle_task.py` without the last two lines, so loading it calls no model.
- `run_models(models, rerun_errors=False)` in `kaggle_task.py`: checks every model name first,
  then runs each one with the retries and error reporting from Phase 4.
- `validate.py` fails if `kaggle_paste.py` is out of date.
- Repo: https://github.com/jashanpreet-k/zombiebench. On Kaggle:
  ```python
  import urllib.request
  exec(urllib.request.urlopen("https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/kaggle_paste.py").read().decode())
  run_models(["google/gemini-3.8-flash"])
  ```
- The 4 commits before the push were rewritten without their Co-Authored-By lines. Authors,
  committers, dates and file contents didn't change, but the hashes did, so the first test's
  results now point at `e3c278a` instead of `15ce866`.
- `results/2026-10-03-claude-haiku-4-5.json`.

### Claude Haiku 4.5 (anthropic/claude-haiku-4-5@20251001), all 36 cases, 0 errors
| | A | B | C | D | All |
|---|---|---|---|---|---|
| easy | 3/3 | 3/3 | 3/3 | 3/3 | 12/12 |
| hard | 6/6 | 6/6 | 6/6 | 3/6 | 21/24 |
| all | 9/9 | 9/9 | 9/9 | 6/9 | **33/36 (92%)** |

No unreadable replies, missing ids or hallucinated ids.

**The pattern: all 3 misses are hard D cases.** In each, the new bug shares a cause *category*
with a history bug, and the model called it that bug coming back. Its reasons say "same" or
"analogous":
- **zb-32 → #2301 (timezone):** "…causing the same timezone handling issue that was fixed in the
  exam-timer component." The report says the exam opened on time and only the certificate PDF
  is wrong.
- **zb-33 → #2408 (cache):** "…is analogous to the map cache bug where old data persisted…"
  #2408 kept bike positions stale on the map; this serves one rider's history to another.
- **zb-36 → #2825 (a year-end date):** "…the same root cause as passes showing expiry a day
  early." Here the model followed the report's own wrong guess ("Maybe a timezone problem?").
  But in India, showing a time in UTC moves it *earlier*, so UTC can never push 29–31 December
  into the next year. The real cause is a week-based-year date format.

So the model treats "the same kind of bug" as "the same bug". That's the opposite of the
audit's "new code repeating an old mistake" lesson, seen from the model's side. Hard D cases
are where that confusion shows.

### What went wrong and how we fixed it
- **I couldn't create the repo from here:** `gh` isn't installed, and I didn't want to pull a
  token out of the keychain. I created the empty repo on github.com myself, then pushed.
- **The commit rewrite left 2 stale hashes** (in NOTES and the first test's results). Both now
  point at the rewritten commit.
- **Loading with `exec()` hides the task's source from Kaggle.** It printed "Could not get
  source code for task 'zombiebench'", because `inspect.getsource` can't read code that came
  from a string. That doesn't affect results, but a leaderboard task saved this way would carry
  no source code. For the final run, save the downloaded file to disk and import it (or paste
  it into a cell), and load it from a URL pinned to a commit instead of `main`.

### Notes for the write-up
- Results so far:
  - Claude Haiku 4.5: 33/36
  - gpt-5.4-nano: 24/36
  - always answering "new": 18/36
  - the Bug Graveyard formula: 12/36
- Haiku's only weakness is "same cause category, different defect". A strong model gets every
  A, B and C case, so the separation lives in hard D.

## Phase 6: Four models on 36 cases, empty replies, and an expert tier (2026-10-03)

### What I asked for
- Save the 36-case results for gpt-5.5, claude-opus-5, Claude Haiku 4.5 and gpt-5.4-nano.
- Retry an empty proxy response ("message=None") with the same backoff, count it as ERROR
  (not "unreadable") if it stays empty, and let `rerun_errors` re-ask it.
- A third tier, "expert": 12 cases (3 per type) that frontier models can still fail but that
  stay fair and answerable from the text. They should include:
  - 25–30 fixed bugs per history, with similar-sounding names
  - "same mistake class, different bug"
  - "twin candidates" decided only by a fix-summary detail
  - two issues in one report
  - a confident but wrong diagnosis inside the report
- A blind audit of the 12 expert cases, then a push.

### Results on the 36 easy and hard cases
| Model | Easy | Hard | All 36 |
|---|---|---|---|
| gpt-5.5 | 12/12 | 24/24 | **36/36** |
| claude-opus-5 | | | **35/36**; the miss was an empty proxy response, so 35/35 answered |
| Claude Haiku 4.5 | 12/12 | 21/24 (D 3/6) | **33/36** |
| gpt-5.4-nano | 11/12 | 13/24 (B 1/6, C 2/6) | **24/36** |
| Always answering "new" | 6/12 | 12/24 | 18/36 |
| Baseline formula | 7/12 | 5/24 | 12/36 |

Two frontier models are at or near 100%, so the 36 cases no longer separate the strongest
models. That's why I added the expert tier. Saved in
`results/2026-10-03-kaggle-36-cases-four-models.json`.

### Empty proxy responses
- Kaggle's model proxy sometimes returns `choices[0].message=None`. The library logs it and
  returns an empty string, which our parser called "unreadable" (a wrong answer). That's what
  happened to claude-opus-5 on zb-20.
- `ask()` now treats an empty or blank reply like a 429: retry after 5, 10, 20, 40, 60, 60 s,
  then ERROR ("empty response from the model proxy (message=None) on every try").
- `rerun_errors=True` re-asks ERROR cases, and also cases an older run saved as "unreadable"
  with an empty reply, so results saved before this fix can still be repaired.

### The expert tier (zb-37 to zb-48)
- **3 invented projects with 27–28 fixed bugs each:** a hotel booking system, a stock-trading
  app and a video-streaming service. Each project has one case of each type sharing its
  history.
- **Similar-sounding names on purpose:** "…a rupee off…" ×4, "Special requests…" ×3,
  "Stop-loss orders fire…" ×2, "Price alerts…" ×4, "Subtitles…drift out of sync…" ×2,
  "…'link expired'…" ×2.
- **Which case uses which element:**
  - **Twin candidates:** zb-37 (booking-page vs invoice rounding), zb-41 (bonus vs split),
    zb-39 (subtitle converter vs Android TV pause), zb-42 (signed URLs vs live tokens); zb-43
    matches neither twin.
  - **Confident wrong diagnosis:** zb-37 and zb-41 (the wrong twin is named), zb-44 and
    zb-45 ("definitely #… again", but it's new).
  - **Two issues in one report:** zb-38 (double stop-loss plus grey logos), zb-40 (lost cot
    request plus logouts).
  - **Same mistake class, different code:** zb-46 (timezone, new night-audit scheduler),
    zb-47 (rounding, capital gains report), zb-48 (stale data in downloads), plus zb-43
    and zb-45.
- **Checks kept:**
  - cue words balanced within the tier: any cue word in A 2/3, B 3/3, C 2/3, D 2/3
  - null components in both regressions and new bugs
  - answers spread 2 / 2 / 2 across the first, middle and last third of the history
  - key clues quoted exactly
  - siblings computed (expert regressions have 2–6 each)
- **Baseline on expert:** 3/12 (A 0/3, B 0/3, C 0/3, D 3/3). All 48: 15/48.

### What went wrong and how we fixed it
- **The leak check caught the wrong diagnoses.** "The overnight batch **is back**" (zb-44) and
  "the rating filter **regressed**" (zb-45) appeared only in new bugs. Developers say the same
  about real regressions, so the wrong diagnoses in zb-37 (A) and zb-41 (B) now say
  "…regressed" and "…is back" too.
- **Two expert B reports echoed their answers.** zb-40 and zb-42 shared 3 and 5 keywords with
  their answers ("clock", "link", "phone", "because"…). I reworded them in a user's own words
  ("My TV's time runs 20 min fast", "an error says the video address has run out"). They now
  share 0.

### Blind audit of the expert tier
Same method as Phase 4: a fresh agent saw only each case's history and report, shuffled and
renamed E1–E12. **It agreed on 12/12.** Its one doubt was zb-40: the report implies but doesn't
prove that the cot request was on record before the date change, so it could have been #3115
(the housekeeping list hiding requests) or a new bug.

I fixed zb-40's wording. The guest's first confirmation email now lists "Baby cot" under
requests, and "The new confirmation email has no requests at all" (the new key clue). That
shows the request was saved and then lost on the date change. A second fresh agent re-audited
just zb-40 blind: regression #3139, **no doubt**.


## Phase 7: The 48-case leaderboard (2026-10-06)

### What I asked for
- Save the 48-case Kaggle results (commit `5897756`, run on 2026-10-06), with grok-4.6 marked
  unavailable and deepseek-r1 marked not completed.
- Write up five findings, after checking every count against the results file.
- Update the README with the full leaderboard, then commit and push.

### Leaderboard: 48 cases, 14 models
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

- **Not completed:**
  - xai/grok-4.6 was listed in `kbench.llms`, but every call returned "404 - model not found"
    (stopped after 31 cases).
  - deepseek-ai/deepseek-r1-0528 was very slow; I stopped it by hand after 3 cases (all 3
    correct).
- **Errors:** none on any completed model.
- **Saved:** `results/2026-10-06-kaggle-48-cases.json` has every model's per-tier and
  per-type scores and all 80 misses with the model's reason.
- **Checked:** every model's table matches its own list of misses, and every miss's expected
  answer matches `cases.json`.

### Findings (each count checked against the results file)
1. **Expert D ("same mistake, different code") is the hardest category.**
   - zb-46 was missed by 6 models, zb-47 by 5 and zb-48 by 7.
   - That's 18 of 42 tries (43%). The next hardest categories are hard C and expert A, at 21%
     each.
   - 16 of the 18 expert D misses name the history bug with the same *kind* of mistake:
     #3129 (UTC day cut), #3336 or #3308 (rounding), #3571 (catalog cache).
   - The two exceptions: Haiku on zb-48 picked #3574 (renewed downloads), and gpt-5.4-nano on
     zb-46 named #3110, which isn't in the history.
2. **Planted wrong diagnoses.** In zb-41 a support comment wrongly says "#3325 is back".
   - 5 models followed it: gpt-5.4-nano, gpt-5.4-mini, gemini-2.5-flash, gpt-oss-20b and
     qwen3-235b.
   - gpt-5.4-nano followed all 5 planted wrong diagnoses: zb-37 (→ #3108), zb-39 (→ #3539),
     zb-41 (→ #3325), zb-44 (→ #3318) and zb-45 (→ #3518).
   - No other model followed any planted diagnosis except zb-41's.
3. **zb-37: right rejection, wrong answer.**
   - 6 models rejected the developer's wrong #3108 but answered "new" instead of #3174:
     gemini-2.5-flash, Sonnet 4.5, gpt-5.4-mini, gemini-3.1-flash-lite, Haiku 4.5 and qwen3.
   - Three of those reasons name #3174 itself: Sonnet 4.5 ("matching bug #3174"),
     gemini-3.1-flash-lite ("aligning it with the logic addressed in #3174") and
     gemini-2.5-flash.
   - gemini-2.5-flash says outright that the report's language and component (TypeScript,
     booking-engine) are why it answered "new". See the limit below.
4. **An open 31B model nearly matches the frontier.** google/gemma-4-31b scored 47/48. Its only
   miss was zb-26 (hard C), where it called 88/98 shown as 88% "identical" to the rounding bug
   #2311.
5. **The benchmark doesn't separate the top tier.** Five models scored 48/48: gpt-6.1-sol,
   claude-opus-5-5, gemini-3.1-pro-preview, gpt-5.5 and gemini-3.8-flash.

### Other observations
- **qwen3-235b's one unreadable reply** (zb-25) wrote the key as `"bug\n_id"`, with a newline
  inside it. The verdict it started ("new") would have been correct.
- **gpt-5.4-nano varies between runs.** On the same first 36 cases it scored 24/36 on
  2026-10-03 and 22/36 now (easy 11/12, then 9/12). Haiku 4.5 was stable: 33/36 both times,
  with the same three hard D misses.
- **The most-missed single cases** are zb-37 and zb-48 (7 models each), then zb-46 and zb-25
  (6 each).

### Limits
- **zb-37's report has a misfiled component and language** (booking-engine, TypeScript, though
  the answer is in invoices, Python). That pushes models toward "new", and gemini-2.5-flash
  says so explicitly. It was meant to be a realistic misfiling, but it makes this case partly a
  test of ignoring metadata, not only of reading the evidence.
- **The top tier is saturated:** five models are at 48/48, and an open 31B model is one case
  behind.
- **Each model ran once**, and gpt-5.4-nano moved by 2 cases between runs, so differences of a
  case or two between models aren't meaningful.
- **Expert has 3 cases per type**, so expert per-type scores move in steps of 33%.

### What went wrong and how we fixed it
- I'd said "13 models"; the file has **14 completed models** (16 attempted). The README and this
  log list all 14.
- I credited only Sonnet 4.5 with naming #3174 on zb-37; gemini-2.5-flash and
  gemini-3.1-flash-lite name it too.
- I made the results summary file by hand and deleted it after saving the results JSON. It
  isn't committed.
