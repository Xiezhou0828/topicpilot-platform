# TASK-BE-024B｜Opportunity Qualification Policy V1

**Date:** 2026-08-12
**Status:** `COMPLETE / SHADOW ONLY`
**Production write:** `NO`
**Scheduler change:** `NO`
**Calibration:** `NOT RUN` (placeholder/replay contract only)

## 1. Summary

TASK-BE-024B is implemented as an additive deterministic policy layer over the
existing BE-024/024A Opportunity shadow engine. The layer freezes PM semantic
ordering while keeping all numeric thresholds, weights, lifecycle multipliers,
support distances, lag/RS/volume rules, and maturity penalties centralized and
versioned as provisional/tunable parameters.

The implementation does not recalculate Topic Score, Topic Grade, or Topic
Lifecycle; those remain upstream Topic Engine authorities. It does not expose
an API, add persistence, change a migration, activate a scheduler, write
production data, or publish a customer recommendation.

## 2. Existing Pipeline Audit

The repository already contained:

```text
Topic Engine Grade/Lifecycle/Strength
        ↓
ThemeContext + effective membership/no-trade facts
        ↓
canonical DAILY_BAR OHLCV evidence
        ↓
Trend Continuation / Catch-up strategy evidence
        ↓
strategy-local ranking
        ↓
Opportunity decision/read/explainability shadow contract
```

BE-024B preserves this ownership and inserts qualification semantics before
ranking/presentation. The strategy engine remains provider-neutral and
in-memory. The existing canonical OHLCV evidence builder remains the only
technical fact calculator in this path.

## 3. Files Changed

### Backend

- `services/api/src/topicpilot_api/topic_engine/opportunity_qualification.py`
  - PM Qualification Policy V1, grade/exception provenance, Lifecycle ×
    Strategy status, 20MA/60MA qualification, risk precedence, state mapping,
    presentation caps, cadence metadata, and versioned parameters.
- `services/api/src/topicpilot_api/topic_engine/opportunity_strategies.py`
  - explicit Lifecycle Fit stage, formal/exception grade handling, lifecycle
    rank context, missing-20MA fail-closed behavior, policy metadata, and full
    result qualification provenance.
- `services/api/src/topicpilot_api/topic_engine/opportunity_contract.py`
  - qualification class/version fields in the provider-neutral read contract
    and per-observation calibration provenance.
- `services/api/src/topicpilot_api/topic_engine/__init__.py`
  - public exports for policy constants and Lifecycle matrix.

### Tests

- `services/api/tests/test_opportunity_qualification.py`
  - 12 deterministic policy/gate/matrix/cap/replay tests.
- `services/api/tests/test_opportunity_contract.py`
  - read/explainability qualification-class coverage.
- Existing BE-024/024A strategy, evidence, shadow, and contract tests were
  retained and rerun.

### Documentation

- `docs/product/TOPICPILOT_PRODUCT_IDEAS.md`
- `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`
- `docs/product/TOPICPILOT_PRODUCT_DECISIONS.md` (PD-015)
- `docs/product/TOPICPILOT_OPPORTUNITY_ENGINE_SPEC.md` (024B amendment)
- `docs/ROADMAP.md` (incremental handoff)
- `docs/architecture/decisions/OPPORTUNITY_QUALIFICATION_POLICY_V1.md`
- `docs/architecture/decisions/README.md`
- this report

Historical BE-024/024A reports were preserved. No `NEXT_TASK` authority file
was changed; the external authority is `AI/NEXT_TASK.md` outside this
repository.

## 4. Policy V1 Matrix

