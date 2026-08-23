# Owner Decision Memo — TASK-WS3-LEGACY5-ELIGIBILITY-A2-COMPLEMENTARITY-STUDY-20260822

## Direct answers

- MA20: V1 retains **2471 raw anchors / 2471 episodes**. T+5 changes from **0.0172** to **0.0172** (+0.0000); T+10 changes from **0.0316** to **0.0316** (+0.0000). It is a **research candidate only**, not accepted.
- MA60: V2 retains **2096 raw anchors / 2096 episodes**. T+5 changes by **+0.0011** and T+10 by **+0.0037**. The opportunity cost is **375** candidates and **173** excluded H5 matured cases with MFE>=5%.
- MA20+MA60 versus MA60: V3 retains **2096 raw anchors / 2096 episodes**. Relative to V2, T+5 changes by **+0.0000** and T+10 by **+0.0000**; it removes **0** additional candidates. No acceptance conclusion is drawn.
- MA20 opportunity cost versus V0: **0** candidates removed; excluded H5 matured cases with MFE>=3/5/10% = **0/0/0**; adverse endpoint<=0 / MAE<=-5% cases removed = **0/0**.
- A2 and Legacy-5 are **complementary rather than identical** under the fixed +/-1-session match: same-session BOTH=560 pairs, A2_ONLY=4485, LEGACY5_ONLY=1679; these are descriptive event counts, not a production merge.
- BOTH same-session path quality: the paired combined H10 endpoint mean is **0.0508** versus A2_ONLY **0.0293** and Legacy5_ONLY **0.0151**. This is **informative but not acceptance evidence**; A2 event-level time-to-opportunity remains unavailable from the existing path artifact.
- Research disposition: **RESEARCH_CANDIDATE only**. No eligibility variant is accepted; Price>=20 was not researched in this task.

## Core variant snapshot

| Variant | Raw anchors / episodes | Instruments | T+5 | T+10 | MFE5 mean | MAE5 mean | MFE10 mean | MAE10 mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V0 Legacy-5 | 2471 / 2471 | 544 | 0.0172 | 0.0316 | 0.0879 | -0.0477 | 0.1288 | -0.0672 |
| V1 +MA20 | 2471 / 2471 | 544 | 0.0172 | 0.0316 | 0.0879 | -0.0477 | 0.1288 | -0.0672 |
| V2 +MA60 | 2096 / 2096 | 529 | 0.0184 | 0.0353 | 0.0922 | -0.0499 | 0.1367 | -0.0702 |
| V3 +MA20+MA60 | 2096 / 2096 | 529 | 0.0184 | 0.0353 | 0.0922 | -0.0499 | 0.1367 | -0.0702 |

## Governance

`WS3_ONLY=YES`; `A_SETUP_ACCEPTED=NO`; `A_STRATEGY_ACCEPTED=NO`; `LEGACY_STRATEGY_ACCEPTED=NO`; `PRODUCTION_MUTATION=NO`; `DEPLOY=NO`; `PUSH=NO`; `NEXT_TASK_CHANGED=NO`. Corporate-action state is `UNKNOWN_RAW_ONLY`; same-session barrier ordering is `SAME_SESSION_ORDER_UNKNOWN`.

The figures are gross descriptive research. They do not define entry, exit, stop, position sizing, cooldown, or production semantics. A2/Core V0, WS1/WS2/WS4, API/UI, scheduler, and NEXT_TASK are unchanged.
