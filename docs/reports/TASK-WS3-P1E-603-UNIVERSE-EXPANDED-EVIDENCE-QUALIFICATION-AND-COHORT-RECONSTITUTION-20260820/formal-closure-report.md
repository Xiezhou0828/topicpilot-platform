# WS3 P1-E — Universe-Expanded Evidence Qualification and Cohort Reconstitution

Task: `TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820`  
Workstream: TopicPilot Parallel Plan WS3 — Core V0 walk-forward research only  
As-of: `2026-08-13`  
Research run: `FULL_RECONSTRUCTION`, two full replays, timestamp-normalized artifacts

## Closure disposition

`COMPLETE_RESEARCH_ARTIFACTS_REPRODUCIBLE`

This task produced an auditable, reproducible evidence surface and Strategy Review input. It did not create an accepted strategy, formal recommendation publication, Opportunity activation, Product contract promotion, scheduler change, deployment, production mutation, or `NEXT_TASK` change. A1, A2, A3, and Catch-up remain research candidates.

## Dataset and protocol identity

| Item | Frozen identity |
|---|---|
| Shared Data Foundation | `TASK-SHARED-DATA-FOUNDATION-603-UNIVERSE-AND-2Y-OHLCV-BOOTSTRAP-EXECUTION-20260819` |
| Accepted PIT surface | 603 instruments, 288,881 accepted OHLCV rows |
| Window | `2024-08-13..2026-08-13` |
| Shared normalized data SHA-256 | `e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4` |
| Corporate-action event dataset normalized SHA-256 | `78f684d5b014f43f3b34393be1bc644805e67f05e18b21e7ab98d075a1cd60b2` |
| Walk-forward protocol | `core-v0-walk-forward.v1` |
| Development / validation / holdout | `2026-02-02..2026-06-30` / `2026-07-01..2026-07-31` / `2026-08-01..2026-08-13` |
| Prior history | 60 accepted sessions for MA60; 20 accepted sessions strictly before T for A2 reference |
| Outcome horizons | T+1, T+3, T+5, T+10 accepted sessions after T |
| Parameter posture | Frozen parameter versions; no retuning or threshold search |
| Source canonical head at replay | `c40aa42e7cac665386009f29c94a8dafce896427` |

PIT instrument status is taken from the Shared Data Foundation instrument-level audit: 587 eligible, 16 bounded-limited, 0 unusable. The per-session eligibility surface separately records 238,589 `ELIGIBLE`, 14,120 `LIMITED`, and 36,172 `INELIGIBLE` rows; those row counts are not used as instrument-level PIT status.

## Frozen candidate definitions

### A1

Authority: `CORE_V0_A1_PRE_BREAKOUT`, version `core-v0-a1-pre-breakout.v1`. The A1 quality freeze contains seven candidates; its normalized freeze hash is `321eee383b3aa0fd5e006a43ddaa1c61229a1f7e29f3738e78d7e3abed44d1b4`.

| Candidate | Frozen threshold |
|---|---:|
| recent_20_high_proximity Q30 | `>= -0.02684279376635195` |
| recent_20_high_proximity Q40 | `>= -0.02413793103448276` |
| recent_20_high_proximity Q50 | `>= -0.02147248243559719` |
| return_5d Q60 | `<= 0.07389330024813896` |
| true_range_pct Q60 | `<= 0.05599185750636132` |
| true_range_pct Q70 | `<= 0.06408819993349192` |
| proximity Q30 AND true_range_pct Q70 | both previous frozen thresholds, both non-missing |

Feature semantics are PIT-safe: `close_T / max(high_{T-19..T}) - 1`, `close_T / close_{T-5} - 1`, and `(high_T-low_T)/close_T`. A1 outcome labels are descriptive only: a later same-instrument A2 observation yields `SUCCESSFUL_A1`; otherwise the frozen 10-session descriptive path taxonomy is retained.

### A2

Authority: `CORE_V0_A2_CONFIRMED_BREAKOUT`, version `core-v0-a2-confirmed-breakout.v1`. Formation uses the prior 20 accepted-session high, `Close(T) > reference`, and a single-session close. The frozen entry evidence slice is the observable `A2_CLOSE_GT_2_TO_3PCT` band (`0.02 < Close(T)/reference - 1 <= 0.03`). Evaluation is descriptive at T+1/T+3/T+5/T+10; no stop rule is inferred. Invalidation paths remain descriptive: reference loss, reclaim, failed reclaim, depth bands, shallow quick reclaim, deep no reclaim, and multi-session below/no reclaim.

Origin classification remains evidence-only: `a1_origin_date` present means `A1_ORIGIN_A2`; otherwise `DIRECT_ENTRY_A2`; unknown is not imputed.

## Expanded results

