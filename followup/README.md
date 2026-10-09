# ZombieBench controlled follow-up

Status: public task running through the authenticated Kaggle CLI. Saved responses and the current analysis are in `runs/`, `analysis.json`, and [RESULTS.md](RESULTS.md). The original dataset, task and results are unchanged.

## Design

Experiment 1 uses 17 source cases × five levels = 85 prompts. L0 has no comment; P adds a confident but irrelevant meeting note; L1 names the wrong historical bug tentatively; L2 makes the existing confident diagnosis; L3 claims the author personally fixed that wrong bug. All inserted comments occupy one terminal description line. They have 14–20 whitespace-delimited words and 90–134 characters; within each case the longest is at most 1.5 times the shortest. Only that line changes. L0 necessarily has no added text.

The 12 additions have three cases per type A/B/C/D, six easy and six hard. Approved exception: zb-07 and zb-27 each had one miss among the original 14 models; only zb-09 was a universally correct type-C case. The other ten added cases had no misses. Five original planted-diagnosis cases supply the remaining ladders. Their comment is removed from the source and normalized to the same terminal position. In zb-39, the original diagnosis-only comment now explicitly names its corresponding wrong ID #3539. Thus this is a controlled standardized follow-up, not an exact rerun of the original planted arms.

Experiment 2 has nine matched pairs: one distinct defect in an independent function and one true regression in the historically patched function. Histories and input contracts match within pairs. Domains and fault kinds vary, but the repeated scaffold and explicit source traces may make these easier than the original expert cases. They are synthetic and not calibrated for expert difficulty.

## Quality evidence

`python followup/validate.py` extends the root checks without editing them: valid IDs/gold/siblings, source selection counts, all 68 insertion diffs, label balance, comment positions/lengths, ID-free placebo, matched histories and equal tested cue-word counts. These finite cue tests cannot prove absence of every possible shortcut.

Three fresh agents independently answered disjoint shuffled batches without the answer key or conversation. Agreement: Exp1 85/85 and Exp2 18/18; no ambiguity or rewording. This is one audit per prompt, not three votes per prompt. Audit files include prompt hashes. The previous two-arm audit is preserved in `archive/two_arm/`.

The unchanged root baseline formula scored 23/103 unique prompts: 3/17 at each ladder level, 0/9 different-code and 8/9 same-code. Deterministic repeat agreement does not establish LLM stability.

```sh
python followup/build_cases.py
python followup/prepare.py
python followup/validate.py
python followup/check_audit.py
python followup/run_baseline.py
python followup/build_task.py
python followup/test_followup.py
python followup/estimate_cost.py
```

## Execution and quota

`kaggle_followup.py` is a standalone task named `zombiebench_followup`; it makes no calls merely on import. `n_runs=1` means 85 ladder prompts + 18 expansion prompts. `n_runs=2` adds only the 85 missing second-repeat ladder answers when saved outputs are present. Calls use separate chats, provider defaults and no SDK response cache.

`run_plan(remaining_usd)` runs the requested nine cheaper models first, then two frontier controls, then repeats only the cheaper models' Experiment 1. Total planned workload is 1,898 calls before retries. The notebook helper refuses unavailable IDs; the CLI scheduler records and skips them without substitution. Sonnet 4.5 was absent from the catalog. Raw replies, parsed answers, reasons, prompt hashes and every attempt's usage are saved in `followup/runs/` and included in a result ZIP. An API error is retried once. Unreadable model text is a scored miss, not an API retry.

Check both daily and monthly **inference dollars** before each batch. Installed CLI 2.2.4's `kaggle quota` reports accelerator hours; `python followup/inference_quota.py` reads the official SDK dollar-quota endpoint. Newer CLI releases offer `kaggle benchmarks quota`. Never print access tokens or proxy credentials.

