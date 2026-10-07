# ZombieBench controlled follow-up

This is a separate experiment. The original benchmark, result files, article source and live DEV post are unchanged. No Kaggle model runs have been executed for this follow-up yet.

## Design and departures from the requested selection

**Experiment 1:** 17 clean/planted pairs (34 unique prompts). Run both arms twice per model, in fresh chats, with identical prompts and provider settings in both repetitions. The original prompt and parser/grader are frozen in `grading.py`; evaluation metadata is never sent to a model.

- Added-comment sample: zb-13, zb-14, zb-15 (A); zb-04, zb-05, zb-22 (B); zb-07, zb-09, zb-27 (C); zb-10, zb-12, zb-34 (D). Three per type; six easy and six hard.
- Only zb-09 among easy/hard C cases was correct in all 14 completed source runs. With the author's explicit approval, zb-07 and zb-27 are exceptions: each was missed by one model. Among equally eligible one-miss candidates, choose lowest case ID (zb-07, zb-27 before zb-28). The other ten selected cases had no misses. Report these exceptions; do not call all 12 universally solved.
- A/B comments name an actual sibling; C comments name the recorded decoy. Original D cases have no `decoy_bug_id` by schema, so the wrong historical target is recorded separately as `comment_bug_id` (zb-10 → #1105, zb-12 → #1311, zb-34 → #2629). These are symptom-level distractors, not previously designated gold-data decoys.
- Removed-comment sample: zb-37, zb-39, zb-41, zb-44, zb-45. The planted arm preserves the original report byte-for-byte; the clean arm deletes only the specified comment substring. In zb-39 the team names the pause diagnosis, not an explicit numeric ID. Its associated history target is #3539; flag this distinction in any write-up.
- Existing non-treatment wording (including guesses elsewhere in a report and zb-37's misfiled metadata) is deliberately retained. “Clean” means the experimental comment is absent, not that all other distractions are removed.
- `twin_diffs.md` shows the model-prompt diff for **every** pair. All other report fields, history and gold answers are identical within each pair.

**Experiment 2:** Nine new different-code bugs (D) plus nine matched same-code regressions (A). Within each pair, the histories, title, language and component are identical. The failing route and the working control route exchange roles. Source snapshots identify whether the defective operation is in the function covered by the old patch or its independent implementation. Each history has 27 bugs including related alternatives; answer positions are balanced across the first, middle and last third.

Domains: cold-chain dispatch, water billing, library circulation, pathology administration, EV charging, drone planning, satellite operations, energy settlement and transit alerts. Mistakes: timezone, rounding, caching, null handling, races and units. The histories intentionally use a common distractor scaffold with domain-specific entities; these are expert-style histories, not yet empirically calibrated expert-difficulty items. Explicit route evidence may make them easier than the original expert D cases. This tests transfer of the same/new distinction, not real-world bug-triage accuracy.

## Quality gates completed

- `python3 -B followup/validate.py`: passes. Reuses root `validate.py` checks without modifying it. Checks source eligibility/exceptions, IDs, exact comment-only changes, gold preservation, counts, embedded prompt fields, matched histories and equal cue counts within each Exp2 pair.
- `python3 -B followup/check_audit.py`: fresh agent with no inherited conversation, restricted to shuffled prompt text without answers, labels, case IDs or pair metadata. **34/34 Exp1 and 18/18 Exp2 agreement; no ambiguities.** No rewording/re-audit was required. The first attempt was blocked by account quota; the retry after the reset completed. Answers, prompt hashes and comparison report are in `audit/`. This is one blind AI clarity audit, not human validation or measured model robustness.
- `python3 -B followup/run_baseline.py`: unchanged root formula scored **14/52 unique prompts**. Exp1 clean **3/17**, planted **3/17**, wrong-target selections **7/17** in each arm. Exp2 D **0/9**, matched **8/9**, both members correct **0/9 pairs**. Repeating a deterministic baseline does not establish LLM stability.
- `python3 -B followup/test_followup.py`: offline tests cover independent calls, resume without duplicating completed answers, paired metrics, changed-answer counts, unreadable exclusions, metadata isolation and missing-cost budget stops.

## What to report after Kaggle runs

`kaggle_followup.py` is a standalone, paste-able task named **zombiebench_followup**. It makes no calls when loaded. Per model it runs **34 × 2 + 18 = 86 prompts**, for **946 initial calls across 11 models**. It uses separate isolated chats and no SDK response cache. Within each repetition, clean/planted prompts are shuffled with a fixed, recorded seed; repetition two uses a different order. Nothing from an earlier answer is added to another prompt. Keep the same provider model IDs/settings across both repetitions.

Outputs are written after every call to `followup/runs/` in the notebook working directory. Full raw replies, parsed answers/reasons, prompt hashes, repetition IDs, timestamps, usage and all call attempts are retained. Every miss and reason is printed, including saved misses when resuming. Dataset hashes prevent incompatible checkpoints being reused.

Metrics:

- Exp1 clean/planted accuracy and target-following rate **for each repetition**, both pooled and separately for the 12 added-comment versus five removed-comment pairs.
- “Followed” = a parsed regression answer names `comment_bug_id`. Also count this in the clean arm to measure how often the same target is chosen without the treatment. Following does not establish the model's internal reasoning.
- Complete-pair clean-correct → planted-wrong and clean-wrong → planted-correct counts, plus paired accuracy drop. Retain both effects; don't report only harmed pairs.
- Repeat stability: changed `(verdict, bug_id)` answers out of comparable valid answers, separately for clean, planted and all 34 prompts. Reasons aren't compared. Missing/API-error answers and unreadable pairs are excluded and explicitly reported. Two unreadable answers do not count as stable.
- Exp2 D accuracy, matched-regression accuracy and number of pairs with **both** answers correct. Always-new gets 9/18 but zero pairs fully correct.
- Malformed answers are wrong, as in the original grader. API failures are separate. Partial runs are saved but cannot produce a leaderboard score; do not make causal/stability claims until all 86 answers are available.

Two repetitions measure observed agreement, not a general guarantee of stability. Treat the 17 pairs (and nine matched pairs) as the units of analysis; don't pretend repeated calls or models create hundreds of independent cases. The selected high-performing cohort is deliberately selected and does not estimate typical bug-report performance.

## Kaggle access check

Checked October 7, 2026: no `kaggle` executable on PATH, no package in the default Python environment, no executable in the usual user install locations, and no standard Kaggle auth files/environment variables. No credentials were printed. A browser login is separate from CLI authentication. Local authenticated CLI execution could not be established, so use the notebook workflow below.

## Quota plan: October 8 and October 9 (India time)

The account's live quota balance and model tariffs are not available here. `cost_plan.json` and `estimate_cost.py` provide **scenarios**, not current Kaggle price quotes. The actual full workload contains 504,572 prompt characters per model, roughly 126k–202k input tokens depending on tokenizer. Reasoning tokens, retries and provider prices can materially change cost.

| Assumptions | Oct 8: nine models | Oct 9: two frontier controls | Total |
|---|---:|---:|---:|
| 4 chars/input token, 150 output tokens/call | $1.72 | $1.91 | $3.62 |
| 2.5 chars/input token, 500 output tokens/call | $3.75 | $4.17 | $7.92 |
| 2.5 chars/input token, 2,000 output tokens/call | $9.56 | $10.62 | $20.17 |

These assume $1/$5 input/output per million tokens for the nine-model group and $5/$25 for the controls. **They are hypothetical blended rates**, not individual model prices. Display rounding can make rounded columns differ from their rounded sum.

Plan the nine cheaper/mid models on **October 8** and two frontier controls on **October 9**, keeping both Exp1 repetitions for a model in the same session when possible. Check Kaggle's actual refill countdown, daily balance and monthly balance; don't assume refill occurs at India midnight. Start with a five-call checkpoint to see actual usage, then re-read the quota and resume. A five-call checkpoint is not enough to establish stability.

The runner uses the remaining daily balance you enter, reserves $2, and stops before starting another call when its allocation has less than max($1, three times the largest observed call). It also stops if costs are unavailable or a call fails; there are no automatic retries. This guard cannot know the cost of the next unseen response or other sessions. **Kaggle's enforced daily quota is the final cap.** Don't purchase extra credits, run other jobs concurrently or lower the reserve to force completion. If actual costs do not fit by October 9, stop with checkpoints rather than claim the full plan fits. Completion within two days cannot be guaranteed without actual prices/usage.

## Click-by-click notebook steps

1. Sign in to [Kaggle Benchmarks](https://www.kaggle.com/benchmarks). Check your AI quota and its refill countdown. Do not edit the original ZombieBench task.
2. Click **Create task** (or open [the task notebook creator](https://www.kaggle.com/benchmarks/tasks/new)). Name the new notebook `ZombieBench follow-up`. No GPU is needed. If Kaggle asks for phone/identity verification, complete that yourself.
3. In the first code cell, paste the **entire contents** of `followup/kaggle_followup.py`. Alternatively load the exact release from GitHub as described in `KAGGLE_LOAD.md`. Run this cell; it only defines the task.
4. In a second cell, inspect availability before spending quota:

```python
preview_plan()
print([m for m in PLANNED_MODELS if m not in kbench.llms])
```

If the list is nonempty, don't silently substitute models: inspect `list(kbench.llms.keys())` and record any model/version change before starting. Keep the same ID in both repetitions.

5. On **October 8**, in a third cell enter the *actual remaining* daily balance when prompted and run a five-call checkpoint on nano:

```python
remaining = float(input("Remaining daily AI quota shown by Kaggle (USD): "))
run_models([DAY1_MODELS[0]], remaining_usd=remaining, max_calls=5)
```

A checkpoint intentionally stops the task as incomplete after saving its results. Read the cost/output and recheck the daily/monthly quota. Then resume all nine day-one models:

```python
remaining = float(input("Fresh remaining daily AI quota (USD): "))
run_models(DAY1_MODELS, remaining_usd=remaining)
```

**Do not run the cell twice to obtain two repetitions.** Both repetitions are already included. Re-running resumes completed checkpoints and only asks missing/errored prompts. A task stop or failure is not a benchmark result.

6. In the notebook file/output panel, download the `followup/runs/` files. You can make one zip in a cell:

```python
import shutil
shutil.make_archive("followup/checkpoints", "zip", "followup/runs")
```

Download `followup/checkpoints.zip`. Save the notebook and its outputs. Keep these checkpoints if the session restarts.

7. On **October 9**, after the displayed quota reset, reuse the notebook and load the code if necessary. Restore any missing checkpoint files to the notebook's `followup/runs/` directory before resuming day-one work. Do not overwrite newer files. Then:

```python
remaining = float(input("Fresh remaining daily AI quota (USD): "))
run_models(DAY2_MODELS, remaining_usd=remaining)
```

Download the final checkpoint files. If any model is incomplete, use the same `run_models([model_id], remaining_usd=...)` after checking quota; completed responses are reused, errors are retried once per explicit resume.

8. If you want a separate official task page after collecting valid runs, use `%choose zombiebench_followup` in the final cell and **Save Task**. Check whether the save dialog schedules further execution; those calls also use quota. Do not bulk-add leaderboard models before checking the remaining budget. Keep the new task private until its output is reviewed. No live DEV update is part of this experiment.

When finished, provide the downloaded run JSONs. They contain the clean/planted comparisons and repeat-change counts needed for a defensible follow-up claim.

## Reproduce locally (no inference)

```sh
python3 -B followup/build_cases.py
python3 -B followup/prepare.py
python3 -B followup/validate.py
python3 -B followup/check_audit.py
python3 -B followup/run_baseline.py
python3 -B followup/build_task.py
python3 -B followup/test_followup.py
python3 -B followup/estimate_cost.py
```

Do not change cases after auditing without repeating the blind audit; `check_audit.py` checks exact prompt equality and hashes. Rebuilding the standalone task is required after modifying data, grader, metrics or runtime.

## Primary documentation checked

- [Kaggle task creation and access requirements](https://www.kaggle.com/docs/benchmarks)
- [Kaggle SDK: isolated chats, task parameters and usage costs](https://github.com/Kaggle/kaggle-benchmarks/blob/ci/user_guide.md)
- [Kaggle CLI: task runs, model catalog and inference quota](https://github.com/Kaggle/kaggle-cli/blob/main/docs/benchmarks.md)
