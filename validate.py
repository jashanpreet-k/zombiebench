"""Checks cases.json, and that kaggle_task.py carries the same cases.

- every case, history bug and report has all its fields
- expected answers fit the case type, and a regression's bug_id is in that case's history
- the four types have the same number of cases
- no duplicate case ids, and no duplicate bug ids within a history

Usage: python validate.py [cases.json]
"""

import ast
import json
import sys
from collections import Counter

TYPES = {"A": "regression", "B": "regression", "C": "new", "D": "new"}
CASE_FIELDS = ["id", "type", "history", "new_report", "expected", "why"]
BUG_FIELDS = ["id", "name", "cause", "language", "component", "symptoms", "fix_summary"]
REPORT_FIELDS = ["title", "description", "language", "component"]
HISTORY_SIZE = range(5, 9)


def is_text(value):
    return isinstance(value, str) and value.strip() != ""


def is_id(value):
    return isinstance(value, int) and not isinstance(value, bool)


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
    if case.get("type") not in TYPES:
        error(f"type must be one of {', '.join(TYPES)}, not {case.get('type')!r}")
    if not is_text(case.get("why")) or "\n" in case.get("why", ""):
        error("why must be one line of text")

    history = case.get("history")
    bug_ids = []
    if not isinstance(history, list) or len(history) not in HISTORY_SIZE:
        error(f"history must list {HISTORY_SIZE.start}–{HISTORY_SIZE.stop - 1} bugs")
        history = history if isinstance(history, list) else []
    for i, bug in enumerate(history):
        if not isinstance(bug, dict):
            error(f"history[{i}] is not an object")
            continue
        for field in BUG_FIELDS:
            value = bug.get(field)
            if field == "id" and not is_id(value):
                error(f"history[{i}] id must be a whole number")
            elif field != "id" and not is_text(value):
                error(f"history[{i}] (#{bug.get('id')}) missing '{field}'")
        bug_ids.append(bug.get("id"))
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
    if case.get("type") == "B":
        if report.get("component") is not None:
            error("a B report must not state its component (use null)")
    elif "component" in report and not is_text(report["component"]):
        error("new_report component must be text")

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

    for case_id, count in Counter(c.get("id") for c in cases if isinstance(c, dict)).items():
        if count > 1:
            errors.append(f"case id {case_id} appears {count} times")

    per_type = Counter(c.get("type") for c in cases if isinstance(c, dict))
    counts = [per_type.get(t, 0) for t in TYPES]
    if len(set(counts)) != 1:
        errors.append("types are unbalanced: " + ", ".join(f"{t}={per_type.get(t, 0)}" for t in TYPES))

    if embedded_cases() != cases:
        errors.append("kaggle_task.py's CASES differ from cases.json: run python embed_cases.py")

    if errors:
        print(f"{len(errors)} problem(s):")
        for message in errors:
            print(f"  - {message}")
        sys.exit(1)
    print(f"OK: {len(cases)} cases, " + ", ".join(f"{t}={per_type[t]}" for t in TYPES))


if __name__ == "__main__":
    main()
