"""Original ZombieBench prompt and grading rules, frozen for this follow-up."""
import json
import re
VERDICTS = ("regression", "new")

def build_prompt(case):
    lines = [
        "You are triaging bug reports for a software team.",
        "",
        "Below are bugs the team has already fixed, then one new bug report. Decide whether the new",
        "report is a REGRESSION (one of the fixed bugs coming back: the same defect with the same",
        "underlying cause) or a NEW bug that is not any of the fixed ones.",
        "",
        "FIXED BUGS",
    ]
    for bug in case["history"]:
        lines += [
            "",
            f"#{bug['id']} {bug['name']}",
            f"- Cause: {bug['cause']}",
            f"- Language: {bug['language']}",
            f"- Component: {bug['component']}",
            f"- Symptoms: {bug['symptoms']}",
            f"- Fix: {bug['fix_summary']}",
        ]
    report = case["new_report"]
    lines += [
        "",
        "NEW BUG REPORT",
        "",
        f"Title: {report['title']}",
        f"Language: {report['language'] or 'not given'}",
        f"Component: {report['component'] or 'not given'}",
        f"Description: {report['description']}",
        "",
        "Reply with JSON only, no other text, in exactly this shape:",
        '{"verdict": "regression" or "new", "bug_id": the fixed bug\'s number if it is a regression, '
        'otherwise null, "reason": "one sentence"}',
    ]
    return "\n".join(lines)

def first_json_object(text):
    """The first {...} in the text that has a "verdict" key, or None."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            data, _ = decoder.raw_decode(text, match.start())
        except ValueError:
            continue
        if isinstance(data, dict) and "verdict" in data:
            return data
    return None

def read_bug_id(value):
    """(True, id or None) for a usable bug_id, (False, None) for anything else."""
    if value is None:
        return True, None
    if isinstance(value, bool):
        return False, None
    if isinstance(value, int):
        return True, value
    if isinstance(value, float) and value.is_integer():
        return True, int(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("", "null", "none"):
            return True, None
        match = re.fullmatch(r"#?\s*(\d+)", text)
        if match:
            return True, int(match.group(1))
    return False, None

def parse_answer(reply):
    """(verdict, bug_id, reason) from the model's reply, or None if it isn't the JSON we asked for."""
    data = first_json_object(reply if isinstance(reply, str) else "")
    if data is None:
        return None
    verdict = data.get("verdict")
    if not isinstance(verdict, str) or verdict.strip().lower() not in VERDICTS:
        return None
    ok, bug_id = read_bug_id(data.get("bug_id"))
    if not ok:
        return None
    reason = data.get("reason")
    return verdict.strip().lower(), bug_id, reason if isinstance(reason, str) else ""

def judge(case, reply):
    """One case's result from the model's reply: status "pass" or "fail", and any problem with the answer."""
    expected = case["expected"]
    result = {"id": case["id"], "tier": case["tier"], "type": case["type"], "status": "fail",
              "problem": None, "verdict": None, "bug_id": None, "reason": ""}
    answer = parse_answer(reply)
    if answer is None:
        result.update(problem="unreadable", reason=repr(str(reply)[:200]))
        return result
    verdict, bug_id, reason = answer
    result.update(verdict=verdict, bug_id=bug_id, reason=reason)
    if verdict == "regression" and bug_id is None:
        result["problem"] = "missing id"
    elif verdict == "regression" and bug_id not in {bug["id"] for bug in case["history"]}:
        result["problem"] = "hallucinated id"
    if (verdict, bug_id) == (expected["verdict"], expected["bug_id"]):
        result["status"] = "pass"
    return result

def describe(verdict, bug_id):
    if verdict == "regression":
        return "regression (no id)" if bug_id is None else f"regression #{bug_id}"
    return verdict
