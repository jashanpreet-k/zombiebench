"""Checks cases.json, and that kaggle_task.py carries the same cases.

- every case, history bug and report has all its fields
- history size fits the tier (easy 5–8 bugs, hard 12–15)
- expected answers fit the case type, and a regression's bug_id is in that case's history
- siblings are exactly the other history bugs that share the answer's component or cause
  (2–3 for hard regressions); a C case names its decoy bug
- key_clue is quoted exactly from the report
- the four types have the same number of cases in each tier
- no duplicate case ids, and no duplicate bug ids within a history
- kaggle_task.py and kaggle_paste.py carry the same cases and code
- cue words ("again", "used to", ...) and a missing component don't give the answer away
- answers aren't bunched in one part of the history

Usage: python validate.py [cases.json]
"""

import ast
import json
import re
import sys
from collections import Counter

from embed_cases import paste_file

TYPES = {"A": "regression", "B": "regression", "C": "new", "D": "new"}
TIERS = {"easy": range(5, 9), "hard": range(12, 16)}
HARD_SIBLINGS = range(2, 4)
CASE_FIELDS = ["id", "tier", "type", "history", "new_report", "expected", "siblings", "decoy_bug_id", "key_clue", "why"]
BUG_FIELDS = ["id", "name", "cause", "language", "component", "symptoms", "fix_summary"]
REPORT_FIELDS = ["title", "description", "language", "component"]
# Phrases that sound like "it came back". They must not predict the answer on their own.
CUE_WORDS = {
    "again": r"\bagain\b",
    "still": r"\bstill\b",
    "came back": r"\b(?:came|come|comes|coming|is|are|was|were) back\b",
    "used to": r"\bused to\b",
    "stopped working": r"\bstopped working\b",
    "no longer / anymore": r"\bno longer\b|\banymore\b",
    "reappeared": r"\breappear\w*",
    "regressed": r"\bregress\w*",
}
THIRDS = ["first", "middle", "last"]


def is_text(value):
    return isinstance(value, str) and value.strip() != ""


def is_id(value):
    return isinstance(value, int) and not isinstance(value, bool)


def same_text(a, b):
    return is_text(a) and is_text(b) and a.strip().lower() == b.strip().lower()


def siblings_of(history, answer):
    """The other history bugs with the same component or the same cause as the answer."""
    return sorted(bug["id"] for bug in history if bug is not answer
                  and (same_text(bug.get("component"), answer.get("component"))
                       or same_text(bug.get("cause"), answer.get("cause"))))


def check_case(case, errors):
    name = case.get("id", "?") if isinstance(case, dict) else "?"

    def error(message):
        errors.append(f"{name}: {message}")

    if not isinstance(case, dict):
        return error("is not an object")
    for field in CASE_FIELDS:
        if field not in case:
            error(f"missing '{field}'")
    if not is_text(case.get("id")):
        error("id must be text")
    if case.get("tier") not in TIERS:
        error(f"tier must be one of {', '.join(TIERS)}, not {case.get('tier')!r}")
    if case.get("type") not in TYPES:
        error(f"type must be one of {', '.join(TYPES)}, not {case.get('type')!r}")
    if not is_text(case.get("why")) or "\n" in case.get("why", ""):
        error("why must be one line of text")

    history = case.get("history")
    size = TIERS.get(case.get("tier"), range(0))
    if not isinstance(history, list) or len(history) not in size:
        error(f"a {case.get('tier')} history must list {size.start}–{size.stop - 1} bugs")
    history = [bug for bug in history if isinstance(bug, dict)] if isinstance(history, list) else []
    for i, bug in enumerate(history):
        for field in BUG_FIELDS:
            value = bug.get(field)
            if field == "id" and not is_id(value):
                error(f"history[{i}] id must be a whole number")
            elif field != "id" and not is_text(value):
                error(f"history[{i}] (#{bug.get('id')}) missing '{field}'")
    bug_ids = [bug.get("id") for bug in history]
    for bug_id, count in Counter(bug_ids).items():
        if count > 1:
            error(f"bug id {bug_id} appears {count} times in the history")

    report = case.get("new_report")
    if not isinstance(report, dict):
        error("new_report must be an object")
        report = {}
    for field in REPORT_FIELDS:
        if field not in report:
            error(f"new_report missing '{field}'")
    for field in ("title", "description", "language"):
        if field in report and not is_text(report[field]):
            error(f"new_report {field} must be text")
    if report.get("component") is not None and not is_text(report["component"]):
        error("new_report component must be text, or null when the report doesn't say")

    clue = case.get("key_clue")
    if not is_text(clue):
        error("key_clue must be text")
    elif clue not in str(report.get("title")) and clue not in str(report.get("description")):
        error("key_clue must be quoted exactly from the report's title or description")

    decoy = case.get("decoy_bug_id")
    if case.get("type") == "C":
        if decoy not in bug_ids:
            error(f"decoy_bug_id {decoy!r} is not in the history")
    elif decoy is not None:
        error("only C cases have a decoy_bug_id")

    expected = case.get("expected")
    if not isinstance(expected, dict):
        return error("expected must be an object")
    verdict, bug_id = expected.get("verdict"), expected.get("bug_id")
    if case.get("type") in TYPES and verdict != TYPES[case["type"]]:
        error(f"type {case['type']} must expect '{TYPES[case['type']]}', not {verdict!r}")
    if verdict == "regression" and bug_id not in bug_ids:
        error(f"expected bug_id {bug_id!r} is not in the history")
    if verdict == "new" and bug_id is not None:
        error("a 'new' verdict must have bug_id null")

    siblings = case.get("siblings")
    answer = next((bug for bug in history if bug.get("id") == bug_id), None) if verdict == "regression" else None
    if not isinstance(siblings, list) or not all(is_id(s) for s in siblings):
        error("siblings must be a list of bug ids")
    elif answer is not None:
        should_be = siblings_of(history, answer)
        if sorted(siblings) != should_be:
            error(f"siblings should be {should_be} (bugs sharing #{bug_id}'s component or cause), not {sorted(siblings)}")
        if case.get("tier") == "hard" and len(should_be) not in HARD_SIBLINGS:
            error(f"a hard regression needs {HARD_SIBLINGS.start}–{HARD_SIBLINGS.stop - 1} siblings, has {len(should_be)}")
    elif siblings:
        error("only regressions have siblings")