| Surface | Expanded result | Prior frozen comparison |
|---|---:|---:|
| A1 events | 14,557 events / 601 instruments / 420 active dates | 700 / 297 / 66; 20.7957x event count |
| A1 cohorts | 13,908 successful; 423 failed; 72 continued; 119 structure-loss; 35 unclassified | 386 / 214 / 30 / 37 / 33 |
| A2 events | 5,277 events / 599 instruments / 410 active dates | 490 / 320 / 62; 10.7694x event count |
| A2 raw observations | 6,306 | 512 prior raw observations |
| A2 GT 2–3% | 712 events / 399 instruments / 288 active dates; 13.4925% retention | frozen evidence slice |
| A2 GT 2–3% T+5 | 704 evaluable; median forward return 0.2367%; mean 2.4591% | descriptive only |
| A2 GT 2–3% T+10 | 696 evaluable; median forward return 0.4811%; mean 4.0951% | descriptive only |
| A1-origin A2 | 4,957 events / 597 instruments | prior 253 |
| Direct-entry A2 | 320 events / 230 instruments | prior 237 |
| Unclassified origin | 0 | prior 0 |

All three calendar segments (`2024_PARTIAL`, `2025`, `2026_THROUGH_CANONICAL_END`) and both markets (TPE/TWO) have evidence for A1, A2, the frozen A2 entry slice, and both origin groups. The temporal/market matrix and concentration audit are included in the task artifact directory.

## Failure criteria and checks

The reconstruction was required to fail closed on source row/instrument mismatch, non-accepted data, invalid or duplicate OHLCV, missing required lineage, quarantine/NO_DATA/lifecycle leakage, supersession errors, future-session dependency in formation, look-ahead, or horizon leakage. Results:

- Shared source reconciliation: PASS — 603 instruments and 288,881 rows observed exactly.
- Invalid OHLCV: 0; duplicate sessions: 0; incomplete accepted rows: 0.
- Quarantine leakage: 0; NO_DATA synthetic fill: 0; lifecycle leakage: 0.
- Incomplete source lineage rows: 0.
- Look-ahead leakage detected: `false`.
- Evaluation-horizon leakage detected: `false`.
- Formation future-session dependency: `false`.
- Adjustment state: `UNKNOWN_RAW_ONLY`; raw OHLCV was not treated as adjusted truth.
- Known corporate-action formation windows were excluded according to the frozen event overlay; no browser-side or ad-hoc replacement was used.

## Research readiness conclusion

The expanded evidence capacity is sufficient, with bounded limitations, for the next confirmatory research review of the frozen A1 quality candidates, A2 entry evidence slice, descriptive invalidation paths, and descriptive origin split. It is not evidence of acceptance. It does not support formal recommendation publication or production activation. Any subsequent Strategy Review must retain the frozen definitions, the PIT/lineage caveats, the unknown adjustment state, and the descriptive-only interpretation of returns and path labels.

## Reproducibility and provenance

Two identical full replays completed successfully. Normalized core artifact aggregate SHA-256:

`363af6741a6edbbb2b4a092aa1b3938e0492f5fb6169885dd05df12a7691224d`

The reproducibility manifest records `reconstruction_runs=2`, `reproducible=YES`, and the per-artifact hashes. The runner source is `services/api/src/topicpilot_api/research/ws3_p1e_expanded_evidence.py`; compilation passed in the project API runtime. No test files were changed, so test-count delta is `N/A`; validation was the full replay, source reconciliation, audit checks, `py_compile`, and `git diff --check`.

## Artifacts and modified files

- Runner: `services/api/src/topicpilot_api/research/ws3_p1e_expanded_evidence.py`
- Closure report: this file.
- Evidence artifacts: `reports/TASK-WS3-P1E-603-UNIVERSE-EXPANDED-EVIDENCE-QUALIFICATION-AND-COHORT-RECONSTITUTION-20260820/`, including the source contract manifest, PIT eligibility surface, A1/A2 panels, cohort comparisons, frozen candidate capacity, entry/invalidation/origin diagnostics, temporal-market matrix, concentration audit, look-ahead/PIT audit, performance profile, reproducibility manifest, P2E readiness, and run summary.

## Promotion and state controls

| Control | Result |
|---|---|
| Isolated worktree | `C:\Users\acer\Documents\Codex\ws3-p1e-603-20260820` |
| Research branch | `codex/task-ws3-p1e-603-20260820` |
| Task worktree commit SHA | `b581ee1` |
| Canonical owner branch before promotion | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` at `c40aa42e7cac665386009f29c94a8dafce896427` |
| Promotion mode | commit-preserving explicit-path promotion; no blanket stage/clean/reset/stash |
| Remote push / remote merge / deploy / production mutation | not performed |
| Owner dirty/untracked preservation | preserved; no owner dirty file is in the WS3 write set |
| `NEXT_TASK` | unchanged |
| Post-promotion canonical SHA | recorded in final handoff after readback |

The final handoff records the task commit SHA, canonical post-promotion SHA, canonical readback, and completed task worktree/branch cleanup. No unrelated WS1/WS2 worktree or branch is removed.