| Dimension | Frozen semantic | Implementation evidence |
|---|---|---|
| S/A | Formal Opportunity universe for A/B strategies | `formal_grades`, `THEME_CONTEXT_ELIGIBLE`, `FORMAL_OPPORTUNITY` |
| B | Exception only with warming/improving signal and explicit provenance | `EXCEPTION_CANDIDATE`, `TOPIC_GRADE_B_EXCEPTION_CANDIDATE`, provenance evidence |
| D | Hard exclude new Opportunity | `TOPIC_GRADE_D_HARD_EXCLUDE` / `TOPIC_GRADE_HARD_EXCLUDED` |
| Sprouting | Waiting confirmation / not a formal strong push | `LIFECYCLE_CONFIRMATION_REQUIRED`, `WAITING_CONFIRMATION` |
| Fermenting | Trend high fit; Catch-up medium-high fit | `LIFECYCLE_HIGH_FIT`, `LIFECYCLE_MEDIUM_HIGH_FIT` |
| Main Rise | High fit for both | `LIFECYCLE_HIGH_FIT` |
| Mature | Trend low/downgraded; Catch-up stricter gates | `LIFECYCLE_LOW_FIT`, `LIFECYCLE_STRICTER_GATES`, provisional rank multipliers |
| Declining | Hard exclude new A/B | `LIFECYCLE_HARD_EXCLUDE` |
| Close vs 20MA | `>=` passes; `<` excludes; missing defers | `CLOSE_BELOW_20MA_HARD_EXCLUDE`, `TWENTY_MA_REQUIRED_EVIDENCE_UNAVAILABLE` |
| 60MA | Structure/ranking/explainability only | `SIXTY_MA_ROLE`, `LIFECYCLE_RANK_CONTEXT`; no 60MA hard exclusion |
| Risk | Before ranking; hard risk cannot be rescued by score | result rank nulled on hard qualification/risk exclusion |
| Ranking | A/B independent; no global winner | `rank_strategy_results` rejects mixed strategy ids; engine field is null |
| State | SELECTED / WAITING_RETEST / WAITING_CONFIRMATION / DEFERRED / EXCLUDED | decision/read contract |
| Presentation | A/Trend Top 3; B/Catch-up Top 2; complete backend ranking retained | `presentation_candidates` |
| Cadence | Post-close rank; intraday status-only | `POST_CLOSE`, `STATUS_ONLY`, reranking disabled |

## 5. FROZEN Decisions

- Topic Engine owns Topic Score, Grade, Lifecycle, and Strength.
- Opportunity does not turn Lifecycle into a new Grade or recalculate upstream
  semantics.
- `S/A` are formal; `B` requires explicit exception provenance; `D` excludes.
- Declining topics cannot create new A/B Opportunities.
- Close `>= 20MA` is a hard qualification gate; close `< 20MA` is excluded.
- Missing required 20MA evidence is deferred, not assumed to pass.
- 60MA is never a standalone hard exclusion.
- Hard risk is evaluated before ranking and cannot be offset by a high rank.
- Trend and Catch-up rank independently; a global winner is unavailable.
- The five state values and their fail-closed/data-deferred semantics are stable.
- Presentation caps do not discard backend ranking/evidence.
- Formal rank refresh is post-close; intraday is status-only in V1.
- LLMs may later verbalize evidence only; they cannot decide eligibility, risk,
  rank, state, or bypass a gate.

## 6. PROVISIONAL Parameters

`OpportunityPolicy` and nested `OpportunityEvidencePolicy` carry explicit
version/status metadata. The following remain `PROVISIONAL / TUNABLE / VERSIONED`:

- Trend/Catch-up ranking weights and profile versions;
- relative-strength windows and bounds;
- Catch-up lag and inflection thresholds;
- volume activation and price/volume thresholds;
- support distance, extension, retest, and cooldown/validity values;
- Sprouting and Mature lifecycle rank multipliers;
- exact maturity stricter-gate penalties and future intraday thresholds.

The implementation centralizes these defaults and serializes them for audit; it
does not claim optimization or PM calibration.

## 6.1 OPEN / NOT PM-FROZEN Business Rules

The semantic order is frozen, but these decisions remain open and must be
separately versioned before production activation or calibration claims:

- Grade qualification thresholds beyond the S/A/B/D semantic classes;
- Lifecycle qualification mechanics and future lifecycle rules;
- whether 20MA is the only mandatory technical gate;
- any 60MA gate or bonus;
- support-distance threshold and formal price/volume pattern definitions;
- risk cooldown days;
- Topic Quality / Technical / Entry / Chip ranking weights;
- maximum stocks per topic;
- Opportunity validity/expiry period;
- intraday automatic re-ranking policy;
- Exception upgrade threshold and institution/chip confirmation threshold; and
- all Opportunity state-transition thresholds and timing.

