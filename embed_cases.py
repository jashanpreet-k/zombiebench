"""Copies cases.json into the CASES block of kaggle_task.py, then writes kaggle_paste.py.

kaggle_paste.py is kaggle_task.py without its last two lines, so loading it on Kaggle
defines everything and calls no model. Run this after every change to cases.json or
kaggle_task.py; validate.py fails until you do.

Usage: python embed_cases.py
"""

import json
import pprint

START = "# --- CASES: copied from cases.json by embed_cases.py; edit cases.json, then run it ---"
END = "# --- end CASES ---"
AUTO_RUN = '\n\nif __name__ == "__main__":\n    zombiebench.run(kbench.llm)\n'
PASTE_HEADER = """\
# Generated from kaggle_task.py by embed_cases.py: edit kaggle_task.py or cases.json, then run it.
# This file defines the cases, the task and its helpers, and calls no model when it runs.
# In a Kaggle Benchmarks notebook:
#
#   import urllib.request
#   exec(urllib.request.urlopen("https://raw.githubusercontent.com/jashanpreet-k/zombiebench/main/kaggle_paste.py").read().decode())
#   run_models(["google/gemini-3.8-flash"])

"""


def paste_file(task_source):
    """kaggle_paste.py's text: kaggle_task.py without the lines that run a model."""
    if not task_source.endswith(AUTO_RUN):
        raise ValueError("kaggle_task.py should end with its two auto-run lines")
    return PASTE_HEADER + task_source[: -len(AUTO_RUN)] + "\n"


def main():
    with open("cases.json", encoding="utf-8") as f:
        cases = json.load(f)
    with open("kaggle_task.py", encoding="utf-8") as f:
        source = f.read()

    before, rest = source.split(START + "\n", 1)
    _, after = rest.split(END, 1)
    block = "CASES = " + pprint.pformat(cases, width=110, sort_dicts=False) + "\n"
    source = before + START + "\n" + block + END + after
    with open("kaggle_task.py", "w", encoding="utf-8") as f:
        f.write(source)
    with open("kaggle_paste.py", "w", encoding="utf-8") as f:
        f.write(paste_file(source))
    print(f"Embedded {len(cases)} cases in kaggle_task.py and wrote kaggle_paste.py")


if __name__ == "__main__":
    main()
