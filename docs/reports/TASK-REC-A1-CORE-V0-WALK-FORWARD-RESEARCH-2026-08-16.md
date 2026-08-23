# TASK-REC-A1-CORE-V0-WALK-FORWARD-RESEARCH-2026-08-16

## Decision

Core V0 walk-forward was **not executed**. The workstream failed closed at
research preflight because the frozen REC-A1 inputs are not byte-reproducible
from the clean canonical SHA, and the canonical OHLCV/PIT candidate panel and
complete forward-outcome inputs are not available in the isolated reproducible
environment. No browser-side, synthetic, fixture, or ad-hoc replacement was
used.

This is a research-only result and a Strategy Review input boundary. It is not
an accepted/rejected strategy decision, a Recommendation publication, or an
Opportunity production activation.

## Frozen identity

| Field | Value |
| --- | --- |
| Source repository | `C:/Users/acer/Desktop/題材領航/topicpilot-platform` |
| Source SHA | `c40a1d4e0337d9c56cf805cbd708eba216b41ab0` |
| Protocol | `core-v0-walk-forward.v1` |
| Parameter version | `topic-opportunity-policy.provisional.1` |
| Parameter state | `PROVISIONAL_TUNABLE_VERSIONED`; no search/tuning/optimization |
| REC-A1 dataset | `REC-A1-CA-EVENTS-V0` |
| Dataset content hash | `4d9b4912bd1c4613510e60c5cf4b5a629c367e1c94dd733d3b1dc3f935e0eb5d` |
| Frozen owner-artifact SHA-256 | `1091f97268ac01342a1803bc511780b9948c06c50176e367588b829af0d530e0` |
| Clean canonical-HEAD artifact SHA-256 | `78f684d5b014f43f3b34393be1bc644805e67f05e18b21e7ab98d075a1cd60b2` |
| Research window | `2026-02-02` through `2026-08-13` |
| Dataset shape | `372` event rows; `507` canonical identities; `353` event identities; `154` reviewed UNKNOWN identities; `0` unreviewed UNKNOWN identities |
| Dataset use | Research-only outcome-integrity support; trading-decision use forbidden |

The complete machine-readable identity and preflight record is in
[`core-v0-protocol-and-preflight.json`](../../reports/TASK-REC-A1-CORE-V0-WALK-FORWARD-RESEARCH-20260816/core-v0-protocol-and-preflight.json).

## Protocol locked for a future executable run

The protocol is chronological and predeclared:

| Split | Window | Role |
| --- | --- | --- |
| Development | `2026-02-02..2026-06-30` | Research window; no parameter optimization |
| Validation | `2026-07-01..2026-07-31` | Chronological validation |
| Holdout | `2026-08-01..2026-08-13` | Final holdout, subject to subsequent outcomes |

Each signal requires at least 60 prior canonical trading sessions of feature
history. Forward outcomes are defined at T+1, T+3, T+5, and T+10 subsequent
canonical trading sessions. The run must use only inputs effective/observable
on or before the evaluation date, preserve source-to-canonical lineage, and
exclude or fail closed on outcome-integrity anomalies according to the frozen
REC-A1 policy. No parameter search, threshold tuning, or strategy optimization
is permitted.

Candidate definitions were recorded without inventing missing semantics:

- A1 Pre-Breakout and A2 Confirmed Breakout have no frozen canonical runtime
  definition, so they are blocked.
- A3 Strong Pullback/Retest points to the explicit future
  `PULLBACK_ACCEPTANCE` slot, which is not implemented.
- Catch-up/rotation maps only to the provisional shadow `CATCH_UP` runtime; it
  still requires a valid PIT topic context, canonical OHLCV, and outcomes.
- The available `TREND_CONTINUATION` and `CATCH_UP` engines remain
  `SHADOW_ONLY`, not formal Recommendation policy.

The planned metrics are signal/eligibility counts, coverage per horizon,
forward close return, benchmark excess return, hit rate, MFE, MAE,
event-excluded outcome count, no-look-ahead assertion, and explainability
lineage coverage. A result is invalid if any PIT input is missing, a candidate
definition is ambiguous, an input is effective after `as_of`, a forward horizon
is incomplete, lineage is missing, a duplicate/tampered input is found, or a
provisional parameter changes during the run.

## Preflight evidence

| Gate | Result | Evidence |
| --- | --- | --- |
| REC-A1 freeze identity | `FAIL` | The frozen owner artifact and metadata hashes differ from clean canonical HEAD; the linked review ledger is absent from clean HEAD, so the freeze cannot be reproduced from the canonical SHA. |
| Canonical OHLCV research panel | `FAIL` | No canonical OHLCV panel/export exists in the repository; only the PostgreSQL authority/read path is present. |
| Read-only database availability | `FAIL` | No `DATABASE_URL` or `TEST_DATABASE_URL`; the default local PostgreSQL endpoint timed out. |
| PIT Topic context | `FAIL` | Current canonical state has PIT membership/daily-state foundation, not formal Score/Grade/Lifecycle or historical Topic/System State inputs. |
| Candidate definition completeness | `FAIL` | A1/A2/A3 lack frozen runtime semantics; Pullback Acceptance is future/not implemented. |
| Forward outcome coverage | `FAIL` | No candidate/outcome panel is available; the frozen window cannot prove complete T+10 subsequent-session outcomes. |
| Look-ahead assertion | `NOT_RUN` | Replay was not started after prerequisite failure; no look-ahead claim is made. |
| Reproducibility | `BLOCKED` | Protocol/upstream hashes are fixed, but executable data/dependency replay cannot run without the missing canonical panel/database. |

The isolated worktree was clean before the two artifacts were added and
`git diff --check` plus JSON parsing/hash cross-checks passed. The bundled
Python 3.12 runtime does not include pytest, and ruff is unavailable; no
application/test source changed, so `TEST_COUNT_DELTA` is
`NOT_APPLICABLE_DOCUMENTATION_ONLY` rather than an asserted regression result.

## Results and conclusion

No walk-forward signal, eligible candidate, outcome, or performance metric was
produced. The correct research conclusion is:

> **No conclusion about edge, predictive performance, or candidate quality can
> be drawn. Core V0 remains unexecuted and all A1/A2/A3/Catch-up candidates
> remain research candidates.**

The next executable attempt requires a committed, source-linked PIT research
panel containing canonical OHLCV, effective-dated Topic/Stock context,
candidate definitions, evaluation dates, and complete T+1/T+3/T+5/T+10
outcomes, or a reachable approved canonical database snapshot. That is a data
readiness prerequisite, not permission to fill gaps with synthetic or browser
derived values.

## Validation and delivery boundary

| Field | Value |
| --- | --- |
| Source files modified | None |
| Research files created | This report and the linked protocol/preflight JSON |
| API/schema/migration/runtime changes | `NO` |
| Formal Recommendation publication | `NO` |
| Opportunity production activation | `NO` |
| Production mutation / scheduler / deploy | `NO / NO / NO` |
| Push remote | `NO` |
| `NEXT_TASK` | `NOT_MODIFIED` |
| Canonical status before promotion | `READY_FOR_CANONICAL_RECONCILIATION` |
| Release status | `NOT_A_RELEASE_CANDIDATE` |
| Production verification | `NOT_RUN` |

The owner checkout's pre-existing dirty/untracked state was not touched. WS1,
WS2, Topic, Stock, Today, Recommendation, Opportunity, and production write
sets were not modified.
