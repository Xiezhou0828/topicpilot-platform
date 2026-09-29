# Owner-seeded V0 Owner review and forward-observation package

## Review identity

| Field | Value |
|---|---|
| Task | `TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-REVIEW-AND-FORWARD-OBSERVATION-002` |
| Policy | `topic-strength-lifecycle.owner-seeded-v0` / `v0` |
| Policy hash | `5d29d968d9116b3288a288a8c9b15d68e51485ff88e4b58d82c2dfbbc27312ef` |
| Candidate base | `1a140c63c703bfeb24327ff435115e4d9162f3f2` |
| Calibration method | `OWNER_SEEDED_FROM_DESIGN_FREEZE` |
| Historical calibration | `NOT_AVAILABLE` |
| Provisional | `YES` |
| Production active | `NO` |

The exact existing 25-case replay was reviewed. No new scenario replaced the
existing set, and the replay remains synthetic rather than historical.

## Decision boundary

The review package is complete, but qualitative Owner acceptance is still
required. The recommended disposition is `OWNER_REVIEW_ACCEPTED_WITH_OBSERVATION_FLAGS`
provided the Owner accepts the explicitly listed counterintuitive transition
holds. This document does not claim that acceptance on the Owner's behalf.

`TASK_STATUS=COMPLETE_WITH_OWNER_REVIEW_PENDING`

## Scenario review summary

| Classification | Count |
|---|---:|
| `EXPECTED_AND_INTUITIVE` | 10 |
| `EXPECTED_BUT_NEEDS_OBSERVATION` | 9 |
| `TECHNICALLY_VALID_BUT_COUNTERINTUITIVE` | 6 |
| `POTENTIAL_POLICY_DEFECT` | 0 |

The complete row-level table is in `owner-scenario-review.json`.

| ID | Scenario | Absolute / relative | Lifecycle result | Classification |
|---|---|---|---|---|
| S01 | flat neutral Topic | 42.800 B / 51.800 B | BASE | EXPECTED_AND_INTUITIVE |
| S02 | mild positive Topic | 54.885 B / 65.165 A | BASE | EXPECTED_BUT_NEEDS_OBSERVATION |
| S03 | clear A Topic | 75.350 A / 83.350 S | BASE; MAIN_RISE candidate held | TECHNICALLY_VALID_BUT_COUNTERINTUITIVE |
| S04 | high-A Topic | 80.250 A / 86.950 S | BASE; MAIN_RISE candidate held | TECHNICALLY_VALID_BUT_COUNTERINTUITIVE |
| S05 | broad S Topic | 94.429 S / 97.643 S | BASE; MAIN_RISE candidate held | TECHNICALLY_VALID_BUT_COUNTERINTUITIVE |
| S06 | broad negative D Topic | 13.300 D / 24.000 D | BASE; DECLINING candidate held | TECHNICALLY_VALID_BUT_COUNTERINTUITIVE |
| S07 | low numeric score but neutral evidence | 41.000 B / 50.000 B | BASE | EXPECTED_AND_INTUITIVE |
| S08 | one CORE plus 9%, other CORE flat | 57.900 B / 65.500 A | SPROUTING | EXPECTED_BUT_NEEDS_OBSERVATION |
| S09 | four CORE plus 3% | 70.000 A / 78.000 A | BASE; FERMENTING pending | EXPECTED_BUT_NEEDS_OBSERVATION |
| S10 | RELATED 100% plus 0.1% | 43.500 B / 52.500 B | BASE | EXPECTED_AND_INTUITIVE |
| S11 | CORE strong, RELATED weak | 70.000 A / 78.000 A | BASE; no MAIN_RISE | EXPECTED_AND_INTUITIVE |
| S12 | CORE strong, RELATED broad | 79.000 A / 87.000 S | BASE; MAIN_RISE candidate held | TECHNICALLY_VALID_BUT_COUNTERINTUITIVE |
| S13 | RELATED-only surge | 51.000 B / 60.000 B | BASE | EXPECTED_AND_INTUITIVE |
| S14 | REP strong, CORE weak | 57.000 B / 65.000 A | SPROUTING | EXPECTED_BUT_NEEDS_OBSERVATION |
| S15 | REP ordinary, CORE broad strong | 70.000 A / 78.000 A | BASE; FERMENTING pending | EXPECTED_BUT_NEEDS_OBSERVATION |
| S16 | Absolute weak / Relative strong | 26.000 D / 83.500 S | BASE; DECLINING candidate held | EXPECTED_BUT_NEEDS_OBSERVATION |
| S17 | Absolute strong / Relative weak | 84.000 S / 37.000 B | BASE; MAIN_RISE candidate held | TECHNICALLY_VALID_BUT_COUNTERINTUITIVE |
| L18 | BASE to SPROUTING | 47.860 B / 58.000 B | SPROUTING | EXPECTED_AND_INTUITIVE |
| L19 | BASE to FERMENTING directly | 52.000 B / 61.500 B | FERMENTING | EXPECTED_AND_INTUITIVE |
| L20 | FERMENTING to MAIN_RISE | 75.500 A / 84.500 S | MAIN_RISE | EXPECTED_AND_INTUITIVE |
| L21 | MAIN_RISE to MATURE | 48.000 B / 58.000 B | MATURE | EXPECTED_BUT_NEEDS_OBSERVATION |
| L22 | MAIN_RISE one-day pullback | 44.500 B / 54.000 B | MAIN_RISE; MATURE pending | EXPECTED_BUT_NEEDS_OBSERVATION |
| L23 | persistent negative CORE to DECLINING | 16.500 D / 28.200 D | DECLINING | EXPECTED_AND_INTUITIVE |
| L24 | late RELATED strong plus weakening CORE | 53.500 B / 63.000 A | MATURE | EXPECTED_BUT_NEEDS_OBSERVATION |
| L25 | DECLINING to BASE reset | 42.050 B / 51.200 B | BASE | EXPECTED_AND_INTUITIVE |