## 7. Historical Replay / Calibration Contract

The existing replay remains as-of bounded: bars and dated relative-gap history
after the evaluation date are excluded, and future Theme snapshots are cleared
to unavailable/deferred context. The placeholder contract reserves:

- strategies: Trend Continuation and Catch-up;
- horizons: forward 1D, 3D, 5D, and 10D;
- forward return, MFE, MAE, +3%/+5%/+10% hit, support hold/fail,
  invalidation outcome;
- Lifecycle, Grade, state, ranking-profile, policy, and parameter provenance.

No outcome values, fake calibration, or production performance claim was
generated.

The placeholder observation schema and shadow PM calibration rows carry the
selection provenance as an explicit `selectionProvenance` object: lifecycle,
topic grade, opportunity state, ranking-profile version, policy version, and
parameter version. No forward outcome values are populated yet.

The contract also declares `requiredSource = CANONICAL_PRODUCTION_DAILY_OHLCV`,
`syntheticAllowed = false`, and `lookAhead = false`; this is a calibration
eligibility boundary, not a claim that production calibration has occurred.

## 8. Explainability / Read Contract

Every evaluated result retains qualification status, class, reason codes,
policy version, parameter version, and structured evidence. B exceptions expose
the warming signal and provenance. The provider-neutral read projection exposes
the same qualification class under `qualification.class`; the frontend remains
forbidden from deriving gates, rank, risk, state, or lifecycle.

## 9. Tests

Command:

```text
pymanager exec -V:PythonCore/3.12 -m pytest -q \
  tests/test_opportunity_contract.py \
  tests/test_opportunity_qualification.py \
  tests/test_opportunity_strategies.py \
  tests/test_opportunity_shadow.py \
  tests/test_opportunity_evidence.py
```

Result: **59 passed** for the focused Opportunity/evidence/shadow suite.

The broad runnable backend regression passed **331 passed, 22 skipped**. The
skips require an explicit PostgreSQL URL. Eight pre-existing collection modules
were excluded from that runnable command because this environment lacks the
optional `httpx2` TestClient dependency or the root `infra` import path; the
unfiltered collection failure is environmental and not caused by BE-024B.

Coverage includes S/A formal eligibility; B blocked/exception provenance; D
and Declining exclusion; full Lifecycle matrix and Sprouting waiting state;
20MA below/equal/missing behavior; below-60MA recovery; hard risk precedence;
state semantics; A/B caps and independent ranking; backend rank retention;
no-look-ahead replay; policy/read/explainability version fields; deterministic
serialization; and future strategy non-implementation.

Targeted Ruff was run after the implementation changes; no new focused lint
error is accepted. PostgreSQL integration/migration checks are `N/A` because
024B adds no schema or migration and the policy is shadow/in-memory only.

## 9.1 Regression Result

The broad runnable backend regression passed **331 tests**, with **22 tests
skipped**. The focused Opportunity/evidence/shadow suite passed **59 tests**.
The unfiltered backend collection remains environment-blocked by the optional
`httpx2` TestClient dependency and the repository-root `infra` import path;
those collection failures are pre-existing and are not caused by BE-024B. No
existing BE-024/024A state, replay, or future-strategy contract regressed.

## 9.2 Documentation Updated

The product specification, Product Ideas, Product Decisions, product roadmap,
architecture decision record, V2 frontend design specification, AI worklog,
Daily Progress, and this report were updated incrementally. Earlier
Recommendation, strategy-candidate, topic×technical-score, and catch-up
concepts remain historical/provisional rather than being deleted or silently
promoted.

## 10. Known Limitations and Risks

- Formal production canonical history is still required before replay or
  calibration can be meaningful.
- The policy does not activate an API, persistence, Scheduler, or customer
  surface.
- Exact lifecycle penalty/strictness values remain provisional until approved
  history-based calibration.
