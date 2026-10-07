# Verified single-cell loader

Paste this into a new Kaggle Benchmarks task notebook. It loads definitions only.
The SHA-256 pins the exact reviewed file even if the main branch later changes.

```python
import hashlib
import urllib.request
url = "https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/followup/kaggle_followup.py"
source = urllib.request.urlopen(url).read()
assert hashlib.sha256(source).hexdigest() == "6c4d007e06b985fb0f55b3843a178ff56fb5aacc8ef2602c0b6acbe5bcbc3dc7", "Source changed; review it before running."
exec(compile(source, "zombiebench_followup.py", "exec"))
preview_plan()
```

Continue with README.md's quota check and day-one/day-two cells. Never reuse the original ZombieBench notebook for this follow-up.
