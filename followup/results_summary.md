# Follow-up results

In a controlled test across 9 models, adding a confident wrong diagnosis reduced accuracy from 145/153 to 121/153 (15.7 percentage points). Each comparison used the same report, with only the comment changed.

| Level | Correct | Accuracy (Wilson 95%) | Wrong target | Target rate (Wilson 95%) |
|---|---:|---|---:|---|
| L0 | 145/153 | 94.8% [90.0, 97.3] | 6/153 | 3.9% [1.8, 8.3] |
| P | 143/153 | 93.5% [88.4, 96.4] | 6/153 | 3.9% [1.8, 8.3] |
| L1 | 138/153 | 90.2% [84.5, 94.0] | 6/153 | 3.9% [1.8, 8.3] |
| L2 | 121/153 | 79.1% [72.0, 84.8] | 18/153 | 11.8% [7.6, 17.8] |
| L3 | 122/153 | 79.7% [72.7, 85.3] | 27/153 | 17.6% [12.4, 24.5] |

Original-five L2-wrong → L0-correct: 12

```json
{
  "exp2": {
    "different": {
      "correct": 53,
      "answered": 81,
      "planned": 81,
      "errors_or_missing": 0,
      "accuracy": 0.654320987654321,
      "accuracy_all": 0.654320987654321,
      "accuracy_wilson95": [
        0.5458937528984923,
        0.7487735046840956
      ],
      "false_zombies": 28,
      "false_zombie_rate": 0.345679012345679,
      "false_zombie_wilson95": [
        0.25122649531590424,
        0.4541062471015077
      ]
    },
    "same": {
      "correct": 81,
      "answered": 81,
      "planned": 81,
      "errors_or_missing": 0,
      "accuracy": 1.0,
      "accuracy_all": 1.0,
      "accuracy_wilson95": [
        0.9547219145675847,
        1
      ]
    },
    "pair_both_correct": {
      "correct": 53,
      "answered": 81,
      "planned": 81,
      "wilson95": [
        0.5458937528984923,
        0.7487735046840956
      ]
    }
  },
  "stability": {
    "comparable_valid_answers": 340,
    "planned": 765,
    "changed": 22,
    "changed_ids": [
      "m0-zf1-zb-45-P",
      "m3-zf1-zb-44-L0",
      "m3-zf1-zb-45-L2",
      "m7-zf1-zb-13-L1",
      "m7-zf1-zb-14-L2",
      "m7-zf1-zb-05-L3",
      "m7-zf1-zb-22-L2",
      "m7-zf1-zb-37-L1",
      "m7-zf1-zb-44-L0",
      "m7-zf1-zb-45-L0",
      "m7-zf1-zb-45-P",
      "m7-zf1-zb-45-L1",
      "m9-zf1-zb-22-L1",
      "m9-zf1-zb-07-L3",
      "m9-zf1-zb-27-P",
      "m9-zf1-zb-39-L1",
      "m9-zf1-zb-41-L3",
      "m9-zf1-zb-44-P",
      "m9-zf1-zb-44-L1",
      "m9-zf1-zb-45-P",
      "m9-zf1-zb-45-L1",
      "m9-zf1-zb-45-L2"
    ],
    "identical": 318,
    "identical_rate": 0.9352941176470588,
    "identical_wilson95": [
      0.9039775761792218,
      0.9568842902612577
    ],
    "unreadable_pair_ids": [],
    "change_rate": 0.06470588235294118
  }
}
```

{
  "complete_models": [
    "anthropic/claude-haiku-4-5@20251001",
    "anthropic/claude-opus-5-5@default",
    "google/gemini-2.5-flash",
    "google/gemini-3.1-flash-lite-preview",
    "google/gemma-4-31b",
    "openai/gpt-5.4-mini-2026-03-17",
    "openai/gpt-5.4-nano-2026-03-17",
    "openai/gpt-6.1-sol",
    "openai/gpt-oss-20b"
  ],
  "partial_models": [
    "qwen/qwen3-235b-a22b-instruct-2507"
  ],
  "stability": {
    "comparable_valid_answers": 340,
    "planned": 765,
    "changed": 22,
    "changed_ids": [
      "m0-zf1-zb-45-P",
      "m3-zf1-zb-44-L0",
      "m3-zf1-zb-45-L2",
      "m7-zf1-zb-13-L1",
      "m7-zf1-zb-14-L2",
      "m7-zf1-zb-05-L3",
      "m7-zf1-zb-22-L2",
      "m7-zf1-zb-37-L1",
      "m7-zf1-zb-44-L0",
      "m7-zf1-zb-45-L0",
      "m7-zf1-zb-45-P",
      "m7-zf1-zb-45-L1",
      "m9-zf1-zb-22-L1",
      "m9-zf1-zb-07-L3",
      "m9-zf1-zb-27-P",
      "m9-zf1-zb-39-L1",
      "m9-zf1-zb-41-L3",
      "m9-zf1-zb-44-P",
      "m9-zf1-zb-44-L1",
      "m9-zf1-zb-45-P",
      "m9-zf1-zb-45-L1",
      "m9-zf1-zb-45-L2"
    ],
    "identical": 318,
    "identical_rate": 0.9352941176470588,
    "identical_wilson95": [
      0.9039775761792218,
      0.9568842902612577
    ],
    "unreadable_pair_ids": [],
    "change_rate": 0.06470588235294118
  }
}
