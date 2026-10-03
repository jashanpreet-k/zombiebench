"""The Bug Graveyard Zombie Detector, run on ZombieBench's cases.

A Python port of bug-graveyard/sanity/lib/detector.ts:

    match score = 25 × same cause
                + 15 × same language
                + 25 × same component
                + 35 × min(shared keywords, 4) / 4      (rounded to a whole number)

The highest-scoring history bug wins (a tie goes to the name that sorts first).
If its score is at least 60 the verdict is "regression" with that bug's id,
otherwise "new".

The formula only sees what the new report says, never the expected answer:
- A report has no cause field, so "same cause" counts only when the report's
  title or description names the history bug's cause (e.g. "timezone").
- "Same component" needs a component on the report; B-type reports have none.
- Keywords come from a history bug's name + symptoms and the report's
  title + description, with the same stop words, aliases and stemming as the
  original detector.

Usage: python baseline.py [cases.json] [--verbose]
"""

import json
import math
import re
import sys

MATCH_THRESHOLD = 60
WEIGHTS = {"cause": 25, "language": 15, "component": 25, "keywords": 35}
FULL_KEYWORDS = 4

STOP_WORDS = set(
    """a an and are as at be been but by can could did do does for from had has have how if in into is it its
    just like me my no not of on once or our out over so some than that the their them then there these they
    this those through to too up us very was we were what when where which while who why will with would you
    your after again all also any back bug bugs came come every fixed fix get got one only still two new old
    ever never nothing something someone""".split()
)
# Short forms people write for the same thing
ALIASES = {"dst": "daylight", "tz": "timezone"}


def stem(word):
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 4 and word.endswith("es"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def keywords_of(text):
    """A text's keywords: stem -> the first word it came from."""
    words = {}
    for raw in re.findall(r"[^\W_]+", text.lower()):
        word = ALIASES.get(raw, raw)
        if len(word) < 3 or word in STOP_WORDS or word.isdigit():
            continue
        words.setdefault(stem(word), word)
    return words


def normalize(text):
    return " ".join(re.findall(r"[^\W_]+", (text or "").lower()))


def same_text(a, b):
    return bool(a and b and a.strip().lower() == b.strip().lower())


def names_cause(report_text, cause):
    """True when the report's own words name the cause, e.g. 'Off-by-one' in '... off by one ...'."""
    phrase = normalize(cause)
    return bool(phrase) and f" {phrase} " in f" {normalize(report_text)} "


def score_match(report, bug):
    report_text = f"{report['title']} {report['description']}"
    mine = keywords_of(report_text)
    theirs = keywords_of(f"{bug['name']} {bug['symptoms']}")
    shared = [word for key, word in mine.items() if key in theirs]

    points = {
        "cause": WEIGHTS["cause"] if names_cause(report_text, bug["cause"]) else 0,
        "language": WEIGHTS["language"] if same_text(report.get("language"), bug["language"]) else 0,
        "component": WEIGHTS["component"] if same_text(report.get("component"), bug["component"]) else 0,
        # floor(x + 0.5) rounds halves up, like JavaScript's Math.round
        "keywords": math.floor(WEIGHTS["keywords"] * min(len(shared), FULL_KEYWORDS) / FULL_KEYWORDS + 0.5),
    }
    return {"bug": bug, "score": sum(points.values()), "points": points, "shared": shared}


def predict(case):
    matches = [score_match(case["new_report"], bug) for bug in case["history"]]
    matches.sort(key=lambda m: (-m["score"], m["bug"]["name"].lower()))
    best = matches[0]
    if best["score"] >= MATCH_THRESHOLD:
        return {"verdict": "regression", "bug_id": best["bug"]["id"]}, best
    return {"verdict": "new", "bug_id": None}, best


def is_correct(prediction, expected):
    return prediction["verdict"] == expected["verdict"] and prediction["bug_id"] == expected["bug_id"]


def describe(answer):
    return f"regression #{answer['bug_id']}" if answer["verdict"] == "regression" else "new"


def print_summary(results):
    """results: (tier, type, passed) per case. One row per tier, then all tiers together."""
    tiers = [t for t in ("easy", "hard") if any(r[0] == t for r in results)]
    print(f"{'':<6}" + "".join(f"{t:>7}" for t in "ABCD") + f"{'all':>14}")
    for tier in tiers + ["all"]:
        rows = [r for r in results if tier in ("all", r[0])]
        cells = []
        for case_type in "ABCD":
            oks = [ok for _, t, ok in rows if t == case_type]
            cells.append(f"{sum(oks)}/{len(oks)}" if oks else "-")
        passed = sum(ok for _, _, ok in rows)
        print(f"{tier:<6}" + "".join(f"{c:>7}" for c in cells)
              + f"{passed:>6}/{len(rows)} = {passed / len(rows):.0%}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--verbose" in sys.argv
    with open(args[0] if args else "cases.json", encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    print(f"{'case':<7}{'tier':<6}{'type':<6}{'expected':<18}{'baseline':<18}{'best match':<12}{'score':>5}  ok")
    for case in cases:
        prediction, best = predict(case)
        ok = is_correct(prediction, case["expected"])
        results.append((case["tier"], case["type"], ok))
        print(
            f"{case['id']:<7}{case['tier']:<6}{case['type']:<6}{describe(case['expected']):<18}{describe(prediction):<18}"
            f"#{best['bug']['id']:<11}{best['score']:>5}  {'✓' if ok else '✗'}"
        )
        if verbose:
            p = best["points"]
            print(
                f"{'':19}cause {p['cause']}, language {p['language']}, component {p['component']}, "
                f"keywords {p['keywords']} ({', '.join(best['shared']) or 'none'})"
            )

    print()
    print_summary(results)


if __name__ == "__main__":
    main()
