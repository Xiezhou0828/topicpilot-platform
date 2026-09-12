# Old L5 vs Lifecycle V1 summary

This is a semantic state comparison only. No investment returns or future outcomes were evaluated.

- Old L5 preserved hash: `17faa9be1189d6fab1bdfe518a1faf9e90d9be1ec994008ed59beef8bf6ecb95`.
- Old rows / V1 rows: **16250 / 16250**.
- Changed effective state rows: **12714**; unchanged: **3536**.
- Old known-stage transitions: **642**; V1 known-stage transitions: **338**.
- One-day A→B→A flips: old **28**, V1 **0**, decreased: **YES**.
- MAIN_RISE transitions: **136**; segment-2+ rows **744**, segment-2+ transitions **82**; segment-3+ rows **385**, transitions **44**.
- MAIN_RISE→MATURE five-session stall events: **88**.
- MATURE→MAIN_RISE re-entry events: **68**.
- MATURE→DECLINING events: **4**.
- Related-only MAIN_RISE rows: **0**; leader-only MAIN_RISE rows: **0**.
- Core-driven MAIN_RISE rows without strong aggregate breadth: **176**.

## Stage distributions

| Stage/status | Old L5 | V1 |
|---|---:|---:|
| DECLINING | 2811 | 75 |
| FAIL_CLOSED | 4750 | 0 |
| FERMENTING | 1642 | 3238 |
| INSUFFICIENT_DATA | 1250 | 7750 |
| MAIN_RISE | 3057 | 1306 |
| MATURE | 1094 | 1321 |
| PENDING | 1204 | 680 |
| SPROUTING | 442 | 1880 |

The V1 rows are `RETROSPECTIVE_RESEARCH_ONLY` and use the current taxonomy projected backward. A missing segment-3 case is reported as not found rather than invented.