def check_leaks(cases, errors):
    """Prints, per tier, how many reports of each type carry a cue word or a null component.

    A signal that shows up only in regressions (A, B) or only in new bugs (C, D)
    predicts the answer without reading the bug, so it's an error.
    """
    def cues_in(report):
        text = f"{report.get('title', '')} {report.get('description', '')}"
        return {label for label, pattern in CUE_WORDS.items() if re.search(pattern, text, re.I)}

    rows = {label: lambda report, label=label: label in cues_in(report) for label in CUE_WORDS}
    rows["any cue word"] = lambda report: bool(cues_in(report))
    rows["component: null"] = lambda report: report.get("component") is None

    tiers = [t for t in TIERS if any(c.get("tier") == t for c in cases)]
    reports = {tier: [(c["type"], c["new_report"]) for c in cases if c.get("tier") == tier
                      and c.get("type") in TYPES and isinstance(c.get("new_report"), dict)] for tier in tiers}
    print(f"{'':<22}" + "".join(f"{tier:<18}" for tier in tiers))
    print(f"{'Reports with':<22}" + "".join("".join(f"{t:<4}" for t in TYPES) + "  " for _ in tiers))
    for label, has in rows.items():
        line = f"{label:<22}"
        for tier in tiers:
            counts = Counter(case_type for case_type, report in reports[tier] if has(report))
            line += "".join(f"{counts.get(t, 0):<4}" for t in TYPES) + "  "
            in_regressions = any(counts[t] for t in TYPES if TYPES[t] == "regression")
            in_new_bugs = any(counts[t] for t in TYPES if TYPES[t] == "new")
            if in_regressions != in_new_bugs:
                where = "regressions (A, B)" if in_regressions else "new bugs (C, D)"
                errors.append(f"{tier}: '{label}' only appears in {where}, so it gives the answer away")
        print(line)
    print(f"{'reports':<22}" + "".join(
        "".join(f"{sum(1 for ct, _ in reports[tier] if ct == t):<4}" for t in TYPES) + "  " for tier in tiers))
    print()


def check_positions(cases, errors):
    """Prints where each regression's answer sits in its history; no third may hold over half."""
    counts = {}
    for case in cases:
        history, expected = case.get("history"), case.get("expected") or {}
        ids = [bug.get("id") for bug in history if isinstance(bug, dict)] if isinstance(history, list) else []
        if expected.get("verdict") != "regression" or expected.get("bug_id") not in ids:
            continue
        third = THIRDS[ids.index(expected["bug_id"]) * 3 // len(ids)]
        counts.setdefault(case.get("tier"), Counter())[third] += 1
    total = sum(counts.values(), Counter())
    print(f"{'Answer position':<22}" + "".join(f"{third:<8}" for third in THIRDS))
    for tier, tier_counts in [*counts.items(), ("all", total)]:
        print(f"{tier:<22}" + "".join(f"{tier_counts.get(third, 0):<8}" for third in THIRDS))
    print()
    if total and max(total.values()) * 2 > sum(total.values()):
        errors.append("over half of the answers sit in the same third of their history")


def embedded_cases():
    """The CASES list in kaggle_task.py, read without importing kaggle_benchmarks."""
    with open("kaggle_task.py", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "CASES" for t in node.targets):
            return ast.literal_eval(node.value)
    return None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "cases.json"
    with open(path, encoding="utf-8") as f:
        cases = json.load(f)

    errors = []
    if not isinstance(cases, list) or not cases:
        errors.append("cases.json must be a non-empty list")
        cases = []
    for case in cases:
        check_case(case, errors)
    cases = [c for c in cases if isinstance(c, dict)]

    for case_id, count in Counter(c.get("id") for c in cases).items():
        if count > 1:
            errors.append(f"case id {case_id} appears {count} times")

    for tier in TIERS:
        per_type = Counter(c.get("type") for c in cases if c.get("tier") == tier)
        if per_type and len({per_type.get(t, 0) for t in TYPES}) != 1:
            errors.append(f"{tier} types are unbalanced: " + ", ".join(f"{t}={per_type.get(t, 0)}" for t in TYPES))

    check_leaks(cases, errors)
    check_positions(cases, errors)

    if embedded_cases() != cases:
        errors.append("kaggle_task.py's CASES differ from cases.json: run python embed_cases.py")
    try:
        with open("kaggle_task.py", encoding="utf-8") as f, open("kaggle_paste.py", encoding="utf-8") as g:
            in_sync = g.read() == paste_file(f.read())
    except (OSError, ValueError):
        in_sync = False
    if not in_sync:
        errors.append("kaggle_paste.py is out of date: run python embed_cases.py")

    if errors:
        print(f"{len(errors)} problem(s):")
        for message in errors:
            print(f"  - {message}")
        sys.exit(1)
    per_tier = Counter(c["tier"] for c in cases)
    per_type = Counter(c["type"] for c in cases)
    print(f"OK: {len(cases)} cases (" + ", ".join(f"{t} {per_tier[t]}" for t in TIERS) + "), "
          + ", ".join(f"{t}={per_type[t]}" for t in TYPES))


if __name__ == "__main__":
    main()
