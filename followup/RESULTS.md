# Follow-up results

In a controlled test across 4 models, adding a confident wrong diagnosis reduced accuracy from 61/68 to 42/68 (27.9 percentage points). Each comparison used the same report, with only the comment changed.

| Level | Correct | Accuracy (Wilson 95%) | Wrong target | Target rate (Wilson 95%) |
|---|---:|---|---:|---|
| L0 | 61/68 | 89.7% [80.2, 94.9] | 5/68 | 7.4% [3.2, 16.1] |
| P | 61/68 | 89.7% [80.2, 94.9] | 4/68 | 5.9% [2.3, 14.2] |
| L1 | 57/68 | 83.8% [73.3, 90.7] | 5/68 | 7.4% [3.2, 16.1] |
| L2 | 42/68 | 61.8% [49.9, 72.4] | 14/68 | 20.6% [12.7, 31.6] |
| L3 | 46/68 | 67.6% [55.8, 77.6] | 18/68 | 26.5% [17.4, 38.0] |

Original-five L2-wrong → L0-correct: 7

```json
{
  "exp2": {
    "different": {
      "correct": 16,
      "answered": 36,
      "planned": 36,
      "errors_or_missing": 0,
      "accuracy": 0.4444444444444444,
      "accuracy_all": 0.4444444444444444,
      "accuracy_wilson95": [
        0.2954126874008022,
        0.6041893824430271
      ],
      "false_zombies": 20,
      "false_zombie_rate": 0.5555555555555556,
      "false_zombie_wilson95": [
        0.395810617556973,
        0.7045873125991978
      ]
    },
    "same": {
      "correct": 36,
      "answered": 36,
      "planned": 36,
      "errors_or_missing": 0,
      "accuracy": 1.0,
      "accuracy_all": 1.0,
      "accuracy_wilson95": [
        0.9035813714055363,
        1
      ]
    },
    "pair_both_correct": {
      "correct": 16,
      "answered": 36,
      "planned": 36,
      "wilson95": [
        0.2954126874008022,
        0.6041893824430271
      ]
    }
  },
  "stability": {
    "comparable_valid_answers": 85,
    "planned": 340,
    "changed": 9,
    "changed_ids": [
      "m4-zf1-zb-13-L1",
      "m4-zf1-zb-14-L2",
      "m4-zf1-zb-05-L3",
      "m4-zf1-zb-22-L2",
      "m4-zf1-zb-37-L1",
      "m4-zf1-zb-44-L0",
      "m4-zf1-zb-45-L0",
      "m4-zf1-zb-45-P",
      "m4-zf1-zb-45-L1"
    ],
    "identical": 76,
    "identical_rate": 0.8941176470588236,
    "identical_wilson95": [
      0.8108648139957895,
      0.9432875928801936
    ],
    "unreadable_pair_ids": [],
    "change_rate": 0.10588235294117647
  }
}
```
