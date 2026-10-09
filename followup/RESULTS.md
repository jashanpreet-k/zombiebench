# Follow-up results

Across 1 models and 17 paired reports, adding a confident wrong diagnosis reduced accuracy from 11/17 to 2/17 (52.9 percentage points).

| Level | Correct | Accuracy (Wilson 95%) | Wrong target | Target rate (Wilson 95%) |
|---|---:|---|---:|---|
| L0 | 11/17 | 64.7% [41.3, 82.7] | 5/17 | 29.4% [13.3, 53.1] |
| P | 13/17 | 76.5% [52.7, 90.4] | 3/17 | 17.6% [6.2, 41.0] |
| L1 | 10/17 | 58.8% [36.0, 78.4] | 5/17 | 29.4% [13.3, 53.1] |
| L2 | 2/17 | 11.8% [3.3, 34.3] | 13/17 | 76.5% [52.7, 90.4] |
| L3 | 4/17 | 23.5% [9.6, 47.3] | 12/17 | 70.6% [46.9, 86.7] |

Original-five L2-wrong → L0-correct: 1

```json
{
  "exp2": {
    "different": {
      "correct": 0,
      "answered": 9,
      "planned": 9,
      "errors_or_missing": 0,
      "accuracy": 0.0,
      "accuracy_all": 0.0,
      "accuracy_wilson95": [
        0,
        0.2991450484195441
      ],
      "false_zombies": 9,
      "false_zombie_rate": 1.0,
      "false_zombie_wilson95": [
        0.7008549515804559,
        1
      ]
    },
    "same": {
      "correct": 9,
      "answered": 9,
      "planned": 9,
      "errors_or_missing": 0,
      "accuracy": 1.0,
      "accuracy_all": 1.0,
      "accuracy_wilson95": [
        0.7008549515804559,
        1
      ]
    },
    "pair_both_correct": {
      "correct": 0,
      "answered": 9,
      "planned": 9,
      "wilson95": [
        0,
        0.2991450484195441
      ]
    }
  },
  "stability": {
    "comparable_valid_answers": 85,
    "planned": 85,
    "changed": 9,
    "changed_ids": [
      "m0-zf1-zb-13-L1",
      "m0-zf1-zb-14-L2",
      "m0-zf1-zb-05-L3",
      "m0-zf1-zb-22-L2",
      "m0-zf1-zb-37-L1",
      "m0-zf1-zb-44-L0",
      "m0-zf1-zb-45-L0",
      "m0-zf1-zb-45-P",
      "m0-zf1-zb-45-L1"
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
