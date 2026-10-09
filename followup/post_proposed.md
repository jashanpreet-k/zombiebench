---
title: "Same Kind of Bug Isn't the Same Bug: Where AI Models Get Fooled"
published: true
cover_image: https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/cover.png
tags: devchallenge, kagglechallenge, ai, machinelearning
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

In a controlled test across 4 models, adding a confident wrong diagnosis reduced accuracy from 61/68 to 42/68 (27.9 percentage points). Each comparison used the same report, with only the comment changed.

I gave AI models (14 in my own runs, 17 on the official Kaggle leaderboard) a list of fixed bugs and one new bug report, and asked: is this an old bug coming back, or a new one? Most handle it well until the new bug is the same *kind* of mistake, made again in different code. In my runs, models missed 18 of 42 attempts on those cases, almost always by naming the old bug with the same kind of mistake. One model wrote that the bug was "now reoccurring in the night audit due to the scheduler change": it saw the code was different and still called it the same bug.

![Miss types across 14 ZombieBench model runs](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-miss-types.png)

Across 672 attempts (14 models × 48 cases), models got 592 right. Of the 80 misses, 55 were *false zombies*: a new bug called a regression. Only 17 went the other way. When these models are wrong, they're usually wrong in one direction: they see a familiar pattern and assume it's the old bug back.

## What I Benchmarked

### Why I built it

For the DEV Sanity Challenge I built Bug Graveyard, an app where fixed bugs get "buried" and a Zombie Detector warns you when one rises again. The detector is a simple formula: 25 points for the same cause, 15 for the same language, 25 for the same component, and up to 35 for shared keywords. At 60 or more, it's a zombie.

It worked in my demo, but I kept wondering whether an AI model would do better. ZombieBench is my attempt to answer that with numbers.

### How ZombieBench works

Every case gives the model a history of fixed bugs (name, cause, language, component, symptoms and fix summary) and one new bug report. The model must answer in JSON: `{"verdict": "regression" or "new", "bug_id": ..., "reason": ...}`. A case passes only if both the verdict and the bug id are right.

There are four case types:

| Type | What it is | Right answer |
|---|---|---|
| A | Clear regression: the same bug, described in similar words | the old bug's id |
| B | Reworded regression: the same bug in a user's own words | the old bug's id |
| C | Keyword decoy: sounds like an old bug, but the cause is different | new |
| D | A new bug (in the harder tiers, the same *kind* of mistake in different code) | new |

And three tiers:

- **Easy:** 12 cases with 5–8 fixed bugs each.
- **Hard:** 24 cases with 12–15 fixed bugs. Every right answer has 2–3 *siblings* (same component or same cause), so the model must pick the exact id. Reports are messy, with log lines, side issues and wrong guesses.
- **Expert:** 12 cases with 25–30 fixed bugs and similar-sounding names. Some have twin candidates that only a fix-summary detail separates, two issues in one report, or a *planted wrong diagnosis*: a developer or support comment that confidently names the wrong bug.

The tiers came from testing. My first 12 cases were too easy (gemini-3.8-flash got 12/12), so I added the hard tier. After gpt-5.5 got 36/36 on easy plus hard, I added the expert tier.

**Example (zb-41, expert B).** Two of its 27 fixed bugs:

- **#3325 Average buy price wrong after a stock split:** the quantity wasn't multiplied, so holdings showed a fifth of the shares. Fixed in `CorporateActions.apply_split()`.
- **#3374 Average buy price wrong after a bonus issue:** holdings showed twice the shares at the old average price, so the app showed a large loss. Fixed in `CorporateActions.apply_bonus()`.

The new report:

> Last month I got free Infosys shares, one for every one I already had. Since then the app says I'm down ₹42,000, which is about what I put in. It's as if the app thinks I paid for the free ones too. Support note on this ticket: 'The split bug, #3325, is back; splits and these go through the same code.'

Free shares, one for one, is a bonus issue, and the symptom matches #3374. The right answer is regression #3374; the support note is a deliberately planted incorrect diagnosis.

### How I made it fair

- **Invented data.** Every project, bug and report is made up. Nothing is copied from GitHub or an existing dataset.
- **Graded by code, not an LLM judge.** The answer must match exactly, and a reply that isn't the JSON I asked for counts as wrong. A call that fails (rate limits, or an empty reply from the model proxy) is retried with backoff and then reported as an error, not scored.
- **Leak checks.** My validator fails if a cue phrase like "again", "still" or "used to" (or a missing component) appears only in regressions or only in new bugs. Otherwise a model could score just by spotting "again".
- **Blind audits.** The build log records blind audits and revisions for the original cases, but their raw audit answers were not archived. For the follow-up, fresh agents answered shuffled prompts without the answer key; the prompts, answers and agreement checks are archived in the repository.
- **Baselines.** Always answering "new" scores 24/48, so that's the floor to beat. My Bug Graveyard formula scores 15/48, worse than guessing.

