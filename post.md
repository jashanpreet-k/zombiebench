---
title: "Same Kind of Bug Isn't the Same Bug: Where AI Models Get Fooled"
published: true
tags: devchallenge, kagglechallenge, ai, machinelearning
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

I gave AI models (14 in my own runs, 17 on the official Kaggle leaderboard) a list of fixed bugs and one new bug report, and asked: is this an old bug coming back, or a new one? Most handle it well until the new bug is the same *kind* of mistake, made again in different code. In my runs, models missed 18 of 42 attempts on those cases, almost always by naming the old bug with the same kind of mistake. One model wrote that the bug was "now reoccurring in the night audit due to the scheduler change": it saw the code was different and still called it the same bug.

![Miss types across 14 ZombieBench model runs](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-miss-types.png)

Across 672 attempts (14 models × 48 cases), models got 592 right. Of the 80 misses, 55 were **false zombies**: a new bug called a regression. Only 17 were **missed zombies**: a true regression called new. In these runs, false-zombie verdict errors outnumbered missed-zombie verdicts; the counts describe the answers, not why a model chose them.

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
- **Blind audits.** A fresh AI agent that never saw the answer key answered every case. On the first 36 it agreed on 34. Its disagreements showed that a report blaming a *new* feature for repeating an old mistake reads as a new bug, so I reworded 6 cases (no answers changed), and a second blind audit agreed on all 6. On the expert tier it agreed on 12 of 12; I fixed its one doubt and re-audited that case.
- **Baselines.** Always answering "new" scores 24/48, so that's the floor to beat. My Bug Graveyard formula scores 15/48, worse than guessing.

## Models Tested

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

This is the leaderboard the Kaggle link shows: Kaggle's own run, one run per model, scored as accuracy over answered cases.

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

gpt-oss-120b and Gemini 3.8 Flash were still running on Kaggle when I published, so they aren't in this table.

> **Note:** all findings and quotes below come from my own notebook runs, which saved every miss; Kaggle's official run is separate. Scores varied by up to 7 cases between runs (Gemini 2.5 Flash: 42/48 in my run, 0.73 or about 35/48 on Kaggle), so small gaps between models aren't meaningful.

![Heatmap of misses by model, tier, and case type](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-heatmap.png)

*Every miss from my runs. The dark column on the right is expert D: new bugs that repeat an old kind of mistake in different code.*

## Findings

### 1. "Same mistake, different code" is the hardest category

![Eight cases missed by the most models](https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/charts/zombiebench-hardest-cases.png)

Expert D cases are new bugs that repeat an old bug's *kind* of mistake in code its fix never touched, and the report holds the clue. In zb-46, a hotel's new night-audit scheduler starts at 00:00 UTC, so early walk-ins land on the previous day, while the occupancy report (where old timezone bug #3129 was fixed) shows them correctly.

Models missed expert D cases 18 times out of 42 (43%). The next hardest categories were at 21%. In 16 of the 18 misses, the model named the old bug with the same kind of mistake. From qwen3-235b:

> "...which is the same underlying timezone cause as in bug #3129, now reoccurring in the night audit due to the scheduler change."

It noticed the different code and still called it the same bug.

### 2. Five models picked the bug a wrong support comment named

In zb-41 (the example above), 5 models selected the bug ID named in the support note: gpt-5.4-nano, gpt-5.4-mini, gemini-2.5-flash, gpt-oss-20b and qwen3-235b. From gpt-5.4-mini:

> "This matches the same corporate-action quantity/price adjustment defect as #3325, and the support note confirms splits and bonus issues share the same code path."

The expert tier has 5 planted wrong diagnoses. gpt-5.4-nano followed all 5, and no other model followed any of them except zb-41's. In zb-44 a developer writes "definitely #3318 again", while the alert log in the same report shows the alerts firing on time. From gpt-5.4-nano:

> "The developer comment and matching symptom indicate the same queue/batch processing issue from #3318 has reappeared on iOS."

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

- **Don't let a regression verdict close a ticket on its own.** In these runs, false-zombie errors outnumbered missed-zombie errors. I'd ask which code path the old fix touched and whether the new report concerns that same code.
- **Treat comments that name a bug as claims to verify.** In zb-41, five model outputs selected #3325, the ID named in the support note. There was no run without that note, so these results don't show that it changed the answers.
- **Use a model that scored well here, and review the others.** Five models got all 48 cases right in these single runs; lower-scoring runs had misses. This synthetic benchmark doesn't establish real-world reliability.

### Honest limits

- **It's small:** 48 cases, and the expert tier has only 3 per type, so one case is a third of an expert type.
- **Scores vary between runs.** Gemini 2.5 Flash scored 42/48 in my notebook run and 0.73 (about 35/48) on Kaggle's official run, and gpt-5.4-nano scored 24/36 and then 22/36 on the same 36 cases in two of my runs. Small gaps between models aren't meaningful.
- **zb-37 has misfiled metadata.** Its report is filed under booking-engine and TypeScript, while the answer lives in invoices and Python. I meant it as realistic, but it pushes models toward "new", as gemini-2.5-flash said: "it is reported in a different language (TypeScript vs Python) and component (booking-engine vs invoices), indicating it's a new defect".
- **AI help.** I wrote the cases and built ZombieBench with help from Claude Code, reviewed every case myself, and checked every number against the results files. Blind AI audits checked the answer key, but the cases still come from one person's idea of fair.

### What I'd measure next

More "same mistake, different code" cases, since that's where models split, and several runs per model to measure how noisy the scores are.

## My Benchmark

- **Kaggle task (official leaderboard):** https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench
- **GitHub (code, all 48 cases, and every model's misses with its reason):** https://github.com/jashanpreet-k/zombiebench

Model names in "My runs" are shortened. The full Kaggle model ids, and both leaderboards, are in the repo's `results/` folder.
