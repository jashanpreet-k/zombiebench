"""Summarize the saved 48-case runs without calling models or changing files.

Reads the saved run summary and cases.json. The cases are used only to verify
that a wrong regression ID was present in that case's history.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS_FILE = ROOT / "results" / "2026-10-06-kaggle-48-cases.json"
CASES_FILE = ROOT / "cases.json"
TIERS = ("easy", "hard", "expert")
TYPES = ("A", "B", "C", "D")


def fraction(value):
    """Parse a saved score such as '12/12' into (passed, total)."""
    match = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", str(value))
    if not match:
        raise ValueError(f"Unexpected score format: {value!r}")
    return int(match.group(1)), int(match.group(2))


def regression_id(answer):
    """Return the numeric ID from 'regression #123', otherwise None."""
    match = re.fullmatch(r"regression\s+#(\d+)", str(answer).strip(), re.I)
    return int(match.group(1)) if match else None


def main():
    with RESULTS_FILE.open(encoding="utf-8") as file:
        results = json.load(file)
    with CASES_FILE.open(encoding="utf-8") as file:
        cases = json.load(file)

    case_histories = {
        case["id"]: {bug["id"] for bug in case["history"]}
        for case in cases
    }
    completed = [run for run in results["runs"] if run.get("status") == "completed"]
    if not completed:
        raise ValueError("No completed runs found in the saved results file.")
    models = [run["model"] for run in completed]
    if len(set(models)) != len(models):
        raise ValueError("Completed run entries contain duplicate model names.")

    attempts = sum(run["total"] for run in completed)
    correct = sum(run["passed"] for run in completed)
    api_errors = sum(run.get("errors", 0) for run in completed)
    scored_misses = []
    tier_passed = Counter()
    tier_attempts = Counter()
    type_attempts = Counter()

    for run in completed:
        run_misses = run.get("misses", [])
        if run["passed"] + len(run_misses) + run.get("errors", 0) != run["total"]:
            raise ValueError(f"Passes, misses, and errors do not add up for {run['model']}.")
        scored_misses.extend(run_misses)
        for tier in TIERS:
            tier_score = run["by_tier"][tier]
            passed, total = fraction(tier_score["total"])
            tier_passed[tier] += passed
            tier_attempts[tier] += total
            for case_type in TYPES:
                type_passed, type_total = fraction(tier_score[case_type])
                type_attempts[case_type] += type_total
                if type_passed > type_total:
                    raise ValueError(f"Invalid {tier}/{case_type} score for {run['model']}.")

    if sum(tier_passed.values()) != correct or sum(tier_attempts.values()) != attempts:
        raise ValueError("Tier totals do not match the saved overall totals.")
    if sum(type_attempts.values()) != attempts:
        raise ValueError("Case-type totals do not match the saved overall total.")

    misses_by_type = Counter()
    false_zombies = 0
    missed_zombies = 0
    wrong_historical_ids = 0
    unreadable = 0
    for miss in scored_misses:
        if miss["type"] not in TYPES:
            raise ValueError(f"Unexpected case type in saved miss: {miss['type']!r}")
        misses_by_type[miss["type"]] += 1
        expected = str(miss["expected"]).strip()
        answer = str(miss["answer"]).strip()
        expected_id = regression_id(expected)
        answer_id = regression_id(answer)

        if answer.lower() == "unreadable":
            unreadable += 1
        elif expected.lower() == "new" and answer_id is not None:
            false_zombies += 1
        elif expected_id is not None and answer.lower() == "new":
            missed_zombies += 1
        elif expected_id is not None and answer_id is not None and answer_id != expected_id:
            history = case_histories.get(miss["case"])
            if history is None:
                raise ValueError(f"No case history found for {miss['case']}.")
            if answer_id not in history:
                raise ValueError(
                    f"Wrong regression ID {answer_id} for {miss['case']} is not in its history; "
                    "cannot count it as a wrong historical ID."
                )
            wrong_historical_ids += 1
        else:
            raise ValueError(f"Cannot classify saved miss: {miss!r}")

    if false_zombies + missed_zombies + wrong_historical_ids + unreadable != len(scored_misses):
        raise ValueError("Classified miss counts do not add up to saved misses.")

    expert_d_attempts = sum(
        fraction(run["by_tier"]["expert"]["D"])[1] for run in completed
    )
    expert_d_misses = sum(
        1 for miss in scored_misses
        if miss["tier"] == "expert" and miss["type"] == "D"
    )

    print(f"Completed model runs: {len(completed)}")
    print(f"Model-case attempts: {attempts}")
    print(f"Overall correct: {correct}/{attempts} = {correct / attempts:.1%}")
    print("\nTier results:")
    for tier in TIERS:
        passed = tier_passed[tier]
        total = tier_attempts[tier]
        print(f"  {tier.title():<7} {passed}/{total} = {passed / total:.1%}")

    print("\nMisses by case type:")
    for case_type in TYPES:
        print(f"  {case_type}: {misses_by_type[case_type]}/{type_attempts[case_type]} attempts")

    print("\nMiss categories:")
    print(f"  False Zombies: {false_zombies}")
    print(f"  Missed Zombies: {missed_zombies}")
    if missed_zombies:
        print(f"  False-Zombie / Missed-Zombie ratio: {false_zombies / missed_zombies:.2f}x")
    print(f"  Wrong historical bug IDs: {wrong_historical_ids}")
    print(f"  Unreadable responses: {unreadable}")
    print(f"  API errors in completed runs: {api_errors}")
    print(f"  Expert D misses: {expert_d_misses}/{expert_d_attempts} attempts")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"Could not summarize saved results: {error}", file=sys.stderr)
        raise SystemExit(1)