## Models Tested

I picked a spread on purpose: frontier models, plus the smaller and open-weight models that are cheap enough to run on every incoming ticket, because those are the ones a team would actually use for triage.

I ran 16 models, from frontier down to small and open-weight ones, on the same 48 cases, once each. Two didn't finish: xai/grok-4.6 returned "404 – model not found" on every call, and I stopped deepseek-r1-0528 after 3 slow cases. The 14 that finished had no API errors.

### My runs (per tier, with every miss saved)

| Model | Easy (12) | Hard (24) | Expert (12) | Expert D (3) | Total (48) |
|---|---|---|---|---|---|
| gpt-6.1-sol | 12 | 24 | 12 | 3 | **48** |
| claude-opus-5-5 | 12 | 24 | 12 | 3 | **48** |
| gemini-3.1-pro-preview | 12 | 24 | 12 | 3 | **48** |
| gpt-5.5 | 12 | 24 | 12 | 3 | **48** |
| gemini-3.8-flash | 12 | 24 | 12 | 3 | **48** |
| gemma-4-31b | 12 | 23 | 12 | 3 | **47** |
| gemini-2.5-flash | 12 | 22 | 8 | 1 | **42** |
| claude-sonnet-4-5 | 12 | 22 | 7 | 0 | **41** |
| gpt-5.4-mini | 12 | 21 | 8 | 2 | **41** |
| gemini-3.1-flash-lite-preview | 12 | 21 | 8 | 0 | **41** |
| gpt-oss-20b | 12 | 19 | 9 | 1 | **40** |
| claude-haiku-4-5 | 12 | 21 | 6 | 0 | **39** |
| qwen3-235b-a22b-instruct | 11 | 17 | 7 | 0 | **35** |
| gpt-5.4-nano | 9 | 13 | 4 | 2 | **26** |
| *Always answering "new"* | 6 | 12 | 6 | 3 | 24 |
| *Bug Graveyard formula* | 7 | 5 | 3 | 3 | 15 |

### Official Kaggle leaderboard

This is the saved leaderboard snapshot from publication: Kaggle's own run, one run per model, scored as accuracy over answered cases.

| Model | Kaggle score |
|---|---|
| GPT-6.1 Sol | 1.00 |
| GPT-5.5 | 1.00 |
| Claude Opus 5.5 | 1.00 |
| Gemini 3.1 Pro Preview | 1.00 |
| Gemini 3.7 Flash | 1.00 |
| Gemini 3.5 Flash | 1.00 |
| Gemma 4 31B | 1.00 |
| GLM-5 | 0.98 |
| Claude Opus 4.5 | 0.97 |
| GPT-5.4 mini | 0.88 |
| Claude Sonnet 4.5 | 0.88 |
| gpt-oss-20b | 0.88 |
| Gemini 3.1 Flash-Lite Preview | 0.85 |
| Claude Haiku 4.5 | 0.81 |
| Qwen 3 235B A22B Instruct | 0.73 |
| Gemini 2.5 Flash | 0.73 |
| GPT-5.4 nano | 0.55 |

gpt-oss-120b and Gemini 3.8 Flash were still running on Kaggle when I published, so they aren't in this archived table.

> **Note:** the original 48-case findings and quotes come from my own notebook runs, which saved every miss; Kaggle's official leaderboard run is separate. The controlled follow-up below was run through Kaggle's CLI and saved every response. Scores varied by up to 7 cases between runs (Gemini 2.5 Flash: 42/48 in my run, 0.73 or about 35/48 on Kaggle), so small gaps between models aren't meaningful.

![Heatmap of misses by model, tier, and case type](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-heatmap.png)

*Every miss from my runs. The dark column on the right is expert D: new bugs that repeat an old kind of mistake in different code.*

## Findings

### 1. "Same mistake, different code" is the hardest category

![Eight cases missed by the most models](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-hardest-cases.png)