## Priority cases for Owner inspection

- Strongest S: S05 (94.429 absolute; 97.643 relative), plus S17 as the
  absolute-S/relative-B disagreement case.
- Weakest A: S02 is B absolute but A relative; S09/S15 are 70.000 A with
  FERMENTING evidence; S04 is the high-A / relative-S boundary.
- Strongest B: S08 and S14 show early SPROUTING without A/S; S02 shows a
  relative A against an absolute B.
- D guard: S06 and L23 are broad D cases; S16 is D absolute but S relative.
- FERMENTING boundary: S09, S11, S15, and L19.
- MAIN_RISE boundary: S03-S05, S12, S17, and L20.
- MATURE: L21, L22, and L24, including Grade/Lifecycle disagreement.
- DECLINING and reset: L23 and L25; S06/S16 show initial BASE holds.

## Bounded implementation defect found and corrected

The frozen D guard says broad weakness plus either REP weighted raw `<= -1`
**or** CORE median `<= -2.5` is sufficient. The implementation had required
REP evidence before evaluating that OR branch, which made a CORE-only topic with
deep broad weakness incorrectly remain B. The same unnecessary REP prerequisite
existed in the DECLINING predicate.

The review branch removes only those unnecessary prerequisites and adds a
focused regression test. The policy payload and hash are unchanged; the fix
aligns code with the frozen V0 semantics. This is not a threshold retune or
policy redesign.

## Boundary and monotonicity review

- Policy hash: verified against code, JSON, and replay artifacts.
- Role caps: REP 30 / CORE 60 / RELATED 10, exact.
- Importance domains: REP 1.75/1.50/1.25 and CORE 1.00/0.75/0.50, applied only
  inside role aggregation; RELATED has no individual importance.
- Absolute and relative curves: endpoint clamping and interpolation are
  monotonic; neutral relative evidence is 50 before RELATED contribution.
- Grade guards: D precedence works; low total alone remains B; deep CORE-only
  weakness is now covered by the corrected OR branch.
- Lifecycle: SPROUTING, 2-of-3 FERMENTING/MAIN_RISE confirmation, MATURE after
  MAIN_RISE plus stalled expansion/deterioration, DECLINING persistence, and
  three-session reset were replayed.
- MATURE renewed expansion remains MATURE with a flag; no reverse lifecycle was
  invented.
- Sensitivity remains `DIAGNOSTIC_ONLY`; no threshold was optimized.

## Forward observation readiness