The session guard subtracts $2 from the supplied remaining balance, accounts for reported nanodollar usage, and stops when less than max($0.10, three times the largest observed call) remains in that allocation. Missing cost metadata stops the plan. This is a conservative heuristic, not a provable pre-call cap: unusually large reasoning output can exceed the allowance. The CLI scheduler conservatively reserves a separate $2 allocation for every active job, plus the $2 account reserve. Check quota again before each launch. Resume only after the actual refill shown by Kaggle, preserving the saved files; do not infer a reset from the local calendar date.

`cost_plan.json` gives hypothetical tariff scenarios, not verified Kaggle prices: $5.93 / $13.02 / $33.44 total for short / buffered / long-reasoning assumptions. These were planning scenarios only. Recorded execution costs are computed from saved SDK result files; the authenticated quota endpoint determines what can actually be scheduled.

[Single-cell notebook fallback and exact files to return](KAGGLE_LOAD.md).

## Interpretation

Metrics report accuracy and wrong-target selection at every level, paired placebo/causal/hedge-to-authority changes, original-five recoveries, and same/different-code accuracy. At L0 and P, "followed" means selected the counterfactual target ID; there is no diagnosis comment to follow. L1→L3 changes confidence **and** claimed authority together, so it cannot isolate either mechanism. L0→L2 estimates the effect of the whole inserted comment. P controls for some extra-text distraction, not every semantic difference.

Stability compares verdict and ID, excluding missing/API-error/unreadable pairs; reasons are retained but not required to match. One repeated run measures repeat agreement only, and does not prove general reliability. Wilson 95% intervals describe these observations; pooled intervals do not account for dependence between shared cases and models. Headline analysis should use first runs to avoid overweighting the nine repeated models.

Original public task: https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench

Public follow-up task: https://www.kaggle.com/benchmarks/tasks/jashanpreetkaur24/zombiebench-followup

## CLI entry point

A definition-only file is not sufficient for task creation: Kaggle requires a captured task invocation. After the authenticated quota check, `make_cli_source.py --remaining-usd <verified balance>` builds `kaggle_cli_source.py` with that invocation. Pushing can execute its initial run, so quota must be checked **before** push. Use only the follow-up task slug.

```sh
kaggle quota --format json
python followup/inference_quota.py
kaggle benchmarks tasks models
# After checking balances, build the entry point using that actual balance:
# python followup/make_cli_source.py --remaining-usd <verified balance>
kaggle benchmarks tasks push zombiebench_followup -f followup/kaggle_cli_source.py --wait 60
kaggle benchmarks tasks status zombiebench_followup
# Select one verified model at a time, rechecking dollar quota between batches:
# kaggle benchmarks tasks run zombiebench_followup -m <verified model> --wait 60
kaggle benchmarks tasks download zombiebench_followup -o followup/runs
kaggle benchmarks tasks publish zombiebench_followup
```

For CLI second repetitions, download and review all first-run records, then build with `--n-runs 2`. The builder embeds those saved responses into the new backing notebook so they can be skipped. Without them it refuses to prepare a repeat for the selected model. Before any remote rerun, ensure the source's supplied balance is no greater than the freshly checked balance; stale balances must not authorize further spend.

CLI task executions additionally cap their individual allocation at $2. Check at least $4 remaining before scheduling one (the task allocation plus the account reserve). This is separate from the shared notebook batch budget. Persisted first-run seed records are restored inside the task so server serialization can resume them.


## Run identity correction

The initial CLI entry point explicitly bound nano. Consequently, the version-1 run scheduled under Gemini Flash-Lite actually invoked nano, as confirmed by its SDK result metadata and raw response file. `run_adjustments.json` preserves that independent second nano Experiment 1 run as repetition 2, with raw files unchanged; its additional Experiment 2 answers are excluded. This repeat ran early and in the same order as the first run. The corrected entry point uses `kbench.llm`, Kaggle's selected-model placeholder. Scheduled labels are checked against actual saved model identities before analysis. No Gemini claim is made from the mislabeled run.