Expert D cases are new bugs that repeat an old bug's *kind* of mistake in code its fix never touched, and the report holds the clue. In zb-46, a hotel's new night-audit scheduler starts at 00:00 UTC, so early walk-ins land on the previous day, while the occupancy report (where old timezone bug #3129 was fixed) shows them correctly.

Models missed expert D cases 18 times out of 42 (43%). The next hardest categories were at 21%. In 16 of the 18 misses, the model named the old bug with the same kind of mistake. From qwen3-235b:

> "...which is the same underlying timezone cause as in bug #3129, now reoccurring in the night audit due to the scheduler change."

It noticed the different code and still called it the same bug.

### Nine more same-mistake cases

![Accuracy on matched different-code and same-code cases](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-followup-code.png)

I added 9 different-code cases and 9 matched same-code regressions using the same histories. Different-code accuracy was 16/36, or 44.4% (Wilson 95%: 29.5–60.4%). Same-code accuracy was 36/36, or 100.0% (Wilson 95%: 90.4–100.0%). Models called 20/36 different-code cases regressions: a false-zombie rate of 55.6% (Wilson 95%: 39.6–70.5%). Both members were correct in 16/36 matched model–case pairs.

The matching guards against rewarding a model that always says “new.” These cases use explicit source traces and a repeated scaffold; they extend coverage, but their difficulty is not calibrated to the original expert tier.

### 2. Five models picked the bug a wrong support comment named

In zb-41 (the example above), 5 models selected the bug ID named in the support note: gpt-5.4-nano, gpt-5.4-mini, gemini-2.5-flash, gpt-oss-20b and qwen3-235b. From gpt-5.4-mini:

> "This matches the same corporate-action quantity/price adjustment defect as #3325, and the support note confirms splits and bonus issues share the same code path."

The expert tier has 5 planted wrong diagnoses. gpt-5.4-nano followed all 5, and no other model followed any of them except zb-41's. In zb-44 a developer writes "definitely #3318 again", while the alert log in the same report shows the alerts firing on time. From gpt-5.4-nano:

> "The developer comment and matching symptom indicate the same queue/batch processing issue from #3318 has reappeared on iOS."

### The follow-up: same report, different comment

![Wrong-target selection across comment conditions](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-followup-ladder.png)

Each of 4 models saw the same 17 reports in separate chats under five conditions: no comment (L0), an irrelevant confident meeting note (P), a hedged wrong diagnosis (L1), a confident wrong diagnosis (L2), and a developer claiming to have fixed that bug personally (L3). Only the terminal comment line changed; the correct answer did not. These are first-run results.

Both rate columns include descriptive Wilson 95% intervals.

| Comment | Correct: count; rate [95% CI] | Wrong target: count; rate [95% CI] |
|---|---|---|
| L0 | 61/68; 89.7% [80.2–94.9] | 5/68; 7.4% [3.2–16.1] |
| P | 61/68; 89.7% [80.2–94.9] | 4/68; 5.9% [2.3–14.2] |
| L1 | 57/68; 83.8% [73.3–90.7] | 5/68; 7.4% [3.2–16.1] |
| L2 | 42/68; 61.8% [49.9–72.4] | 14/68; 20.6% [12.7–31.6] |
| L3 | 46/68; 67.6% [55.8–77.6] | 18/68; 26.5% [17.4–38.0] |

On the paired L0/L2 comparison, 19 answers changed from correct to wrong and 0 changed from wrong to correct. The observed accuracy drop was 27.9 percentage points. The placebo accuracy change was 0.0 points; wrong-target selection changed by 19.1 points from L1 to L3.

Among the original planted-diagnosis cases, 7/20 model–case pairs were wrong at L2 and correct at L0. At L0 and P, “wrong target selected” means the ID named in the other conditions: there is no diagnostic comment to follow.

One L3 answer from `google/gemini-3.1-flash-lite-preview` on `zf1-zb-22-L3`:

> The report shows a value magnitude error consistent with unit conversion issues, and the developer confirmed the fix for #2511 is failing.

This comparison measures the effect of the whole inserted comment in this synthetic task. The L1-to-L3 comparison changes confidence and claimed authority together, so it cannot separate their effects. The placebo controls for one kind of extra text, not every semantic difference.

### 3. Right rejection, wrong answer

In zb-37, a developer blames #3108 (booking-page rounding), but the evidence points to the checkout invoice: #3174. Six models correctly rejected #3108 and then answered "new", and three of them named #3174 in their own reason. From Claude Sonnet 4.5, which answered "new":

> "This is a rounding issue in checkout invoices (component: invoices) matching bug #3174, not a regression of #3108 which was about booking confirmation page totals in the booking-engine component."

It found the right bug and still didn't pick it. Part of this is my fault; see the limits below.

### 4. A 31B open model kept up with the frontier

gemma-4-31b scored 47/48 in my run and 1.00 on Kaggle's official run. Its only miss in my run was zb-26, where a results page shows 88 marks out of 98 as 88%:

> "The report describes percentages being rounded down (88/98 displayed as 88%), which is identical to the defect in bug #2311."

But 88/98 is 89.8%, so rounding down would show 89%. The real bug is a wrong denominator.

### 5. The top tier is solved, so the rest is where it matters

Perfect scores in my runs (48/48): gpt-6.1-sol, claude-opus-5-5, gemini-3.1-pro-preview, gpt-5.5 and gemini-3.8-flash. On Kaggle's official run (1.00): GPT-6.1 Sol, GPT-5.5, Claude Opus 5.5, Gemini 3.1 Pro Preview, Gemini 3.7 Flash, Gemini 3.5 Flash and Gemma 4 31B. ZombieBench can't rank these. Below them, my runs go from 47 down to 26 and Kaggle's from 0.98 (GLM-5) to 0.55 (GPT-5.4 nano), and in my runs the misses cluster in the same places: same mistake in different code, planted diagnoses and keyword decoys. If you'd triage bug reports with a smaller model, those are the failure modes to check.

### What I'd do if I used AI for bug triage

- **Don't let a "regression" verdict close a ticket on its own:** most misses were false zombies, so check which code path the old fix touched.
- **Strip or flag comments that name a bug:** in zb-41, five models selected #3325, the ID named in the support note. That original observation alone was correlational; the follow-up above compares standardized comments with clean versions of the same reports.
- **Use a frontier model, or check the small one:** the top models got every case right, and the cheaper ones are where these mistakes showed up. These single runs on synthetic cases don't establish real-world reliability.

### Honest limits

- **Follow-up limits:** the added cases and comments are synthetic. All 4 included models have one full follow-up run; 1 has a second Experiment 1 run. Across valid comparable responses, 76/85 answers were identical (89.4%; Wilson 95% 81.1–94.3%), and 9 changed. Repeat agreement is not proof of general reliability. Pooled Wilson intervals treat observations as binomial trials and do not model dependence from shared cases or models. The headline uses first runs only. Two type-C selection exceptions were approved because only one eligible type-C source case was universally correct. Original planted comments were moved to the same terminal position; zb-39 now explicitly names its diagnosis’s ID.
- **Run correction:** the CLI initially bound nano explicitly, so one run scheduled under Gemini actually called nano. Saved SDK metadata identified the error. The platform’s extra initialization model is excluded from the headline comparison. That independent nano run supplies its repeat comparison; its extra expansion answers are excluded. The corrected task uses Kaggle’s selected-model placeholder, and actual model IDs are checked before pooling.
- **Availability:** Sonnet 4.5 was absent from Kaggle’s follow-up model catalog and was not replaced.

| Follow-up model | Full first runs | Full Experiment 1 repeats | Changed / valid comparable answers |
|---|---:|---:|---:|
| claude-haiku-4-5 | 1 | 0 | Not repeated |
| gemini-3.1-flash-lite-preview | 1 | 0 | Not repeated |
| gpt-5.4-mini-2026-03-17 | 1 | 0 | Not repeated |
| gpt-5.4-nano-2026-03-17 | 1 | 1 | 9/85 |


- **It's small:** 48 cases, and the expert tier has only 3 per type, so one case is a third of an expert type.
- **Scores vary between runs.** Gemini 2.5 Flash scored 42/48 in my notebook run and 0.73 (about 35/48) on Kaggle's official run, and gpt-5.4-nano scored 24/36 and then 22/36 on the same 36 cases in two of my runs. Small gaps between models aren't meaningful.
- **zb-37 has misfiled metadata.** Its report is filed under booking-engine and TypeScript, while the answer lives in invoices and Python. I meant it as realistic, but it pushes models toward "new", as gemini-2.5-flash said: "it is reported in a different language (TypeScript vs Python) and component (booking-engine vs invoices), indicating it's a new defect".
- **AI help.** I wrote the cases and built ZombieBench with help from Claude Code, reviewed every case myself, and checked every number against the results files. Blind AI audits checked the answer key, but the cases still come from one person's idea of fair.

### What I'd measure next

Next I would test less templated reports from independent authors and repeat the comparisons across more sampling settings.

## My Benchmark

- **Kaggle task (official leaderboard):** https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench
- **Controlled follow-up task:** https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench-followup
- **GitHub (code, all 48 cases, and every model's misses with its reason):** https://github.com/jashanpreet-k/zombiebench

Model names in "My runs" are shortened. The original full Kaggle model ids and both original leaderboards are in the repo's `results/` folder. Follow-up raw responses, model identities, intervals and per-model stability are in `followup/`.
