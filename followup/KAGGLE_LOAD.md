# Kaggle fallback: one cell

Use this only if the CLI login/push/run cannot be restored. No follow-up task is public yet.

1. Open Kaggle → Benchmarks → create a new task/notebook; name it `zombiebench_followup`. Do not edit the original ZombieBench notebook.
2. Enable the notebook's Internet access and the Kaggle Benchmarks environment. Read the daily and monthly AI-inference dollar balances; use the smaller remaining balance below (maximum $10). Keep other inference notebooks idle.
3. Paste and run this single cell. It runs the requested model priorities and resumes saved answers. Do not replace an unavailable model silently.

```python
import hashlib, urllib.request
source = urllib.request.urlopen("https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/followup/kaggle_followup.py").read()
assert hashlib.sha256(source).hexdigest() == "ede411ee37b9ad8cc8946722ad3772dbc4a8017af80ca37d91b037a1eafd57ad", "Source changed; review before running."
exec(compile(source, "zombiebench_followup.py", "exec"))
remaining = float(input("Current remaining AI inference dollars (min of daily/monthly, up to 10): "))
run_plan(remaining_usd=remaining)
```

4. If it stops at the quota guard, download `zombiebench-followup-results.zip` immediately. After the shown refill, restore its `runs/` directory under `/kaggle/working/followup/`, recheck the balances, and rerun the same cell. Existing completed answers are skipped. A fresh kernel without restored files will repeat paid calls.
5. Save the notebook version, make the follow-up task public using Share, and copy its actual task URL. The CLI may normalize the URL slug to `zombiebench-followup`; use the URL Kaggle returns.
6. Return **the result ZIP**, **the actual public follow-up task URL**, **the final COMPLETE/STOP/error line**, and **daily/monthly quota balances**. Do not paste credentials or a screenshot containing credentials. If the catalog check stops the run, paste only the unavailable model IDs.

The ZIP contains every saved raw model answer needed for causal and stability analysis. Summary text alone is insufficient. No live article update should be made until those saved results are analyzed.