`forward-observation-contract.md` defines the evidence boundary and the
deterministic capture command. `forward-observation-schema.json` defines the
daily artifact. `forward-observation-manifest.json` starts at zero sessions and
keeps `OBSERVATION_START_DATE=PENDING_OWNER_ACTIVATION`.

The capture helper is date-bound, policy-hash-bound, read-only with respect to
formal authority, idempotent for the same date/topic, and fail-closed for
missing authority, price, benchmark, or lifecycle-chain inputs. No scheduler,
Production database, migration, or alternate formal output is wired.

## Required final status block

```text
TASK_ID=TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-REVIEW-AND-FORWARD-OBSERVATION-002
TASK_STATUS=COMPLETE_WITH_OWNER_REVIEW_PENDING
POLICY_ID=topic-strength-lifecycle.owner-seeded-v0
POLICY_VERSION=v0
POLICY_HASH=5d29d968d9116b3288a288a8c9b15d68e51485ff88e4b58d82c2dfbbc27312ef
IMPLEMENTATION_CANDIDATE_SHA=1a140c63c703bfeb24327ff435115e4d9162f3f2
OWNER_REVIEW_STATUS=OWNER_REVIEW_REQUIRED
SCENARIOS_REVIEWED=25
EXPECTED_AND_INTUITIVE_COUNT=10
EXPECTED_BUT_NEEDS_OBSERVATION_COUNT=9
TECHNICALLY_VALID_BUT_COUNTERINTUITIVE_COUNT=6
POTENTIAL_POLICY_DEFECT_COUNT=0
BOUNDARY_REVIEW_STATUS=PASS_WITH_OWNER_OBSERVATION_FLAGS
MONOTONICITY_REVIEW_STATUS=PASS
SENSITIVITY_AUDIT_STATUS=DIAGNOSTIC_ONLY
POLICY_DEFECT_STATUS=BOUNDED_IMPLEMENTATION_DEFECT_CORRECTED_NO_POLICY_CHANGE
POLICY_CHANGED=NO
POLICY_RECALIBRATED=NO
FORWARD_OBSERVATION_CONTRACT_STATUS=READY
OBSERVATION_SCHEMA_STATUS=READY
OBSERVATION_MANIFEST_STATUS=READY_PENDING_OWNER_ACTIVATION
OBSERVATION_CAPTURE_INTERFACE_STATUS=READY_READ_ONLY_FAIL_CLOSED_IDEMPOTENT
OBSERVATION_START_DATE=PENDING_OWNER_ACTIVATION
OBSERVATION_20D_STATUS=NOT_STARTED
OBSERVATION_40D_STATUS=NOT_STARTED
OBSERVATION_60D_STATUS=NOT_STARTED
HISTORICAL_CALIBRATION=NOT_AVAILABLE
CURRENT_ROLE_RETROFILL=FORBIDDEN
MANUAL_HISTORICAL_AUTHORITY_ASSEMBLY=FORBIDDEN
PIT_STANDARD_RELAXATION=FORBIDDEN
MIGRATION_REQUIRED=NO
MIGRATION_CREATED=NO
MIGRATION_APPLIED=NO
PRODUCTION_ACTIVE=NO
PRODUCTION_DB_MUTATED=NO
DEPLOYED=NO
MERGED=NO
COMMIT_SHA=PENDING_COMMIT
PUSH_STATUS=PENDING_PUSH
OWNER_DECISIONS_REQUIRED=ACCEPT_OR_REJECT_FORWARD_OBSERVATION_WITH_EXPLICIT_FLAGS;AUTHORIZE_START_DATE_IN_FUTURE_TASK
KNOWN_LIMITATIONS=NO_HISTORICAL_CALIBRATION;SYNTHETIC_REPLAY_ONLY;SIX_COUNTERINTUITIVE_TRANSITION_HOLDS;NO_PRODUCTION_ACTIVATION
ARTIFACTS=owner-review.md;owner-scenario-review.json;forward-observation-contract.md;forward-observation-schema.json;forward-observation-manifest.json
TASK_COMPLETE=YES
NEXT_RECOMMENDED_TASK=TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-FORWARD-OBSERVATION-ACTIVATION-003_ONLY_AFTER_OWNER_REVIEW_ACCEPTANCE
```
