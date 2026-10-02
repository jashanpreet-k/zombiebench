"""Copies cases.json into the CASES block of kaggle_task.py, so Kaggle needs only one paste.

Run it after every change to cases.json; validate.py fails until you do.

Usage: python embed_cases.py
"""

import json
import pprint

START = "# --- CASES: copied from cases.json by embed_cases.py; edit cases.json, then run it ---"
END = "# --- end CASES ---"


def main():
    with open("cases.json", encoding="utf-8") as f:
        cases = json.load(f)
    with open("kaggle_task.py", encoding="utf-8") as f:
        source = f.read()

    before, rest = source.split(START + "\n", 1)
    _, after = rest.split(END, 1)
    block = "CASES = " + pprint.pformat(cases, width=110, sort_dicts=False) + "\n"
    with open("kaggle_task.py", "w", encoding="utf-8") as f:
        f.write(before + START + "\n" + block + END + after)
    print(f"Embedded {len(cases)} cases in kaggle_task.py")


if __name__ == "__main__":
    main()