- Technical evidence for extreme-limit/abnormal-risk cases remains bounded by
  the existing evidence contract; unsupported context remains deferred or
  fail-closed rather than invented.
- Existing repository-wide legacy lint findings are outside this task's scope.

## 10.1 Production Data Dependencies

Any future calibration requires accepted production canonical daily-market
OHLCV with point-in-time/as-of binding, formal Topic Grade/Lifecycle snapshots,
selection timestamps, and the versioned policy/ranking configuration. The
current fixture/synthetic test bars are deterministic implementation inputs,
not calibration evidence. No production outcome evaluation has been run.

## 11. Production Boundary

```text
FAKE_CALIBRATION_PERFORMED = NO
PRODUCTION_WRITE_PERFORMED = NO
SCHEDULER_CHANGED = NO
TOPIC_SCORE_CHANGED = NO
TOPIC_GRADE_CHANGED = NO
TOPIC_LIFECYCLE_ALGORITHM_CHANGED = NO
DATABASE_SCHEMA_CHANGED = NO
IDENTITY_BOOTSTRAP_CHANGED = NO
```

The separate 2026-08-12 Production Daily Market Canary was stopped by its
first failing gate and is documented independently in
`TASK-OPS-023A-P2_CANARY_20260812_GATE_STOP_REPORT.md`.

## 12. Final Acceptance Matrix

| Acceptance item | Result | Evidence |
|---|---|---|
| Policy implemented as existing-layer extension | PASS | `opportunity_qualification.py`, strategy integration |
| S/A formal universe | PASS | policy tests |
| B exception provenance | PASS | policy/read tests |
| D hard exclusion | PASS | policy tests |
| Lifecycle × Strategy matrix | PASS | matrix test/serialized policy |
| 20MA hard gate and missing deferral | PASS | gate tests |
| 60MA not a hard gate | PASS | recovery/equality tests |
| Risk before ranking | PASS | hard-risk rank nulling test |
| A/B independent ranking | PASS | mixed-list rejection test |
| Five state semantics | PASS | contract/fixture/regression tests |
| A Top 3 / B Top 2 caps | PASS | cap test |
| Full backend ranking retained | PASS | cap/rank test |
| Post-close/status-only cadence | PASS | policy serialization/validation |
| Provisional parameters versioned | PASS | policy serialization |
| No-look-ahead replay | PASS | replay tests |
| Docs/product/roadmap/decision updated | PASS | listed files |
| Historical decisions preserved | PASS | incremental amendments/reports |
| Production write | NO | explicit boundary |
| Scheduler change | NO | explicit boundary |
| NEXT_TASK modified | NO | no authority file changed |

## 13. Suggested NEXT_TASK

`TASK-BE-024C | Opportunity Shadow API/UI Adapter and Formal-History Replay
Handoff`

This is a report-only suggestion. Before starting it, accumulate accepted
production canonical history, verify the existing daily-data gates, and obtain
separate authorization for any API/UI adapter or persistence. Do not calibrate
or activate production semantics from fixtures. The external authority file
`C:\Users\acer\Desktop\題材領航\AI\NEXT_TASK.md` was checked and not modified.

## 13.1 Recommended Next Step

Run a separately authorized, read-only historical replay and PM calibration
review against canonical production data. Review parameter sensitivity and
state transitions before considering any API, UI, persistence, scheduler, or
production activation work.

## Fixed Response Fields

```text
TASK-BE-024B_STATUS = COMPLETE
EXECUTION_MODE = SHADOW_ONLY
POLICY_IMPLEMENTED = YES
DOCS_UPDATED = YES
20MA_HARD_GATE = YES
60MA_HARD_GATE = NO
RISK_BEFORE_RANKING = YES
A_B_INDEPENDENT = YES
PRESENTATION_CAP = A_TOP_3 / B_TOP_2
PROVISIONAL_PARAMS_VERSIONED = YES
FAKE_CALIBRATION_PERFORMED = NO
PRODUCTION_WRITE_PERFORMED = NO
SCHEDULER_CHANGED = NO
TESTS = PASS
RUFF = PASS
NEXT_TASK = NOT_MODIFIED
```
