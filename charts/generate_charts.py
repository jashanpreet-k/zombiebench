#!/usr/bin/env python3
"""Generate the ZombieBench post charts and cover from saved run results.

Requires matplotlib. The script validates the expected run and miss counts
before writing any images.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze_results import main as analyze_results
RESULTS = ROOT / "results" / "2026-10-06-kaggle-48-cases.json"
CASES = ROOT / "cases.json"
OUT = ROOT / "charts"
EXPECTED_MISS_TYPES = {
    "False Zombies": 55,
    "Missed Zombies": 17,
    "Wrong old bug IDs": 7,
    "Unreadable": 1,
}
EXPECTED_HARDEST = [
    ("zb-37", 7),
    ("zb-48", 7),
    ("zb-25", 6),
    ("zb-46", 6),
    ("zb-26", 5),
    ("zb-41", 5),
    ("zb-47", 5),
    ("zb-32", 4),
]
MODEL_LABELS = {
    "openai/gpt-6.1-sol": "gpt-6.1-sol",
    "anthropic/claude-opus-5-5@default": "claude-opus-5-5",
    "google/gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
    "openai/gpt-5.5-2026-04-23": "gpt-5.5",
    "google/gemini-3.8-flash": "gemini-3.8-flash",
    "google/gemma-4-31b": "gemma-4-31b",
    "google/gemini-2.5-flash": "gemini-2.5-flash",
    "anthropic/claude-sonnet-4-5@20250929": "claude-sonnet-4-5",
    "openai/gpt-5.4-mini-2026-03-17": "gpt-5.4-mini",
    "google/gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite-preview",
    "openai/gpt-oss-20b": "gpt-oss-20b",
    "anthropic/claude-haiku-4-5@20251001": "claude-haiku-4-5",
    "qwen/qwen3-235b-a22b-instruct-2507": "qwen3-235b-a22b-instruct",
    "openai/gpt-5.4-nano-2026-03-17": "gpt-5.4-nano",
}


def regression_id(answer):
    match = re.fullmatch(r"regression\s+#(\d+)", str(answer).strip(), re.I)
    return int(match.group(1)) if match else None


def classify_miss(miss, case_histories):
    expected = str(miss["expected"]).strip()
    answer = str(miss["answer"]).strip()
    expected_id = regression_id(expected)
    answer_id = regression_id(answer)

    if answer.lower() == "unreadable":
        return "Unreadable"
    if expected.lower() == "new" and answer_id is not None:
        return "False Zombies"
    if expected_id is not None and answer.lower() == "new":
        return "Missed Zombies"
    if expected_id is not None and answer_id is not None and answer_id != expected_id:
        if answer_id not in case_histories[miss["case"]]:
            raise ValueError(f"Wrong ID {answer_id} is absent from {miss['case']} history.")
        return "Wrong old bug IDs"
    raise ValueError(f"Cannot classify saved miss: {miss!r}")


def load_and_validate():
    summary = analyze_results()
    if (summary["models"], summary["attempts"], summary["correct"], summary["misses"]) != (14, 672, 592, 80):
        raise ValueError("analyze_results.py totals differ from the approved counts; stopping.")
    if summary["miss_types"] != EXPECTED_MISS_TYPES or summary["hardest"] != EXPECTED_HARDEST:
        raise ValueError("analyze_results.py miss counts differ from the approved counts; stopping.")
    with RESULTS.open(encoding="utf-8") as file:
        results = json.load(file)
    with CASES.open(encoding="utf-8") as file:
        cases = json.load(file)

    case_info = {case["id"]: (case["tier"], case["type"]) for case in cases}
    case_histories = {
        case["id"]: {int(bug["id"]) for bug in case["history"]}
        for case in cases
    }
    runs = [run for run in results["runs"] if run.get("status") == "completed"]
    runs.sort(key=lambda run: list(MODEL_LABELS).index(run["model"]))
    if len(runs) != 14 or len({run["model"] for run in runs}) != 14:
        raise ValueError(f"Expected 14 distinct completed model runs, found {len(runs)}.")
    if set(MODEL_LABELS) != {run["model"] for run in runs}:
        raise ValueError("Completed model IDs differ from the chart's verified 14-model set.")
    if any(run["total"] != 48 for run in runs):
        raise ValueError("Expected every completed model run to contain 48 cases.")

    total_attempts = sum(run["total"] for run in runs)
    total_correct = sum(run["passed"] for run in runs)
    all_misses = [miss for run in runs for miss in run.get("misses", [])]
    miss_types = Counter(classify_miss(miss, case_histories) for miss in all_misses)
    if total_attempts != 672 or total_correct != 592 or len(all_misses) != 80:
        raise ValueError(
            f"Expected 672 attempts, 592 correct, 80 misses; got "
            f"{total_attempts}, {total_correct}, {len(all_misses)}."
        )
    if dict(miss_types) != EXPECTED_MISS_TYPES:
        raise ValueError(f"Miss taxonomy differs: expected {EXPECTED_MISS_TYPES}, got {dict(miss_types)}")

    missed_cases = Counter(miss["case"] for miss in all_misses)
    hardest = sorted(missed_cases.items(), key=lambda item: (-item[1], item[0]))[:8]
    if hardest != EXPECTED_HARDEST:
        raise ValueError(f"Hardest-case counts differ: expected {EXPECTED_HARDEST}, got {hardest}")
    if any(count > 14 for count in missed_cases.values()):
        raise ValueError("A case has more than 14 misses, which is inconsistent with one run per model.")

    case_denominators = {}
    for tier in ("easy", "hard", "expert"):
        for case_type in "ABCD":
            tier_type_cases = [
                case for case in cases
                if case["tier"] == tier and case["type"] == case_type
            ]
            case_denominators[(tier, case_type)] = len(tier_type_cases)
    if {tier: case_denominators[(tier, "A")] for tier in ("easy", "hard", "expert")} != {
        "easy": 3, "hard": 6, "expert": 3
    }:
        raise ValueError("Unexpected case denominators by tier.")
    if any(case_denominators[(tier, t)] != case_denominators[(tier, "A")] for tier in ("easy", "hard", "expert") for t in "BCD"):
        raise ValueError("Case counts differ across types within a tier.")
    return runs, cases, case_info, all_misses, miss_types, missed_cases, case_denominators, total_attempts, total_correct


def make_heatmap(runs, case_denominators):
    tiers = ("easy", "hard", "expert")
    types = "ABCD"
    columns = [(tier, t) for tier in tiers for t in types]
    model_ids = [run["model"] for run in runs]
    # Miss entries live in their enclosing run; attach the model ID explicitly.
    misses = Counter(
        (run["model"], miss["tier"], miss["type"])
        for run in runs for miss in run.get("misses", [])
    )
    values = np.zeros((len(model_ids), len(columns)), dtype=float)
    annotations = [[""] * len(columns) for _ in model_ids]
    for row, model in enumerate(model_ids):
        for col, (tier, case_type) in enumerate(columns):
            denominator = case_denominators[(tier, case_type)]
            count = misses[(model, tier, case_type)]
            values[row, col] = count / denominator
            if count:
                annotations[row][col] = f"{count}/{denominator}"

    fig, ax = plt.subplots(figsize=(13.5, 7.5), facecolor="white")
    ax.set_facecolor("white")
    image = ax.imshow(values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(columns)), [f"{tier.title()}\n{t}" for tier, t in columns], fontsize=9)
    ax.set_yticks(range(len(model_ids)), [MODEL_LABELS[m] for m in model_ids], fontsize=8.5)
    ax.tick_params(length=0)
    fig.suptitle("Where each model missed, by tier and case type", fontsize=14, y=0.99)
    fig.text(
        0.5, 0.945,
        "Cell = misses / cases. Empty = all correct. A/B = real regressions · C = keyword decoy · D = new bug\n"
        "(expert D: same mistake, different code)",
        ha="center", va="top", fontsize=9,
    )
    for row in range(len(model_ids)):
        for col in range(len(columns)):
            if annotations[row][col]:
                color = "white" if values[row, col] >= 0.5 else "#17324d"
                ax.text(col, row, annotations[row][col], ha="center", va="center", fontsize=8, color=color)
    for boundary in (3.5, 7.5):
        ax.axvline(boundary, color="#6b7280", linewidth=1.1)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    colorbar.set_label("Fraction of cases missed")
    fig.subplots_adjust(left=0.23, right=0.94, top=0.85, bottom=0.10)
    fig.savefig(OUT / "zombiebench-heatmap.png", dpi=200, facecolor="white")
    plt.close(fig)


def make_miss_types(miss_types, total_attempts, total_correct):
    labels = [
        "False zombie\n(expected new; answered regression)",
        "Missed zombie\n(expected regression; answered new)",
        "Wrong old bug ID",
        "Unreadable",
    ]
    keys = list(EXPECTED_MISS_TYPES)
    values = [miss_types[key] for key in keys]
    colors = [plt.cm.Blues(v) for v in (0.88, 0.70, 0.52, 0.38)]

    fig, ax = plt.subplots(figsize=(10.8, 4.8), facecolor="white")
    ax.set_facecolor("white")
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, edgecolor="none", height=0.62)
    ax.set_yticks(y, labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.22)
    ax.set_xlabel("Number of wrong outputs")
    fig.suptitle("All 80 misses across 14 models: most were false zombies", fontsize=14, y=0.95)
    ax.text(
        0.5, 1.025,
        f"80 misses · {total_attempts:,} attempts · {total_correct:,} correct",
        transform=ax.transAxes, ha="center", va="bottom", fontsize=10,
    )
    ax.grid(axis="x", color="#dbe5ef", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(value + 0.8, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=10)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    fig.subplots_adjust(left=0.34, right=0.96, top=0.78, bottom=0.15)
    fig.savefig(OUT / "zombiebench-miss-types.png", dpi=200, facecolor="white")
    plt.close(fig)


def make_hardest_cases(case_info, missed_cases):
    hardest = sorted(missed_cases.items(), key=lambda item: (-item[1], item[0]))[:8]
    labels = []
    colors = []
    values = []
    for case_id, count in hardest:
        tier, case_type = case_info[case_id]
        suffix = " · Expert D" if tier == "expert" and case_type == "D" else ""
        labels.append(f"{case_id}{suffix}")
        colors.append(plt.cm.Blues(0.91 if suffix else 0.62))
        values.append(count)

    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor="white")
    ax.set_facecolor("white")
    y = np.arange(len(hardest))
    bars = ax.barh(y, values, color=colors, edgecolor="none", height=0.62)
    ax.set_yticks(y, labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, 9.4)
    ax.set_xticks(range(0, 9))
    ax.set_xlabel("Models that missed the case (out of 14)")
    ax.set_title("The 8 hardest cases: how many of 14 models got each wrong", fontsize=14, pad=18)
    ax.grid(axis="x", color="#dbe5ef", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(value + 0.15, bar.get_y() + bar.get_height() / 2, f"{value} of 14", va="center", fontsize=9)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    fig.subplots_adjust(left=0.23, right=0.96, top=0.88, bottom=0.15)
    fig.savefig(OUT / "zombiebench-hardest-cases.png", dpi=200, facecolor="white")
    plt.close(fig)


def main():
    (runs, cases, case_info, all_misses, miss_types, missed_cases,
     case_denominators, total_attempts, total_correct) = load_and_validate()
    OUT.mkdir(exist_ok=True)
    make_heatmap(runs, case_denominators)
    make_miss_types(miss_types, total_attempts, total_correct)
    make_hardest_cases(case_info, missed_cases)
    make_cover(miss_types, len(all_misses))
    print("Validated: 14 runs, 672 attempts, 592 correct, 80 misses")
    print("Miss categories:", dict(miss_types))
    print("Hardest cases:", sorted(missed_cases.items(), key=lambda item: (-item[1], item[0]))[:8])
    print("Wrote three 200 dpi PNG charts and a 1000x420 cover to charts/.")


def make_cover(miss_types, total_misses):
    fig = plt.figure(figsize=(5, 2.1), dpi=200, facecolor="white")
    fig.text(0.07, 0.73, "ZombieBench", fontsize=29, weight="bold", color="#08306b")
    fig.text(0.07, 0.42,
             f"{miss_types['False Zombies']} of {total_misses} misses were false zombies:",
             fontsize=13, weight="bold", color="#08519c")
    fig.text(0.07, 0.27, "a new bug called an old one", fontsize=14, color="#2171b5")
    fig.savefig(OUT / "cover.png", dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
